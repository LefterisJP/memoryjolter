# Memory Jolter

Memory jolter is a python script with the intention to help people who have forgotten their ethereum keyfile password but still
vaguely remember possible combination of words that the password may have had. The script works by trying all possile combinations
of all possible permutations of the words depending on some rules. The permutation rules are hardcoded but can be easily adjusted
by tweaking the appropriate function.

The hardcoded permutation rules are for capilatization and 1337 speak, which is a common practise for many people who are trying to make passwords they can remember but also want to introduce special characters.

## Installation

You will need python 2.7. This sript does not work with python 3 due to dependency on pyethapp for unlocking the account.

Create a [virtualenv](http://docs.python-guide.org/en/latest/dev/virtualenvs/) for memory jolter and then install the requirements
by doing `pip install -r requirements.txt`.

## Usage

Run the script with `python main.py [ARGS]`.

The possible arguments and what they do are explained below.

### Key File

With `--keyfile pathtokeyfile` you need to provide the path to the keyfile whose password you are trying to find.

### Input File

With `--input-file pathtoinputfile` you need to provide the path to the file which contains the words and wordlists that will
act as input and whose permutations and combinations will be used to find the password.

The input file needs to be in JSON format and contain a JSON list. Each element of the list needs to contain either a string
or a list of string. For each string in the list we will compute all possible permutations. For each wordlist we will not compute
permutations but take all possible combinations of the words in the wordlist.

As an example look at the following json file:

```json
["cat", ["12", "$#"]]
```

This will produce the following possibilities:

```json
['c@T12', 'CaT$#', 'C4T$#', 'caT12', 'C@t12', 'C@t$#', 'C4t$#', 'cAT$#', 'cAt$#', 'CaT12', 'c@T$#', 'CAT12', 'C4t12', 'c4t$#', 'CAt$#', 'c4T$#', 'cAt12', 'C@T12', 'Cat12', 'c4T12', 'c@t12', 'CAT$#', 'caT$#', 'cAT12', 'Cat$#', 'cat$#', 'C@T$#', 'CAt12', 'cat12', 'C4T12', 'c@t$#', 'c4t12']
```

all of which will be tried against the provided keyfile

### Respect Word Order

This option is on by default. And it can be turned off by providing `--no-respect-word-order`. Respecting word order means that the possible combinations will be computed respecting the order of the elements given in the provided input list.

By providing `--no-respect-word-order` for the example input file given above we would get the following password possibilities, essentially doubling them:

```json
['caT$#', 'c@T12', 'CaT$#', 'C4T$#', 'caT12', '$#C4t', '12C4t', '$#c@t', '$#CaT', '12C@t', '12CaT', 'C@t12', 'C@T$#', '12CAt', '$#c@T', 'c@T$#', 'C4t$#', 'cAT$#', 'cAt$#', '12c@t', 'CaT12', '$#cAT', '$#C4T', '12C4T', 'C@t$#', '$#caT', '12C@T', '12caT', '12Cat', '$#Cat', 'c4T12', 'cAt12', 'c4t$#', 'CAt$#', 'c4T$#', 'CAT12', '$#CAT', '$#c4T', '12c4T', '$#C@T', '12cAT', 'C@T12', 'Cat12', '12cAt', 'C4t12', '$#CAt', 'c@t12', 'CAT$#', '$#cat', '12c@T', 'cAT12', 'Cat$#', 'cat$#', '$#cAt', '12c4t', '$#C@t', '12cat', 'CAt12', '12CAT', '$#c4t', 'cat12', 'C4T12', 'c@t$#', 'c4t12']
```

### Threads

The number of threads to use. By default this is a single thread. 


If you provide a number bigger than `1` here then the possible search space for the password is divided by that number and a work chunk is sent to each thread. Each thread then works on its own chunk in parallel greatly increasing the speed of the search.


## Saving tried passwords

In case you need to quit the program or it crashes we keep all the tried combinations in a local file called `tried.json`. When the program restarts then the `tried.json` is read and all already attempted passwords are subtracted from the search space.

This way you can resume your search at another time if it takes too long.

## Other commands

The script contains some other miscellaneous commands that may or may not come in handy.

### Combining Tried Files

If you have run the script in different computers and have created 2 different `tried.json` files then this command enables you to combine them into 1 file to be provided back to the script.

It works by doing:

`python main.py combine_tried_files FILE1 FILE2 ...`

and the result is saved into `combinedtried.json`

### Checking the number of tried passwords

You can inspect a tried file by using this comands:

`python main.py check_tried_length FILE`

By Default `FILE` is `tried.json`. This will return how many passwords have already been attempted. As the program continuously writes on this file, you can query this while the program runs.

### Compact the number of tried passwords

Even though the script should not write duplicated entried into the `tried.json` file it can happen due to some logic error. This command allows you to compact it and delete any and all duplicate entries.

`python main.py make_tried_unique_list FILE`

By default `FILE` is `tried.json`.

### Attempt a password manually

By using this command you can attempt to unlock the keyfile by providing a password manually.

`python main.py --keyfile PATHTOKEYFILE PASSWORDGOESHERE`



