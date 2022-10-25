# spellingbee
A simple program illustrating a solution to the NYTimes Spelling Bee daily puzzle.

https://www.nytimes.com/puzzles/spelling-bee

# TOC:
- Requirements
- Use to solve SpellingBee
- Parallel processing
- ``with-db`` branch

# Requirements

Python 3.8 or later is required. No libraries outside the Python core
distro are required. The program has been tested (well, executed anyway)
on Mac OS 11.6 and 12.0, Fedora 35, and RHEL 7, 8, and Centos 9. Assuming
you have a spelling dictionary and know its location, it should also
work on Windows.

For Mac and Linux, the default dictionary is used if none is specified.

# Use to solve SpellingBee

```
usage: bee [-h] [-b] [--cpus CPUS] [-d DICTIONARY] [-l LETTERS] [-m MIDDLE] [-v]

What bee does, bee does best.

optional arguments:
  -h, --help            show this help message and exit
  -b, --batch           test the entire dictionary
  --cpus CPUS           number of cpus to use in batch mode.
  -d DICTIONARY, --dictionary DICTIONARY
                        Name of the dictionary file.
  -l LETTERS, --letters LETTERS
                        Letters to use, either six letters, or seven with the required letter first.
  -m MIDDLE, --middle MIDDLE
                        Middle letter
  -v, --verbose         Be chatty about what is taking place.
```

These two executions will produce the same result.



```
python bee.py --letters george --middle f 
python bee.py --letters fgeorge
``` 

Specifically, 

```
['feer', 'feere', 'feoff', 'feoffee', 'feoffor', 'fogger', 'fogo', 'fore', 
'forego', 'foregoer', 'forge', 'forger', 'forgo', 'forgoer', 'free', 'freer', 
'froe', 'frog', 'frore', 'geoff', 'goff', 'goffer', 'gofferer', 'goof', 
'goofer', 'groff', 'ofer', 'offer', 'offeree', 'offerer', 'offeror', 'reef', 
'reefer', 'refer', 'referee', 'referrer', 'reforge', 'reforger', 'reoffer', 
'reroof', 'roof', 'roofer']
```

# Parallel processing

This branch is set up for parallel processing. The code will determine
the number of available CPUs, and use them all, or exactly as many as
you specify.  Included is the 20,000 word dictionary based on the most
common words in English. Outside of some proper nouns, it tracks the
NYTimes dictionary used with their SpellingBee program relatively well.

`--cpus` determines the number of child processes. You can request any
number that you want to use, including exceeding the number of cores
available to. 

The easiest way to understand the effects of child processes and 
available cores is to run the program using the `time` command. 
In this example on a 12-core CPU, we see linear scaling. First with
6 cores in use:

```
[~]: time python bee.py -b --cpus 6 --dict 20k.txt
Using 6 processes.
Child process 623871 is analyzing 547 pangrams.
Child process 623872 is analyzing 546 pangrams.
Child process 623873 is analyzing 546 pangrams.
Child process 623874 is analyzing 546 pangrams.
Child process 623875 is analyzing 546 pangrams.
Child process 623876 is analyzing 546 pangrams.
child_pid=623871 has completed with status=0
child_pid=623872 has completed with status=0
child_pid=623875 has completed with status=0
child_pid=623873 has completed with status=0
child_pid=623876 has completed with status=0
child_pid=623874 has completed with status=0
Elapsed time: 120.51243424415588 seconds.

real	2m0.581s
user	11m48.236s
sys	0m0.049s
```

And then with the full 12:

```
[~]: time python bee.py -b --cpus 12 --dict 20k.txt
Using 12 processes.
Child process 623346 is analyzing 274 pangrams.
Child process 623347 is analyzing 273 pangrams.
Child process 623348 is analyzing 273 pangrams.
Child process 623349 is analyzing 273 pangrams.
Child process 623350 is analyzing 273 pangrams.
Child process 623351 is analyzing 273 pangrams.
Child process 623352 is analyzing 273 pangrams.
Child process 623353 is analyzing 273 pangrams.
Child process 623354 is analyzing 273 pangrams.
Child process 623355 is analyzing 273 pangrams.
Child process 623356 is analyzing 273 pangrams.
Child process 623357 is analyzing 273 pangrams.
child_pid=623355 has completed with status=0
child_pid=623346 has completed with status=0
child_pid=623349 has completed with status=0
child_pid=623354 has completed with status=0
child_pid=623350 has completed with status=0
child_pid=623353 has completed with status=0
child_pid=623348 has completed with status=0
child_pid=623351 has completed with status=0
child_pid=623352 has completed with status=0
child_pid=623357 has completed with status=0
child_pid=623347 has completed with status=0
child_pid=623356 has completed with status=0
Elapsed time: 61.22240591049194 seconds.

real	1m1.291s
user	12m6.510s
sys	0m0.071s
```

Now, let's ask for more than are available. The cores on the above 
computer are hyperthreaded, so we might expect some advantage in 
trying to use them, but there is none.

```
[~]: time python bee.py -b --cpus 24 --dict 20k.txt
Using 24 processes.
Child process 623448 is analyzing 137 pangrams.
Child process 623449 is analyzing 137 pangrams.
Child process 623450 is analyzing 137 pangrams.
Child process 623451 is analyzing 137 pangrams.
Child process 623452 is analyzing 137 pangrams.
Child process 623453 is analyzing 137 pangrams.

... deleted lines ...

child_pid=623464 has completed with status=0
child_pid=623456 has completed with status=0
child_pid=623452 has completed with status=0
child_pid=623455 has completed with status=0
child_pid=623460 has completed with status=0
child_pid=623453 has completed with status=0
child_pid=623449 has completed with status=0
Elapsed time: 63.63719820976257 seconds.

real	1m3.706s
user	25m8.850s
sys	0m0.215s
```

If we ask for 50, there is still not much of an effect:
```
[~]: time python bee.py -b --cpus 50 --dict 20k.txt
Using 50 processes.
Child process 623559 is analyzing 66 pangrams.
Child process 623560 is analyzing 66 pangrams.
Child process 623561 is analyzing 66 pangrams.
Child process 623562 is analyzing 66 pangrams.
Child process 623563 is analyzing 66 pangrams.
Child process 623564 is analyzing 66 pangrams.

... deleted lines ...

child_pid=623585 has completed with status=0
child_pid=623590 has completed with status=0
child_pid=623594 has completed with status=0
child_pid=623576 has completed with status=0
child_pid=623584 has completed with status=0
child_pid=623574 has completed with status=0
Elapsed time: 64.4562349319458 seconds.

real	1m4.525s
user	25m29.045s
sys	0m0.418s
```

# with-db branch

Any filtering of the dictionary should be done first. The project now
has two "bee" dictionaries that are already filtered.

A SQLite3 database is used to store the results. The parameters are now:

```
usage: bee [-h] [-b] [--cpus CPUS] [-d DICT] [--db DB] [-l LETTERS] [-m MIDDLE] [-v]

What bee does, bee does best.

optional arguments:
  -h, --help            show this help message and exit
  -b, --batch           find all the pangrams in the dictionary, and test 
                        all the circular shifts of
                        each pangram for the spelling bee words.
  --cpus CPUS           number of cpus to use in batch mode, assuming one process per core.
  -d DICT, --dict DICT  Name of the dictionary file.
  --db DB               Name of the database to which to write the results.
  -l LETTERS, --letters LETTERS
                        Letters to use, either six letters, or seven with the required 
                        letter first.
  -m MIDDLE, --middle MIDDLE
                        Middle letter
  -v, --verbose         Be chatty about what is taking place.
```


