import argparse
import os
import shutil
import sys
from itertools import combinations
from operator import itemgetter
from random import shuffle

import crossover
from drawer import PolygonsEncoder
from evaluator import ImageEvaluator, evaluate
from island import Island
from save import save_progress


BASES = '01'
N_POLYGONS = 5
STOP = 10 ** 6
SAVE_INTERVAL = STOP / 10
MIN_SAVE_DT = 60
VISIBLE_DELTA_EV = 10 ** 6


def main(options):
    """
    Simplest GA main function.
    """
    n_polygons = options.n_polygons
    print('drawing {} with {} polygons'.format(options.target, n_polygons))

    n_total_sides = n_polygons * options.max_sides
    print('target: {}'.format(repr(options.target)))
    print('n_polygons: {}'.format(options.n_polygons))
    print('n_total_sides: {}'.format(n_total_sides))

    evaluator = ImageEvaluator(options.target)
    image_size = evaluator.target_size
    polygons_encoder = PolygonsEncoder(
        image_size, n_total_sides, min_sides=options.min_sides, max_sides=options.max_sides)

    islands = tuple([Island(polygons_encoder, evaluator) for _ in range(options.n_islands)])
    best_ev_offspring = islands[0].best  # arbitrary individual
    print('islands =', islands)

    while True:
        for i_isla, isla in enumerate(islands):
            delta = isla.run(options.crossover_freq)

            print('i = {i}, it = {it:,}, v = {ev:,}'.format(
                i=i_isla, it=isla.iteration, ev=isla.best['evaluation']))

            if delta < 0:
                dst = save_progress(isla, options)
                isla_best_dst = os.path.join(evaluator.target_dst_dir, 'best-island-{}-{}.png'.format(i_isla, isla.id[:7]))
                shutil.copy(dst, isla_best_dst)

        islands_best_ev = [isla.best_evaluation for isla in islands]

        f1_offsprings = get_offsprings([best_ev_offspring['genome']] + [isla.best['genome'] for isla in islands], n_crossovers=options.n_crossovers)
        print('f1: {:,}'.format(len(f1_offsprings)))
        f2_offsprings = get_offsprings(f1_offsprings, n_crossovers=options.n_crossovers)
        print('f2: {:,}'.format(len(f2_offsprings)))
        offsprings = f1_offsprings + f2_offsprings
        ev_offsprings = [evaluate(polygons_encoder, evaluator, genome) for genome in offsprings]
        ev_offsprings.sort(key=itemgetter('evaluation'))
        if ev_offsprings[0]['evaluation'] < best_ev_offspring['evaluation']:
            best_ev_offspring = ev_offsprings[0]
            best_ev_offspring['phenotype'].save(os.path.join(evaluator.target_dst_dir, 'best-crossover.png'))
            print('New best crossover!', best_ev_offspring['evaluation'])
        if best_ev_offspring['evaluation'] < min(islands_best_ev):
            print('crossover is currently the best: {:,}'.format(best_ev_offspring['evaluation']))


def get_offsprings(parents, n_crossovers=1, n_max_offsprings=64):
    """Recombinate parents individuals with crossover.

    Also keep parents information.

    Arguments:
        parents {list} -- parents sources for crossovers
    """
    offsprings = []
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
    shuffle(offsprings)
    return offsprings[: n_max_offsprings]


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


def get_options():
    parser = argparse.ArgumentParser()
    parser.add_argument('target', help='target image path')
    parser.add_argument('-p', '--n-polygons', type=int, default=64,
        help='number of polygons to use [default: %(default)s]')
    parser.add_argument('-i', '--n-islands', type=int, default=2,
        help='number of islands [default: %(default)s]')
    parser.add_argument('-c', '--crossover-freq', type=int, default=1000,
        help='number of separate islands iterations between crossover [default: %(default)s]')
    parser.add_argument('-n', '--n-crossovers', type=int, default=1,
        help='number of for crossover reproductions for each couple of partners [default: %(default)s]')
    parser.add_argument('-s', '--saving-freq', type=int, default=1000,
        help='image saving frequency in iterations [default: %(default)s]')
    parser.add_argument('--min-sides', type=int, default=3, help='[default: %(default)s]')
    parser.add_argument('--max-sides', type=int, default=6, help='[default: %(default)s]')
    parser.add_argument('--iterations', type=int, default=STOP,
        help='number of iterations [default: %(default)s]')
    parser.add_argument('-m', '--image_mode', default='RGB', help='[default: %(default)s]')
    parser.add_argument('--p-position', action='store_true',
        help='enable single position probability mutations (experimental)')

    options = parser.parse_args()
    if "RANDOMSEED" in os.environ:
        seed_text = os.environ["RANDOMSEED"]
        try:
            options.seed = int(seed_text)
        except ValueError:
            sys.exit("RANDOMSEED={0!r} invalid".format(seed_text))
    else:
        options.seed = None
    return options


if __name__ == '__main__':
    options = get_options()
    main(options)
