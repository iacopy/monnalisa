from __future__ import division
from collections import Counter
from itertools import combinations
from operator import attrgetter
from operator import itemgetter
from random import randrange
import argparse
import datetime
import os
import sys
import time

import numpy as np

from drawer import PolygonsEncoder
from drawer import ImageEvaluator
from drawer import draw_polygons
from drawer import evaluate
from genome import flip_mutate
from genome import genetic_diff
from genome import get_rand_positions
from genome import slow_rand_weighted_mut_positions
from drawer import __file__ as drawer__file__
from island import Island
from save import save_progress
import crossover

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
    target = options.target
    n_polygons = options.n_polygons
    pos_p_mut_changes = options.p_position

    min_save_dt = 0.5
    print('drawing {} with {} polygons'.format(options.target, n_polygons))

    n_total_sides = n_polygons * options.max_sides
    print('target: {}'.format(repr(options.target)))
    print('n_polygons: {}'.format(options.n_polygons))
    print('n_total_sides: {}'.format(n_total_sides))

    ### START ###
    evaluator = ImageEvaluator(options.target)
    image_size = evaluator.target_size
    polygons_encoder = PolygonsEncoder(
        image_size, n_total_sides, min_sides=options.min_sides, max_sides=options.max_sides)
    genome_size = polygons_encoder.genome_size
    mut_pos_learning_rate = 1 / genome_size

    islands = [Island(polygons_encoder, evaluator) for _ in range(options.n_islands)]
    print('islands =', islands)

    while True:
        for i_isla, isla in enumerate(islands):
            isla.run(options.crossover_freq)

            print('i = {i}, it = {it:,}, v = {ev:,}'.format(
                i=i_isla, it=isla.iteration, ev=isla.best['evaluation']))

            save_progress(isla, options)

        offsprings = get_offsprings(islands)

        ev_offsprings = [evaluate(polygons_encoder, evaluator, genome) for genome in offsprings]
        offsprings_ev = [x['evaluation'] for x in ev_offsprings]
        islands_best_ev = [isla.best_evaluation for isla in islands]
        destinations = islands_crossover_offsprings_tournament(islands_best_ev, offsprings_ev)
        for i_offspring, i_island in destinations.items():
            print('{} => {}'.format(i_offspring, i_island))
            islands[i_island].set_best(ev_offsprings[i_offspring])
            save_progress(islands[i_island], options)


def get_offsprings(islands):
    """Recombinate best islands individuals with crossover.

    Also keep parents information.

    Arguments:
        islands {list} -- islands sources for crossovers

    Returns:
        dict -- map offsprings with their parents.
    """

    offsprings = {}
    islands.sort(key=attrgetter('best_evaluation'), reverse=True)
    for (isla_a_index, isla_b_index) in combinations(range(len(islands)), 2):
        isla_a = islands[isla_a_index]
        isla_b = islands[isla_b_index]
        best_a = isla_a.best['genome']
        best_b = isla_b.best['genome']
        crossover_points = crossover.normal_rand_crossover_operator(best_a, best_b, min_n_events=0)
        if crossover_points:
            # otherwise no recombination, no new sequences
            parents = {isla_a_index, isla_b_index}
            for offspring in [
                ''.join(c) for c in crossover.crossover(best_a, best_b, crossover_points)
                ]:
                # keep parents information
                offsprings[offspring] = parents
    return offsprings


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
        help='number of polygons to use')
    parser.add_argument('-i', '--n-islands', type=int, default=1)
    parser.add_argument('-c', '--crossover-freq', type=int, default=1000,
        help='number of separate islands iterations between crossover')
    parser.add_argument('--min-sides', type=int, default=3)
    parser.add_argument('--max-sides', type=int, default=6)
    parser.add_argument('--iterations', type=int, default=STOP,
        help='number of iterations')
    parser.add_argument('-m', '--image_mode', default='RGB')
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
