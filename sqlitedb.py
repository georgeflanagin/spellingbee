# -*- coding: utf-8 -*-
import typing
from   typing import *

"""
This is a base class for manipulating all sqlite databases.

See README for examples of how to use it for your own database.
"""

import os
import sys
min_py=(3, 10)
if sys.version_info < min_py:
    print(f"This program requires Python {min_py[0]}.{min_py[1]}, or higher.")
    sys.exit(os.EX_SOFTWARE)


# Credits
__author__ =        'George Flanagin'
__copyright__ =     'Copyright 2017, 2025 George Flanagin'
__credits__ =       'None. This idea has been around forever.'
__version__ =       '2.01'
__maintainer__ =    'George Flanagin'
__email__ =         'me+git@georgeflanagin.com'
__status__ =        'continual development.'
__license__ =       'MIT'

import re
import sqlite3
import tempfile
import time

try:
    import pandas
    we_have_pandas = True
except Exception as e:
    we_have_pandas = False

try:
    from gkfdecorators import trap
except Exception:
    import functools

    def trap(func):
        @functools.wraps(func)
        def wrapper(*a, **k):
            return func(*a, **k)
        return wrapper


###
# Global constants to make the code
# *slightly* more readable.
###
GB = 1 << 30
MB = 1 << 20
KB = 1 << 10

SELECT_OPS = {"select", "pragma", "explain", "values"}
NOT_SELECT_OPS = {"insert", "update", "delete", "replace",
                "create", "drop", "alter", "attach",
                "detach", "vacuum"}

