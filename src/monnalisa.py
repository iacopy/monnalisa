import argparse
import os
import shutil
import sys
from functools import partial
from itertools import combinations
from operator import itemgetter
from random import shuffle

import crossover
from drawer import PolygonsEncoder
from evaluator import ImageEvaluator, func_evaluate
from history import HistoryIO
from island import Island

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

    im_eval = ImageEvaluator(options.target, resize=options.resize)
    image_size = im_eval.target_size
    polygons_encoder = PolygonsEncoder(
        image_size, n_total_sides, min_sides=options.min_sides, max_sides=options.max_sides)
    evaluate = partial(func_evaluate, polygons_encoder, im_eval)

    islands = tuple([Island(polygons_encoder, im_eval) for _ in range(options.n_islands)])
    best_ev_offspring = islands[0].best  # arbitrary individual
    status = {
        'best_ev_offspring': best_ev_offspring,
        'islands': islands,
    }

    history_io = HistoryIO(options)
    if history_io.exists():
        if options.restart:
            print('Resetting history', history_io.id)
            history_io.init()
            history_io.init_stats(status)
            history_io.init_plot(status)
        else:
            print('Resuming existing history', history_io.id)
            status = history_io.resume()
            islands = status['islands']
            best_ev_offspring = status['best_ev_offspring']
    else:
        print('Brand new history', history_io.id)
        history_io.init()
        history_io.init_stats(status, plot=True)

    print('islands =', islands)

    while True:
        for i_isla, isla in enumerate(islands):
            delta = isla.run(options.crossover_freq)

            print('i = {i}, it = {it:,}, v = {ev:,}'.format(
                i=i_isla, it=isla.iteration, ev=isla.best['evaluation']))

            if delta < 0:
                isla_best_dst = os.path.join(history_io.dirpath, 'best-island-{}-{}.png'.format(i_isla, isla.id[:7]))
                isla.best['phenotype'].save(isla_best_dst)

        islands_best_ev = [isla.best_evaluation for isla in islands]

        new_best_ev_offspring = mating(
            islands, best_ev_offspring, evaluate,
            f1_size=options.f1,
            f2_size=options.f2,
            n_crossovers=options.n_crossovers,
        )
        if new_best_ev_offspring:
            print('New best crossover! ev = {:,}'.format(new_best_ev_offspring['evaluation']))
            new_best_ev_offspring['phenotype'].save(os.path.join(history_io.dirpath, 'best-crossover.png'))
            best_ev_offspring = new_best_ev_offspring

        if best_ev_offspring['evaluation'] < min(islands_best_ev):
            print('crossover is currently the best: {:,}'.format(best_ev_offspring['evaluation']))

        status = {'islands': islands, 'best_ev_offspring': best_ev_offspring}
        history_io.save(status)
        history_io.update_stats(status, plot=True)
        history_io.update_genomes(status)


def mating(islands, best_ev_offspring, evaluate, f1_size, f2_size, n_crossovers=1):
    f1_offsprings = get_offsprings(
        [best_ev_offspring['genome']] + [isla.best['genome'] for isla in islands],
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
    if ev_offsprings[0]['evaluation'] < best_ev_offspring['evaluation']:
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


def get_options():
    parser = argparse.ArgumentParser()
    parser.add_argument('target', help='target image path')
    parser.add_argument('--resize', type=int, default=128,
        help='resize target image smaller while keeping aspect ratio [default: %(default)s]')
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
    parser.add_argument('--f1', type=int, default=32, help='f1 generation size')
    parser.add_argument('--f2', type=int, default=64, help='f2 generation size')
    parser.add_argument('--min-sides', type=int, default=3, help='[default: %(default)s]')
    parser.add_argument('--max-sides', type=int, default=6, help='[default: %(default)s]')
    parser.add_argument('--iterations', type=int, default=STOP,
        help='number of iterations [default: %(default)s]')
    parser.add_argument('-m', '--image_mode', default='RGB', help='[default: %(default)s]')
    parser.add_argument('--p-position', action='store_true',
        help='enable single position probability mutations (experimental)')
    parser.add_argument('--restart', default=False, action='store_true',
        help='do not resume existing history, but *erase* it and restart [default=%(default)s]')

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
