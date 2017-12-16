import click
import time
import json
import sys
import os
import concurrent.futures
from itertools import product
import thread
import threading

from pyethapp.accounts import Account


def write_tried_file(tried, filename='tried.json'):
    with open(filename, 'w') as f:
        f.write(json.dumps(tried))


class ParallelTried(object):

    def __init__(self, tried, threadsnum):
        self.lock = threading.Lock()
        self.tried = tried
        self.threadsnum = threadsnum
        self.multiplier = int(100 / threadsnum)

        def maybe_update_tried(self, tried, count, threadid):
            if count != 0 and count % ((threadid + 1) * 25) == 0:
                with self.lock:
                    self.tried.extend(tried)
                    write_tried_file(self.tried)
                    return []
            else:
                return tried


def when_found_in_thread(password):
    print("FOUND IT!!! -- {}".format(password))
    with open('FOUND.pass', 'w') as f:
        f.write(password)
    os._exit(0)
    thread.interrupt_main()


def listchunks(l, n):
    n = int(len(l)/n)
    n = max(1, n)
    return (l[i:i+n] for i in xrange(0, len(l), n))


def replace_letter(word, index, letter):
    return word[:index] + letter + word[index + 1:]


def get_product(l1, l2, oneway=True):
    start = list(product(l1, l2))
    start = [t[0] + t[1] for t in start]
    if not oneway:
        other = list(product(l2, l1))
        other = [t[0] + t[1] for t in other]
        start.extend(other)
    return start


def _generate_word_permutations(word):
    """Generate permutations of a word according to a set of rules. This function
    contains rules for all possible combinations of 1337 speak and
    capitalizations"""
    words = [word]
    for i, letter in enumerate(word):
        if letter == 'a':
            new_word = replace_letter(word, i, 'A')
            words.extend(generate_word_permutations(new_word))
            new_word = replace_letter(word, i, '@')
            words.extend(generate_word_permutations(new_word))
            new_word = replace_letter(word, i, '4')
            words.extend(generate_word_permutations(new_word))
        elif letter == 'i':
            new_word = replace_letter(word, i, 'I')
            words.extend(generate_word_permutations(new_word))
            new_word = replace_letter(word, i, '1')
            words.extend(generate_word_permutations(new_word))
        elif letter == 'e':
            new_word = replace_letter(word, i, 'E')
            words.extend(generate_word_permutations(new_word))
            new_word = replace_letter(word, i, '3')
            words.extend(generate_word_permutations(new_word))
        elif letter == 'o':
            new_word = replace_letter(word, i, 'O')
            words.extend(generate_word_permutations(new_word))
            new_word = replace_letter(word, i, '0')
            words.extend(generate_word_permutations(new_word))
        elif letter.isalpha() and letter.islower():
            new_word = replace_letter(word, i, letter.capitalize())
            words.extend(generate_word_permutations(new_word))

    return words


def generate_word_permutations(word):
    return list(set(_generate_word_permutations(word)))


def call(keyfile, password):
    print("------------------------------------------------------------------")
    print("Trying {}".format(password))
    print("------------------------------------------------------------------")

    try:
        Account.load(keyfile, password=password)
    except ValueError as e:
        if str(e) == 'MAC mismatch. Password incorrect?':
            return False
        # else raise, as we got unexpected error
        raise e

    print("Found password: {}".format(password))
    return True


def import_tried_file(name='tried.json'):
    try:
        with open(name, 'r') as f:
            tried = json.loads(f.read())
    except:
        tried = []
    return tried


def search_onethread(keyfile, possibilities, tried):
    total = len(possibilities)
    time1 = time.time()
    time_diff = None
    estimate_given = None
    for count, password in enumerate(possibilities):
        print("----- PROGRESS: {} / {}  -- Tried: {}".format(
                count + 1,
                total,
                len(tried)
        ))
        if estimate_given:
            if time_diff:
                mins = time_diff * ((total - count) / 10) / 60
            else:
                mins = estimate_given
            print("----- Estimated Time Remaining: {} mins".format(mins))
            estimate_given = mins
            time_diff = None
        if call(keyfile, password):
            print("FOUND IT")
            sys.exit(0)

        tried.append(password)
        if count != 0 and count % 9 == 0:
            write_tried_file(tried)
            time_diff = time.time() - time1
            time1 = time.time()
            estimate_given = True


