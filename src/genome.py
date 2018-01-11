from collections import Counter
from itertools import combinations
from math import factorial as f
from math import sqrt
from random import random as rand
from random import choice, choices, sample


def generate(bases, length):
    """Generate random 01 string."""
    return ''.join([choice(bases) for _ in range(length)])


def opposite_genome(genome):
    rv = []
    for base in genome:
        rv.append(str(int(not int(base))))
    return ''.join(rv)


def genetic_distances(*genomes):
    """
    Restituisce una lista delle distanze genetiche tra tutti i genomi passati.

    >>> genetic_diff('0010', '1010')
    [1.0]
    >>> r = genetic_diff('0000', '1111', '0000')
    [2.0, 0.0, 2.0]
    """
    rv = []
    for genome_a, genome_b in combinations(genomes, 2):
        rv.append(sum((abs(int(a) - int(b)) for a, b in zip(genome_a, genome_b))))
    return rv


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


def rand_mut_pos_gen(genome_length, mutation_rate, n_extractions):
    """
    Metodo lento di ottenimento di combinazioni di mutazioni
    basato su un lancio di un numero casuale per ogni base.
    """
    for _ in range(n_extractions):
        yield [i for i in range(genome_length) if rand() <= mutation_rate]


def slow_rand_weighted_mut_positions(genome_length, mutation_rates):
    return [i for i in range(genome_length) if rand() <= mutation_rates[i]]


def get_probs_k_mutations(n, mutation_rate, cutoff=1e-12):
    """
    Restituisce la lista di probabilità che avvengano
    esattamente k mutazioni, per k che va da 0 a `n`.

    Quando la probabiltà scende sotto un certo valore di `cutoff`,
    le restanti probabilità vengono settate a 0.
    """
    probs = [0] * (n + 1)
    for k in range(n + 1):
        p_k = (f(n) / (f(k) * f(n - k))) * \
              (mutation_rate ** k) * \
              (1 - mutation_rate) ** (n - k)
        probs[k] = p_k
        if p_k < cutoff:
            probs[k: n + 1] = [0] * (n - k)
            break
    return probs


def fast_rand_mut_positions_generator(genome_length, mutation_rate, n_extractions):
    """
    Generatore efficiente di `n_extractions` combinazioni di posizioni
    di mutazioni per un genoma o cromosoma di lunghezza `genome_length`,
    in cui la probabilità di mutazione di ogni base è `mutation_rate`.
    """
    probs = get_probs_k_mutations(
        genome_length, mutation_rate,
        cutoff=1 / (n_extractions * 2)
    )
    for n_mutations in choices(range(len(probs)), probs, k=n_extractions):
        yield sample(range(genome_length), n_mutations)


##########################################################################
######### Per vedere e confrontare i due tipi di distribuzione ###########
##########################################################################

# Le distribuzioni dovrebbero essere identiche, anche se uno dei due metodi
# e' moolto piu' lento


def count_n_rand_k_mutations(genome_length, mutation_rate, n_extractions=1):
    """Restituisce il contatore di quante volte è avvenuto un certo numero
    di mutazioni (o eventi, in generale). Metodo LENTO.
    """
    print('{:,} extractions'.format(n_extractions))
    counter = Counter()
    for _ in range(n_extractions):
        counter[sum([1 for _ in range(genome_length) if rand() <= mutation_rate])] += 1
    assert sum(counter.values()) == n_extractions
    print(counter.most_common())
    return counter


def count_n_rand_k_mutations_weights(genome_length, mutation_rate, n_extractions=1):
    """Restituisce il contatore di quante volte è avvenuto un certo numero
    di mutazioni (o eventi, in generale). Metodo veloce.

    Calcola le probabilità che avvengano esattamente `k` mutazioni,
    con `k` che va da 0 a `genome_length`.
    Di fatto le probabilità tendono a 0 abbastanza presto.

    Esempio, con un `mutation_rate` pari a 1 / `genome_length` sono valori vicini a
    [0.3679, 0.36879, 0.06085, 0.18342, 0.01553, 0.00286, 0.00061, 4e-05]
    """
    print('{:,} extractions'.format(n_extractions))
    probs = get_probs_k_mutations(genome_length, mutation_rate)
    counter = Counter(choices(range(len(probs)), probs, k=n_extractions))
    print(counter.most_common())
    return counter