class SQLiteDB:
    """
    Open a SQLite database with optional performance tuning.

    Parameters
    ----------
    name : str
        Path to the SQLite database file.  Use ":memory:" to create a
        temporary in-memory database.

    workload : {"read_heavy", "balanced", "write_heavy"}, optional
        A high-level description of how the database will be used.
        This is an intuitive "tuning slider"—you do not need to know
        any SQLite pragmas.

        - "read_heavy"
            Optimized for workloads where most operations are SELECTs.
            Uses larger caches, more memory-mapped I/O, and fewer fsyncs.
            Good for analysis, reporting, and scientific queries.

        - "balanced"   (default)
            A safe middle ground suitable for mixed read/write workloads.
            Uses moderate caching and normal journaling.

        - "write_heavy"
            Optimized for frequent INSERT/UPDATE operations.
            Uses conservative caching and FULL synchronous mode to keep
            durability high.  Appropriate for ingestion pipelines.

        The workload determines:
            * cache_size
            * mmap_size
            * synchronous level
            * temp_store location
        without exposing the user to low-level SQLite settings.

    memory_budget_mb : int or None, optional
        Maximum amount of memory (in megabytes) SQLite is allowed to use
        for internal caches and memory-mapped pages.

        If omitted (None), a reasonable budget is chosen automatically
        based on:
            * the size of the database file
            * available system RAM
            * the selected workload

        Automatic selection rules:
            - At least 64 MB
            - At most 25% of system RAM
            - Never more than 1 GB unless explicitly requested
            - Scales with database size (larger DB → larger cache)

        This option provides a simple way to tell SQLite:
            “you may use up to this much memory for performance, but no more.”

    Notes
    -----
    * Tuning is applied once, when the connection is opened.
      Retuning an active connection is intentionally avoided to keep
      behavior predictable in multi-process environments.

    * These tuning options are safe for multi-reader, single-writer
      scenarios typical in research computing.

    * WAL mode is enabled by default to improve concurrency.

    * If the database is opened with to_RAM=True, tuning parameters
      apply to the in-memory copy as well.

    """

    __faux_slots__ = ( 'stmt', 'OK', 'db', 'cursor',
        'timeout', 'isolation_level', 'name', 'use_pandas', 'to_RAM' )
    __values__ = ( '', False, None, None,
        15, 'DEFERRED', '', True, False )
    __defaults__ = dict(zip(
        __faux_slots__, __values__
        ))

    def __init__(
        self,
        name: str,
        *,
        workload: str = "balanced",
        memory_budget_mb: int | None = None,
        **kwargs
        ):
        """
        Does what it says. Opens the database if present.
        """
        # Set the defaults.
        for k, v in SQLiteDB.__defaults__.items():
            setattr(self, k, v)

        # Make sure it is there.
        self.name = str(os.path.realpath(name))
        if not self.name:
            sys.stderr.write(f"No database named {self.name} found.")
            return

        # Override the defaults if needed.
        for k, v in kwargs.items():
            if k in SQLiteDB.__slots__:
                setattr(self, k, v)

        error_on_init = True
        try:
            self.db = sqlite3.connect(self.name,
                timeout=self.timeout, isolation_level=self.isolation_level)

            if self.to_RAM:
                memDB = sqlite3.connect(':memory:')
                self.db.backup(memDB, pages=0, progress=None)
                self.db.close()
                self.db = memDB

            self.cursor = self.db.cursor()
            self.cursor.execute("PRAGMA journal_mode = WAL;")
            self.cursor.execute("PRAGMA busy_timeout = 5000")
            self._tune_me(workload, memory_budget_mb)

            self.keys_on()
            error_on_init = False

        except sqlite3.OperationalError as e:
            sys.stderr.write(str(e))

        finally:
            self.OK = not error_on_init


    def __str__(self) -> str:
        """ For simplicity """

        return self.name


    def __bool__(self) -> bool:
        """
        We consider everything "OK" if the object is attached to an open
        database, and the last operation went well.
        """
        return self.db is not None


    def __call__(self) -> sqlite3.Connection:
        """
        This is a bit of syntax sugar to get the cursor object
        out from inside the object. The purpose is to use it
        with the pandas library.
        """

        if not self.db: raise Exception('Not connected!')
        return self.db


    def _tune_me(self, workload: str, memory_budget_mb: int | None) -> None:
        """
        Set cache_size, mmap_size, synchronous, and temp_store based on:
          - workload: "read_heavy", "balanced", or "write_heavy"
          - memory_budget_mb: desired MB for SQLite caches (None = auto)

        This runs once at open time; we don't retune while the DB is in use.
        """
        global GB, MB, KB

        ##
        # Estimate DB size and system RAM
        ##

        db_size_bytes = 0
        try:
            if isinstance(self.name, str) and os.path.exists(self.name):
                db_size_bytes = int(os.path.getsize(self.name))
        except Exception:
            pass

        ###
        # total RAM in bytes (Linux-only but fine for your world)
        ###
        try:
            pages = os.sysconf("SC_PHYS_PAGES")
            page_size = os.sysconf("SC_PAGE_SIZE")
            total_ram_bytes = pages * page_size
        except (ValueError, OSError, AttributeError):
            total_ram_bytes = 8 * GB  # fall back to "8GB machine" guess

        ###
        # Choose a memory budget if user didn't specify one ---
        ###

        if memory_budget_mb is None:
            # Start with 12.5% of DB size, but never less than 64MB
            # and never more than 25% of system RAM or 1GB.
            if db_size_bytes > 0:
                target = max(db_size_bytes >> 3, 64*MB)
            else:
                target = 128 * MB  # small DB, just assume 128MB

            cap = min(total_ram_bytes >> 2, 1*GB)  # <= 25% RAM, <= 1GB
            memory_budget_bytes = min(target, cap)
        else:
            memory_budget_bytes = memory_budget_mb * MB

        # Convert to MB for readability and KB for cache_size pragma.
        budget_mb = max(int(memory_budget_bytes // MB), 16)
        budget_kb = budget_mb << 10

        # --- 3. Map the workload slider to tuning policies ---

        workload = (workload or "balanced").lower()
        if workload not in ("read_heavy", "balanced", "write_heavy"):
            workload = "balanced"

        # Base values; we'll tweak them per workload.
        cache_kb = budget_kb          # amount of memory for page cache
        mmap_bytes = memory_budget_bytes
        synchronous = "NORMAL"
        temp_store = "MEMORY"

        if workload == "read_heavy":
            # More aggressive caching & mmap; still safe.
            cache_kb = int(budget_kb * 1.5)
            mmap_bytes = int(memory_budget_bytes * 2)
            synchronous = "NORMAL"    # still durable, but fewer fsyncs
            temp_store = "MEMORY"

        elif workload == "write_heavy":
            # Favor durability; keep cache reasonable, mmap modest.
            cache_kb = int(budget_kb * 0.75)
            mmap_bytes = int(memory_budget_bytes * 0.5)
            synchronous = "FULL"      # safer for lots of writes
            temp_store = "MEMORY"     # temp indices in RAM

        # Clamp mmap to something sane (SQLite default max is often 2GB+)
        mmap_bytes = max(min(mmap_bytes, 4*GB), 0)  # 0..4GB

        # --- 4. Apply the pragmas ---

        # cache_size: negative value means "KB", not pages.
        try:
            self.cache_kb = cache_kb
            self.cursor.execute(f"PRAGMA cache_size = {-cache_kb}")
        except Exception:
            pass

        try:
            self.mmap_bytes = mmap_bytes
            self.cursor.execute(f"PRAGMA mmap_size = {mmap_bytes}")
        except Exception:
            pass

        try:
            self.synchronous = synchronous
            self.cursor.execute(f"PRAGMA synchronous = {synchronous}")
        except Exception:
            pass

        try:
            self.temp_store = temp_store
            self.cursor.execute(f"PRAGMA temp_store = {1 if temp_store == 'MEMORY' else 0}")
        except Exception:
            pass


    def query_status(self) -> dict:
        """
        It ain't a secret. This function can be used to inspect the
        database tuning parameters.
        """

        result = {}
        for k in "name timeout use_pandas cache_kb mmap_bytes synchronous temp_store".split():
            result[k] = getattr(self, k)
        return result



    @property
    def num_connections(self) -> int:
        """
        Determine the number of open connections to this database.

        NOTE: this function will work if the self.name object is valid
            even if this process does not have the database currently
            open.

        returns:
            -1 : if the name is invalid.
             0 : if the database is not open at all (i.e., no connections).
             n : the number of open connections.
        """
        if not self.name or not os.path.existss(self.name):
            return -1

        lines=[]

        try:
            out = subprocess.run(['lsof', '-t', self.name],
                shell=False, text=True, timeout=3,
                stdout=subprocess.PIPE)
            lines = [ln for ln in out.splitlines() if ln.strip()]
        except:
            pass

        return max(len(lines), 1)


    def __invert__(self) -> int:
        """
        Syntax sugar to allow a reference to the number of
        connections as ~db, where db is an object of type
        SQLiteDB.
        """
        return self.num_connections


    def keys_off(self) -> None:
        self.cursor.execute('pragma foreign_keys = 0')
        self.cursor.execute('pragma synchronous = OFF')


    def keys_on(self) -> None:
        self.cursor.execute('pragma foreign_keys = 1')
        self.cursor.execute('pragma synchronous = NORMAL')

    @trap
    def close(self) -> bool:
        """
        Close the database.

        If to_RAM is True, copy the in-memory database back to disk using
        an atomic replace via a temporary file.
        """
        if not self.db:
            self.OK = False
            return False

        # Commit any pending transactions.
        self.db.commit()

        if not self.to_RAM:
            self.db.close()
            self.db = None
            self.OK = False
            return True

        # to_RAM=True: write back to disk safely.
        db_dir, _ = os.path.split(self.name)
        temp_db_name = os.path.join(db_dir, next(tempfile._get_candidate_names()))

        try:
            temp_db = sqlite3.connect(temp_db_name)
            self.db.backup(temp_db, pages=0, progress=None)
            temp_db.close()

            # Replace original atomically.
            if os.path.exists(self.name):
                os.unlink(self.name)
            os.link(temp_db_name, self.name)

        except Exception as e:
            print(f"Exception raised saving in-memory database.\n{e=}")
            raise
        finally:
            self.db.close()
            self.db = None
            self.OK = False
            try:
                os.unlink(temp_db_name)
            except FileNotFoundError:
                pass

        return True

    @trap
    def commit(self) -> bool:
        """
        Expose this function so that it can be called without having
        to put the dot-notation in the calling code.
        """
        if not self.db:
            raise RuntimeError('not connected.')
        self.db.commit()
        return True


    @staticmethod
    def _is_select_like(sql: str) -> bool:
        """
        Does this SQL statement (probably) return rows?

        We treat as SELECT-like:
            - SELECT ...
            - PRAGMA ...
            - EXPLAIN ...
            - VALUES (...)
            - WITH ... SELECT ...

        We treat as non-SELECT:
            - INSERT / UPDATE / DELETE / REPLACE ...
            - CREATE / DROP / ALTER ...
            - WITH ... INSERT/UPDATE/DELETE/REPLACE ...
            - WITH ... something unidentified.
        """
        global SELECT_OPS, NOT_SELECT_OPS

        # Grab first keyword (letters only)
        s = sql.strip().lower()
        if not ( m := re.match(r"([a-z]+)", s):
            return False

        first = m.group(1)

        # Easy cases ...
        if first in SELECT_OPS:
            return True

        if first in NOT_SELECT_OPS:
            return False

        # Handle our good buddy WITH ...
        if first == "with":
            lowered = s

            pos_select = lowered.find("select")
            candidates = [
                lowered.find("insert"),
                lowered.find("update"),
                lowered.find("delete"),
                lowered.find("replace"),
                ]
            pos_write = min([p for p in candidates if p != -1], default=-1)

            ###
            # It is a WITH ... SELECT statement if we see the SELECT before
            # one of the others. Note that if the statement is syntactically
            # legal, it almost always has one of these operations following WITH.
            ###
            if pos_select != -1 and (pos_write == -1 or pos_select < pos_write):
                return True
            else:
                return False

        # If it is something odd, then it wasn't SELECT.
        return False


    @trap
    def executemany_SQL(self, SQL: str, datasource: Iterable) -> int:
        """
        Execute the same SQL statement against many rows of input
        within a single transaction.

        The datasource can be:
            - an iterable of tuples/lists, or
            - a pandas DataFrame (converted to tuples via itertuples).

        Returns:
            int: number of rows successfully processed.
        """
        global we_have_pandas

        if we_have_pandas and isinstance(datasource, pandas.DataFrame):
            datasource = datasource.itertuples(index=False, name=None)

        if not self.db:
            raise RuntimeError("Not connected!")

        # We might need to know len() if available.
        try:
            expected = len(datasource)  # works for sequences
        except TypeError:
            expected = None

        self.cursor.execute('BEGIN TRANSACTION;')
        try:
            cursor = self.cursor.executemany(SQL, datasource)
            self.cursor.execute('COMMIT;')
        except Exception:
            self.cursor.execute('ROLLBACK;')
            raise

        # Prefer explicit length if we had it; otherwise fall back to rowcount.
        if expected is not None:
            return expected
        return cursor.rowcount

    @trap   # optional: you can re-enable this if you like
    def execute_SQL(self, SQL: str, *args, **kwargs) -> object:
        """
        Execute a single SQL statement.

        Behavior:
            - For SELECT statements:
                - If use_pandas and pandas is available, return a DataFrame.
                - Otherwise, return a list of rows (cursor.fetchall()).
            - For non-SELECT statements:
                - Execute the statement.
                - If transaction keyword is not provided, auto-commit.
                - Return cursor.rowcount.

        Args:
            SQL: the SQL statement.
            *args: positional parameters for the statement.
            transaction: if present (any truthy value), do NOT auto-commit.

        Returns:
            object: list of rows, DataFrame, or rowcount depending on SQL.
        """
        global we_have_pandas

        if not self.db:
            raise RuntimeError("Not connected!")

        docommit = kwargs.get('transaction') is None
        is_select = self._is_select_like(SQL)
        has_args = bool(args)

        # Pandas path for SELECTs.
        if we_have_pandas and self.use_pandas and is_select:
            params = args[0] if has_args and len(args) == 1 else (args if has_args else None)
            return pandas.read_sql_query(SQL, self.db, params=params)

        # Plain sqlite path.
        if has_args:
            cursor = self.cursor.execute(SQL, args)
        else:
            cursor = self.cursor.execute(SQL)

        if is_select:
            return cursor.fetchall()

        if docommit:
            self.commit()

        return cursor.rowcount

    @trap
    def row_one(self, SQL:str, parameters:Union[tuple, None]=None) -> dict:
        """
        Return only the first row of the results. When returned,
        it will not be a list with one row, but just the row
        itself. If the column is provided, then only that column
        is returned as an atomic datum.
        """
        results = self.execute_SQL(SQL, *parameters) if parameters else self.execute_SQL(SQL)
        return None if not results else results[0]
