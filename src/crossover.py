from random import normalvariate
from random import sample

###########################
# Crossing over functions #
###########################

def crossover(seq1, seq2, points=()):
    """
    Returns 2 sequences with exchanged regions between seq1 and seq2.
    Make a len(points)-point(s) crossing-over.

    Do not assume any kind of base types (str, int, bool, ...).

    >>> crossover(list('TAGta'), list('gatGA'), (3,))
    (['T', 'A', 'G', 'G', 'A'], ['g', 'a', 't', 't', 'a'])

    >>> s1, s2 = crossover('ABCDEFGHIJ', 'abcdefghi', (3, 6))
    >>> ''.join(s1), ''.join(s2)
    ('ABCdefGHIJ', 'abcDEFghi')

    >>> s1, s2 = crossover('ABCDEF', 'abcdef', (1, 2, 3, 4, 5))
    >>> ''.join(s1), ''.join(s2)
    ('AbCdEf', 'aBcDeF')

    >>> crossover('AB', 'ab', ())
    (['A', 'B'], ['a', 'b'])

    >>> crossover('AB', 'ab', (0,))
    (['a', 'b'], ['A', 'B'])

    >>> s1 = 'PERFETTO'
    >>> s2 = 'confusione'
    >>> r1, r2 = crossover(s1, s2, (3,))
    >>> ''.join(r1)
    'PERfusione'
    >>> ''.join(r2)
    'conFETTO'
    """
    ret1 = list(seq1)
    ret2 = list(seq2)
    end = max(len(seq1), len(seq2))
    for i in range(0, len(points), 2):
        start = points[i]
        try:
            stop = points[i + 1]
        except IndexError:
            stop = end
        # One line python swap
        ret1[start: stop], ret2[start: stop] = ret2[start: stop], ret1[start: stop]
    return ret1, ret2


def normal_rand_crossover_operator(seq1, seq2, mu=1, sigma=0.666, min_n_events=1):
    """
    Restituisce una lista di n (numero casuale con distribuzione normale definita da `mu` e `sigma`)
    posizioni casuali (ciascuna posizione spazia tra 0 e la lunghezza delle sequenza più lunga).

    :param seq1: first sequence
    :param seq2: second sequence
    :param mu: normalvariate mu parameter
    :param sigma: normalvariate sigma parameter
    :param min_n_events: minumum number of points (recombination events)
    :return: list of crossover points
    """
    n_points = max(int((round(abs(normalvariate(mu, sigma))))), min_n_events)
    return sorted(sample(range(max(map(len, [seq1, seq2]))), n_points))


def rand_crossover(seq1, seq2, rand_crossover_operator=normal_rand_crossover_operator, **kwargs):
    """
    Perform a random crossing over between `seq1` and `seq2`.

    :param seq1: first sequence
    :param seq2: second sequence
    :param rand_crossover_operator: function which returns random crossover points given the 2 source sequences
    :return: a tuple of 2 sequences resulting from crossover
    """
    points = rand_crossover_operator(seq1, seq2, **kwargs)
    return crossover(seq1, seq2, points=points)
