from __future__ import division
from chars import CharEncoder
from chars import evaluator
from chars import flip_mutate
from chars import generate
from chars import rand_positions
from chars import __file__ as chars__file__
from functools import partial
from random import seed
import string
import sys
import time
import os


BASES = '01'
CHARS = string.printable

#: To test cython boost
seed(4122)


def main(target, chars):
    """
    Simplest GA main function.
    """
    print('target: {}'.format(repr(target)))
    print('chars: {}'.format(repr(chars)))
    char_encoder = CharEncoder(chars)
    evaluate = partial(evaluator, target)
    genome_size = len(char_encoder.encode(target))
    father = generate(BASES, genome_size)
    father_phenotype = char_encoder.decode(father)
    father_evaluation = evaluate(father_phenotype)
    iteration = 0
    t0 = time.time()
    while father_evaluation:
        iteration += 1
        mut_positions = rand_positions(genome_size, 1.0 / genome_size)
        child = flip_mutate(mut_positions, father)
        child_phenotype = char_encoder.decode(child)
        child_evaluation = evaluate(child_phenotype)
        if child_evaluation < father_evaluation:
            print('success at {:,}'.format(iteration))
            print(child, child_phenotype, child_evaluation)
            father_evaluation = child_evaluation
            father = child

    et = time.time() - t0
    speed = '{:.3f} it/s'.format(iteration / et)

    try:
        impl_name = sys.implementation.name
        version = '.'.join(map(str, sys.implementation.version))
    except AttributeError:
        impl_name = sys.subversion[0]
        version = '.'.join(map(str, sys.version_info))
    filename = os.path.join(
        os.path.dirname(__file__),
        impl_name + version + '-' + os.path.basename(chars__file__)
    )
    with open('{}.bench.txt'.format(filename), 'a') as fp:
        fp.write(speed + '\n')
    print(chars__file__)
    print('{:,} iterations in {:.2f} s'.format(iteration, et))
    print(speed)


if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) == 2:
        target, chars = args
    elif len(args) == 1:
        target, chars = args[0], CHARS
    elif len(args) == 0:
        target, chars = 'Hello, World!', 'Helo, Wrd!'

    main(target, chars)
