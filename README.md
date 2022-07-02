# spellingbee

Credit: https://nytimes.com/spellingbee

TL;DR version --- build words at least 4 letters long from a set of 7 letters,
where one of them is required. There is never an `S` in the set, and there is
at least one word that contains all seven letters (the "pangram").

The Spelling Bee has given me many opportunities to spread the word about Python.
There are a number of trivial questions about Spelling Bee that can be answered
by a one-line Python statement, and that is itself an interesting property of 
both the puzzle and Python.

For example .. What is the longest pangram?

```python
max((len(w), w) 
    for w in open('/usr/share/dict/linux.words').read().split()
        if len(set(w)) == 7 and 's' not in w)
```

# Requirements

Python 3.8 or later is required. No libraries outside the Python core
distro are required. The program has been tested (well, executed anyway)
on Mac OS 11.6 and 12.0, Fedora 35, and RHEL 7 and 8, Rocky Linux 8, and Centos Stream 9. Assuming you have
a spelling dictionary and know its location, it should also work on 
Windows.

For Mac and Linux, the default dictionary is used if none is specified.

# Use

```
 bee [-h] [-d DICTIONARY] -l LETTERS [-m MIDDLE]

What bee does, bee does best.

optional arguments:
  -h, --help            show this help message and exit
  -d DICTIONARY, --dictionary DICTIONARY
                        Name of the dictionary file.
  -l LETTERS, --letters LETTERS
                        Letters to use, either six letters, or seven with the required letter first.
  -m MIDDLE, --middle MIDDLE
                        Middle letter
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
