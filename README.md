# spellingbee
A simple program illustrating a solution to the NYTimes Spelling Bee daily puzzle.

# Requirements

Python 3.8 or later is required. No libraries outside the Python core
distro are required. The program has been tested (well, executed anyway)
on Mac OS 11.6 and 12.0, Fedora 35, and RHEL 7 and 8. Assuming you have
a spelling dictionary and know its location, it should also work on 
Windows.

For Mac and Linux, the default dictionary is used if none is specified.

# Parallel processing

This branch is set up for parallel processing. The code will determine the
number of available CPUs, and use them all, or exactly as many as you specify. 
Included is the 20,000 word 
dictionary based on the most common words in English. Outside of some 
proper nouns, it tracks the NYTimes dictionary used with their SpellingBee
program relatively well. 

# Use

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
