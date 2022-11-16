# -*- coding: utf-8 -*-

"""
Simple program that plays nytimes.com/spellingbee using a 
dictionary of the user's choice and the rules of the game
given on the website.
"""

import typing
from   typing import *

min_py = (3, 8)

###
# Standard imports, starting with os and sys
###
import os
import sys
if sys.version_info < min_py:
    print(f"This program requires Python {min_py[0]}.{min_py[1]}, or higher.")
    sys.exit(os.EX_SOFTWARE)

###
# Other standard distro imports
###
import argparse
import contextlib
import multiprocessing
import platform
import re
import time

###
# From hpclib
###
import sqlitedb

###
# Credits
###
__author__ = 'George Flanagin'
__copyright__ = 'Copyright 2022'
__credits__ = None
__version__ = 0.95
__maintainer__ = 'George Flanagin'
__email__ = ['me@georgeflanagin.com', 'gflanagin@richmond.edu']
__status__ = 'in progress'
__license__ = 'MIT'

this_os = platform.system()
if this_os == 'Linux':
    default_word_list = '/usr/share/dict/linux.words'
elif this_os == 'Darwin':
    default_word_list = '/usr/share/dict/words'
else:
    default_word_list = './words'

# We will use a global verbose to control how chatty the
# program is.
db = None
mylock = None
mypid = os.getpid()
SQL = "INSERT INTO answers (middle_letter, puzzle, matches, pid) VALUES (?, ?, ?, ?)"
start_time = time.time()
verbose = False

def analyze_pangrams(pangrams:tuple, words:tuple) -> int:
    """
    Take some pangrams and see how many words we can find 
    when using each one in the SpellingBee program.

    For each pangram, we successively treat each letter
    as the middle one as the inner for-loop runs. 
    """
    global verbose
    global db

    try:
        print(f"Child process {os.getpid()} is analyzing {len(pangrams)} pangrams.")
        for pangram in pangrams:
            pangram = "".join(set(pangram))
            db and db.execute_SQL("BEGIN EXCLUSIVE TRANSACTION")
            for i, required_letter in enumerate(pangram):
                expression = build_regex(required_letter, pangram[:i] + pangram[i+1:])
                matches = sorted(tuple(_ for _ in words if expression.fullmatch(_)))
                db and write_results(required_letter, "".join(sorted(pangram)), matches)
            db and robust_commit()

    except KeyboardInterrupt as e:
        print("You pressed control-C")        

    finally:
        db.close()
        os._exit(os.EX_OK)


def beehive(myargs:argparse.Namespace, words:tuple) -> int:
    """
    Try every pangram in the dictionary against the entire list of words.
    """
    global verbose
    global mypid
    global mylock

    num_cpus = myargs.cpus if myargs.batch else 1
    print(f"Using {num_cpus} processes.")

    pangrams = tuple(_ for _ in words if len(set(_)) == 7)
    verbose and print(f"The dictionary contains {len(pangrams)} pangrams")    

    mypids = set()
    for block in splitter(pangrams, num_cpus):
        pid = os.fork()
        if pid: 
            mypids.add(pid)
        else:
            # These objects are distinct in the child processes. Each
            # child has its own lock instance that references the 
            # the singleton lock.
            mypid = os.getpid()
            mylock = multiprocessing.RLock()
            analyze_pangrams(block, words)

    while mypids:
        child_pid, status, _ = os.wait3(0)
        exit_code, signal_number = divmod(status, 256)
        mypids.remove(child_pid)
        print(f"{child_pid=} has completed with {exit_code=} by {signal_number=}")

    return os.EX_OK


def build_dict(filename:str) -> int:
    """
    Take any file of words that is presumably a 'dictionary'
    of some whitespace delimited collection of words. Apply 
    the NYTimes rules of the game, and write the file with 
    the suffix .bee in $PWD.
    """

    # We are not going for efficiency here. This is only executed
    # once, and after this step the new file is the one used, and
    # it assumed to be correct.
    words = tuple(word for word in read_whitespace_file(filename) 
        if len(word) > 3 and 
        word.islower() and 
        word.isalpha() and
        's' not in word)

    print(f"{len(words)=}")

    with open(f"{os.path.basename(filename)}.bee", 'w') as f:
        with contextlib.redirect_stdout(f):
            for word in words:
                print(word)

    return len(words)


def build_regex(required_letter:str, other_letters:str) -> re.Pattern:
    """
    Build the regex that represents the puzzle: 
    """
    all_letters = required_letter + other_letters
    return re.compile(f"[{other_letters}]*{required_letter}[{all_letters}]*")


