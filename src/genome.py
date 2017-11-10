from random import choice
from random import random as rand


def generate(bases, length):
    """Generate random 01 string."""
    return ''.join([choice(bases) for _ in range(length)])


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


def get_rand_positions(length, mutation_rate):
    """
    Extract a random number of random positions within `length`, given
    a per-basis `mutation_rate`.

    n!/(k!(n-k)!)*(1/n^k) * (1 -1/n)^(n-k)
    """
    return [i for i in range(length) if rand() <= mutation_rate]

def slow_rand_weighted_mut_positions(genome_length, mutation_rates):
    return [i for i in range(genome_length) if rand() <= mutation_rates[i]]

