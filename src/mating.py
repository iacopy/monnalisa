"""
Modulo che gestisce i meccanismi di riproduzione sessuata.
"""
from itertools import combinations
from operator import itemgetter
from random import shuffle

import crossover


def mate(islands, best_ev_offspring, evaluate, f1_size, f2_size, n_crossovers=1):
    f1_offsprings = get_offsprings(
        [isla.best['genome'] for isla in islands],
        n_max_offsprings=f1_size,
        n_crossovers=n_crossovers,
    )
    f2_offsprings = get_offsprings(
        f1_offsprings, n_max_offsprings=f2_size, n_crossovers=n_crossovers
    )
    print('f1: {:,}'.format(len(f1_offsprings)))
    print('f2: {:,}'.format(len(f2_offsprings)))
    offsprings = f1_offsprings + f2_offsprings

    ev_offsprings = [evaluate(genome) for genome in offsprings]
    ev_offsprings.sort(key=itemgetter('evaluation'))
    if ev_offsprings and ev_offsprings[0]['evaluation'] < best_ev_offspring['evaluation']:
        return ev_offsprings[0]


def get_offsprings(parents, n_max_offsprings=64, n_crossovers=1):
    """Recombinate parents individuals with crossover.

    Also keep parents information.

    Arguments:
        parents {list} -- parents sources for crossovers
    """
    offsprings = []
    # TODO: randomize parents or parents indices
    for (p_a_index, p_b_index) in combinations(range(len(parents)), 2):
        p_a = parents[p_a_index]
        p_b = parents[p_b_index]
        for i in range(n_crossovers):
            crossover_points = crossover.normal_rand_crossover_operator(p_a, p_b)
            if crossover_points:
                # otherwise no recombination, no new sequences
                for offspring in [
                    ''.join(c) for c in crossover.crossover(p_a, p_b, crossover_points)
                    ]:
                    offsprings.append(offspring)
        # avoid explosion of combinations
        if len(offsprings) >= n_max_offsprings:
            break
    shuffle(offsprings)
    return offsprings[: n_max_offsprings]


# XXX: unused function
def islands_crossover_offsprings_tournament(islands_best_ev, offsprings_ev):
    """
    Assign offsprings to islands if good enough.

    Deterministic, from best to worst.
    """
    # Store indices before sorting
    islands_indices = {x: i for i, x in enumerate(islands_best_ev)}
    offsprings_indices = {x: i for i, x in enumerate(offsprings_ev)}

    islands_best_ev.sort()
    offsprings_ev.sort()

    ret = {}
    i = o = 0
    while o < len(offsprings_ev) and i < len(islands_best_ev):
        current_o = offsprings_ev[o]
        current_i = islands_best_ev[i]
        if current_o < current_i:
            ret[offsprings_indices[current_o]] = islands_indices[current_i]
            o += 1
            i += 1
        else:
            i += 1
    return ret
