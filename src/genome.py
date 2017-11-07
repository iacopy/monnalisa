from random import choice
from random import random as rand


def generate(bases, length):
    """Generate random 01 string."""
    return ''.join([choice(bases) for _ in range(length)])


def rand_positions(length, mutation_rate):
    """
    Extract a random number of random positions within `length`, given
    a per-basis `mutation_rate`.
    """
    return [i for i in range(length) if rand() <= mutation_rate]


def flip_mutate(positions, genome):
    """
    Flip `genome` bases in `positions`.

    :rtype: str
    """
    ret = list(genome)
    for pos in positions:
        if ret[pos] == '0':
            ret[pos] = '1'
        else:
            ret[pos] = '0'
    return ''.join(ret)