def search_perthread(keyfile, possibilities, identifier, ctx):
    total = len(possibilities)
    tried = []
    for count, password in enumerate(possibilities):
        print("-----Thread {} PROGRESS: {} / {}  -- Tried: {}".format(
                identifier,
                count + 1,
                total,
                len(tried)
        ))
        if call(keyfile, password):
                when_found_in_thread(password)

        tried.append(password)
        tried = ctx.maybe_update_tried(tried, count, identifier)
    return tried


def generate_possibilities(inputfile):
    tried = import_tried_file()
    words = []
    phraselists = []
    with open(inputfile, 'r') as f:
        inputdata = json.loads(f.read())

    for entry in inputdata:
        if isinstance(entry, basestring):
            words.append(entry)
        elif isinstance(entry, list):
            if not all(isinstance(x, basestring) for x in entry):
                print("Provided a list at input that does not contain only strings")
                sys.exit(1)

            words.append(entry)

    if len(words) == 0:
        print("Provided no words in the input list")
        sys.exit(1)

    word_perms = []
    for word in words:
        if isinstance(word, list):
            word_perms.append(word)
        else:
            word_perms.append(generate_word_permutations(word))

    possibilities = word_perms[0]
    for perm in word_perms[1:]:

        possibilities = get_product(possibilities, perm, oneway=False)

    possibilities = list(set(possibilities) - set(tried))
    return possibilities, tried


def start_search(keyfile, possibilities, tried, threads):
    if threads == 1:
        search_onethread(keyfile, possibilities, tried)
    else:
        ctx = ParallelTried(tried, threads)
        split_possibilities = listchunks(possibilities, threads)
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
                futures = [
                    executor.submit(
                        search_perthread,
                        keyfile,
                        workchunk,
                        threadid,
                        ctx
                    )
                    for threadid, workchunk in enumerate(split_possibilities)
                ]

                results = []
                for future in futures:
                        results.extend(future.result())

        tried.extend(results)
        write_tried_file(tried)


@click.option(
    '--keyfile',
    help='Path to the keyfile whose password we are trying to find',
    required=True,
    type=click.Path(exists=True),
)
@click.option(
    '--threads',
    required=False,
    help='number of threads to do work',
    default=1,
)
@click.option(
    '--input-file',
    help=(
        'Path to the input file containing the words to combine in order to '
        'find the password.'
    ),
    required=True,
    type=click.Path(exists=True),
)
@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx, threads, keyfile, input_file, **kwargs):
    if ctx.invoked_subcommand is not None:
        ctx.obj = kwargs
    else:
        possibilities, tried = generate_possibilities(input_file)
        start_search(keyfile, possibilities, tried, threads)


@main.command()
@click.argument('files', nargs=-1)
def combine_tried_files(files):
        tried = []
        for arg in files:
            tried.extend(import_tried_file(arg))
        tried = list(set(tried))
        with open('combinedtried.json', 'w') as f:
            f.write(json.dumps(tried))


@main.command()
@click.argument('f', type=click.Path(exists=True), default='tried.json')
def check_tried_length(f):
        tried = import_tried_file(f)
        orig_length = len(tried)
        tried = list(set(tried))
        new_length = len(tried)

        if new_length == orig_length:
            print("Tried file contains {} unique entries".format(new_length))
        else:
            print("Tried file contains {} entries, {} of which are unique".format(orig_length, new_length))


@main.command()
@click.argument('filename', type=click.Path(exists=True), default='tried.json')
def make_tried_unique_list(filename):
        tried = import_tried_file(filename)
        orig_length = len(tried)
        tried = list(set(tried))
        new_length = len(tried)

        if new_length == orig_length:
            print("Tried file contains {} unique entries. Doing nothing".format(new_length))
        else:
            print("Tried file contains {} entries, {} of which are unique".format(orig_length, new_length))
            print("Writting the unique entries only in a file")
            write_tried_file(tried, filename=filename)


@main.command()
@click.argument('password')
@click.option(
    '--keyfile',
    help='Path to the keyfile whose password we are trying to find',
    required=True,
    type=click.Path(exists=True),
)
def trypass(keyfile, password):
        if not call(keyfile, password):
            print("Password mismatch")


if __name__ == '__main__':
        main()
