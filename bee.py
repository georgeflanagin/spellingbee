# -*- coding: utf-8 -*-
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
import platform
import re

###
# From hpclib
###
import linuxutils

###
# Credits
###
__author__ = 'George Flanagin'
__copyright__ = 'Copyright 2021'
__credits__ = None
__version__ = 0.1
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


def bee_main(myargs:argparse.Namespace) -> int:
    with open(myargs.dictionary) as f:
        words = tuple(_.lower() for _ in f.read().split('\n') if len(_) > 3)

    if myargs.batch: 
        return beehive(myargs, words)

    if myargs.middle:
        r_letter = myargs.middle
        letters = myargs.letters
    else:
        r_letter = myargs.letters[0]
        letters = myargs.letters[1:]

    plenum = r_letter+letters
    c_expression = re.compile(f"[{letters}]*{r_letter}[{plenum}]*")

    print(sorted(tuple(_ for _ in words if c_expression.fullmatch(_))))
    return os.EX_OK


def beehive(myargs:argparse.Namespace, words:tuple) -> int:
    return os.EX_OK


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(prog="bee", 
        description="What bee does, bee does best.")

    parser.add_argument('-b', '--batch', action='store_true',
        help="test the entire dictionary')
    parser.add_argument('--cpus', type=int, default=1,
        help="number of cpus to use in batch mode.")
    parser.add_argument('-d', '--dictionary', type=str, default=default_word_list,
        help="Name of the dictionary file.")
    parser.add_argument('-l', '--letters', type=str, required=True,
        help="Letters to use, either six letters, or seven with the required letter first.")
    parser.add_argument('-m', '--middle', type=str, 
        help="Middle letter")

    myargs = parser.parse_args()

    try:
        vm_callable = "{}_main".format(os.path.basename(__file__)[:-3])
        sys.exit(globals()[vm_callable](myargs))

    except Exception as e:
        print(f"Unhandled exception {e}")