def read_whitespace_file(filename:str) -> tuple:
    """
    This is a generator that returns the whitespace delimited tokens 
    in a text file, one token at a time.
    """
    if not filename: return tuple()

    if not os.path.isfile(filename):
        sys.stderr.write(f"{filename} cannot be found.")
        return os.EX_NOINPUT

    f = open(filename)
    yield from (" ".join(f.read().split('\n'))).split()
    

def robust_commit() -> None:
    global db
    global mylock
    try:
        mylock.acquire()
        db.commit()
    except Exception as e:
        print(f"Exception in commit {e=}.")
        os._exit(os.EX_IOERR)
    finally:
        mylock.release()

        

def splitter(group:Iterable, num_chunks:int) -> Iterable:
    """
    Generator to divide a collection into num_chunks pieces.
    It works with str, tuple, list, and dict, and the return
    value is of the same type as the first argument.

    group      -- str, tuple, list, or dict.
    num_chunks -- how many pieces you want to have.

    Use:
        for chunk in splitter(group, num_chunks):
            ... do something with chunk ...

    Full test program:

        s = "nowisthewinterofourdiscontent"
        l = list(s)
        t = tuple(s)
        d = dict(zip(s, range(len(s))))

        print([ group for bag in (s, l, t, d) for group in splitter(bag, 5)])
    """

    quotient, remainder = divmod(len(group), num_chunks)
    is_dict = isinstance(group, dict)
    if is_dict: 
        group = tuple(kvpair for kvpair in group.items())

    for i in range(num_chunks):
        lower = i*quotient + min(i, remainder)
        upper = (i+1)*quotient + min(i+1, remainder)

        if is_dict:
            yield {k:v for (k,v) in group[lower:upper]}
        else:
            yield group[lower:upper]


def write_results(letter:str, pangram:str, results:tuple) -> bool:
    """
    Record a result in the database.
    """
    global db
    global SQL
    global mypid
    global mylock
    results = " ".join(results)
    try:
        mylock.acquire()
        db.execute_SQL(SQL, letter, pangram, results, mypid, transaction=True)

    except Exception as e:
        print(f"{mypid}:Exception writing to db. {e=} {letter=} {pangram=} {results=}")
        return False

    finally:
        mylock.release()
        
    return True


def bee_main(myargs:argparse.Namespace) -> int:
    """
    Examine the arguments to the program, and do the appropriate
    things. First step is reading the dictionary.
    """
    global verbose

    ###
    # Assume the dictionary conforms to the NYTimes rules.
    ###
    with open(myargs.dict) as f:
        words = f.read().split()

    verbose and print(f"Spelling Bee for {len(words)} words.")

    ###
    # If batch is set, we are not solving one spelling bee, 
    # but all of them. 
    ###
    if myargs.batch: 
        return beehive(myargs, words)

    if myargs.middle:
        r_letter = myargs.middle
        letters = myargs.letters
    else:
        r_letter = myargs.letters[0]
        letters = myargs.letters[1:]

    c_expression = build_regex(r_letter, letters)
    print(sorted(tuple(_ for _ in words if c_expression.fullmatch(_))))

    return os.EX_OK


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(prog="bee", 
        description="What bee does, bee does best.")

    parser.add_argument('-b', '--batch', action='store_true',
        help="find all the pangrams in the dictionary, and test all the circular shifts of each pangram for the spelling bee words.")

    parser.add_argument('--cpus', type=int, default=1,
        help="number of cpus to use in batch mode, assuming one process per core.")

    parser.add_argument('-d', '--dict', type=str, default=default_word_list,
        help="Name of the dictionary file.")

    parser.add_argument('--db', type=str, default="",
        help="Name of the database to which to write the results.")

    parser.add_argument('-l', '--letters', type=str,
        help="Letters to use, either six letters, or seven with the required letter first.")

    parser.add_argument('-m', '--middle', type=str, 
        help="Middle letter")

    parser.add_argument('-v', '--verbose', action='store_true',
        help="Be chatty about what is taking place.")

    myargs = parser.parse_args()

    if not myargs.batch and not myargs.letters:
        print("You must supply the --letters argument; 7 letters with the required letter first.")
        print("Use -h to get help.")
        sys.exit(os.EX_DATAERR)

    verbose = myargs.verbose

    try:
        db = sqlitedb.SQLiteDB(myargs.db)
        db.execute_SQL("pragma journal_mode=wal")
    except:
        db = None
        print(f"{myargs.db} not found or is not a database.")

    try:
        ###
        # Find the name of the _main function in this file, and
        # start the program by calling it with myargs.
        ###
        vm_callable = f"{os.path.basename(__file__)[:-3]}_main"
        sys.exit(globals()[vm_callable](myargs))
        

    except Exception as e:
        print(f"Unhandled exception {e}")

    finally:
        print(f"Elapsed time: {time.time()-start_time} seconds.")

