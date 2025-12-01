# -*- coding: utf-8 -*-
import typing
from   typing import *

###
# Standard imports, starting with os and sys
###
min_py = (3, 7)
import os
import sys
if sys.version_info < min_py:
    print(f"This program requires Python {min_py[0]}.{min_py[1]}, or higher.")
    sys.exit(os.EX_SOFTWARE)

###
# Other standard distro imports
###
import argparse
from   collections.abc import *
import contextlib
import logging

###
# Installed libraries like numpy, pandas, paramiko
###

###
# From gkflib
###
from   exitcodes import ExitCode
import linuxutils
from   gkfdecorators import trap
from   autologger import AutoLogger

###
# imports and objects that were written for this project.
###
import enum
import math
import shlex
import subprocess
###
# Global objects
###
logger = None

###
# Credits
###
__author__ = 'George Flanagin'
__copyright__ = 'Copyright 2025'
__credits__ = 'Skyler He, Skyler He <skyleryh6km@gmail.com>'
__version__ = 1.1
__maintainer__ = 'George Flanagin'
__email__ = 'gflanagin@richmond.edu'
__status__ = 'production'
__license__ = 'MIT'


@trap
def dorunrun(command:Union[str, list, tuple],
    timeout:int=None,
    return_datatype:type=dict,
    OK_values:Iterable = (0,)) -> Union[str, bool, int, dict]:
    """
    A wrapper around (almost) all the complexities of running child
        processes. Note that it always runs with shell=False.

    Parameters:
    -----------
    command: A string, or a list of strings,
             that constitute the commonsense definition of the command to be attemped.
    timeout: Generally, we don't
    return_datatype: This argument corresponds to the item the caller wants returned.
                     It can be one of these values:

        - bool : True if the subprocess exited with code 0.
        - int  : the exit code itself.
        - str  : the stdout of the child process.
        - dict : everything as a dict of key-value pairs.

        The default data type is dict, and timeouts always return a dict.

    OK_values: By default, OK means zero. However, the caller can supply a group
        of codes that are interpreted as being acceptable.

    ----------
    Returns: A value corresponding to the requested info.
    """

    # If return_datatype is not in the list, use dict. Note
    # that the next statement covers None, as well.
    return_datatype = dict if return_datatype not in (int, str, bool) else return_datatype

    # Let's convert all the arguments to str and relieve the caller
    # of that responsibility.
    if isinstance(command, (list, tuple)):
        command = [str(_) for _ in command]
    elif isinstance(command, str):
        command = shlex.split(command)
    else:
        raise Exception(f"Bad argument type to dorunrun: {command=}")

    try:
        result = subprocess.run(command,
            timeout=timeout,
            input="",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False)
        i_code = code = result.returncode
        b_code = code in OK_values
        s = result.stdout[:-1] if result.stdout.endswith('\n') else result.stdout
        e = result.stderr[:-1] if result.stderr.endswith('\n') else result.stderr

        if return_datatype is int:
            return i_code
        elif return_datatype is str:
            return s
        elif return_datatype is bool:
            return b_code
        else:
            return {"OK":b_code,
                    "code":i_code,
                    "name":ExitCode(i_code).name,
                    "stdout":s,
                    "stderr":e}

    except subprocess.TimeoutExpired as e:
        return {"OK":False,
                "code":255,
                "name":ExitCode(255).name,
                "stdout":"",
                "stderr":""}

    except Exception as e:
        raise

