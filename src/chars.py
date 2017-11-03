"""
Chars utils.
"""
from math import ceil
from math import log
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


def evaluator(target, candidate):
    """
    0 is best

    :rtype: int
    """
    return sum([a != b for a, b in zip(target, candidate)])


class CharEncoder:
    def __init__(self, char_pool, filler=' '):
        self.char_pool = char_pool
        pool_size = len(char_pool)
        if pool_size > len(set(char_pool)):
            print('Semi-fail: repeated characters in the char pool')
        self.n_bit = int(ceil(log(pool_size, 2)))
        surplus = 2 ** self.n_bit - pool_size
        if surplus:
            if len(filler) == 1:
                self.char_pool += filler * surplus
            else:
                self.char_pool += filler
            print('Added filler to char_pool ->', repr(self.char_pool))
        assert len(self.char_pool) == 2 ** self.n_bit,\
            'FAIL: numero di filler errato ({} expected, got {})'.format(surplus, len(filler))

    def encode(self, chars):
        return ''.join(
            [bin(self.char_pool.index(char))[2:].zfill(self.n_bit) for char in chars]
        )

    def decode(self, chrom_01):
        ret = []
        n_bit = self.n_bit
        for i in range(0, len(chrom_01), n_bit):
            tuplet = chrom_01[i: i + n_bit]
            dec = int(tuplet, 2)
            char = self.char_pool[dec]
            ret.append(char)
        return ''.join(ret)
