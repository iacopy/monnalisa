from __future__ import division
from collections import Counter
from drawer import PolygonsEncoder
from drawer import ImageEvaluator
from drawer import draw_polygons
from genome import flip_mutate
from genome import get_rand_positions
from genome import slow_rand_weighted_mut_positions
from drawer import __file__ as drawer__file__
from random import randrange
import argparse
import sys
import time
import os


BASES = '01'
N_POLYGONS = 5
STOP = 10 ** 6
SAVE_INTERVAL = STOP / 10
MIN_SAVE_DT = 60
VISIBLE_DELTA_EV = 10 ** 6
INITIAL_K_MUT = 1.0
K_MUT_INCREASE = 0.0001
MUT_POS_LEARNING_RATE = 1.001


def main(options):
    """
    Simplest GA main function.
    """
    target = options.target
    n_polygons = options.n_polygons
    pos_p_mut_changes = options.p_position

    min_save_dt = 0.5
    print('drawing {} with {} polygons'.format(options.target, n_polygons))

    def save_progress():
        print('Save image...',)
        dst = os.path.join(
            evaluator.target_dst_dir,
            '{name}_i{i}-t{t}-mse{mse:.4f}.png'.format(
                name=os.path.basename(target), i=iteration, t=n_polygons, mse=father_evaluation
            )
        )
        best_image.save(dst)
        stats_filepath = os.path.join(evaluator.target_dst_dir, 'p{}.txt'.format(n_polygons))
        with open(stats_filepath, 'a') as fp:
            fp.write('{it}; {ev}; {delta}; {fails}\n'.format(
                it=iteration, ev=round(father_evaluation, 4), delta=delta_evaluation, fails=failed_iterations
                )
            )
        # Save mutations
        mutations_dst = os.path.join(evaluator.target_dst_dir, 'p{}-mut.txt'.format(n_polygons))
        with open(mutations_dst, 'w') as fp:
            fp.write('Genome length: {}\n'.format(polygons_encoder.genome_size))
            g_mut = sum(good_mutation_counter.values())
            b_mut = sum(bad_mutation_counter.values())
            fp.write('Positive mutations: {:,}\n'.format(g_mut))
            fp.write('Negative mutations: {:,}\n'.format(b_mut))
            fp.write('Success rate: {:.4%}\n\n'.format(g_mut / b_mut))
            for position in range(polygons_encoder.genome_size):
                fp.write('{:<5}: {}\n'.format(
                    position,
                    good_mutation_counter.get(position, 0) * '+' + bad_mutation_counter.get(position, 0) * '-' + \
                        ' {:.6f}'.format(p_mutations[position])
                    )
                )
            fp.write('\nsum(p) = {:.2f}\n'.format(sum(p_mutations)))
        print('saved {} and {}'.format(dst, stats_filepath))

        print('Bad mutation overhead: {:.4f} s'.format(t_sk_tot))
        t_ev_mean = t_ev_tot / n_evaluations
        t_ev_avoided = t_ev_mean * n_skipped_evaluations
        print('{} skipped evaluation {:.4f} s'.format(n_skipped_evaluations, t_ev_avoided))
        print('Time saved           : {:.2f} m'.format((t_ev_avoided - t_sk_tot) / 60))

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

    father = polygons_encoder.generate()
    father_im_recipe = polygons_encoder.decode(father)
    father_phenotype = draw_polygons(image_size, father_im_recipe['polygons'],
        background_color=father_im_recipe['background'],
        target_image_mode=options.image_mode)
    father_evaluation = evaluator.evaluate(father_phenotype)
    best_image = father_phenotype

    # Mutations
    k_mut = INITIAL_K_MUT
    p_mutations = [k_mut / genome_size] * genome_size
    good_mutation_counter = Counter()
    bad_mutation_counter = Counter()
    bad_mutations = set()

    # Stats
    n_evaluations = n_skipped_evaluations = 0
    t_sk_tot = t_ev_tot = 0
    failed_iterations = 0
    last_saved_ev = father_evaluation

    t0 = time.time()
    last_saved_t = t0
    iteration = 0

    while father_evaluation:
        iteration += 1
        if iteration == options.iterations:
            break

        # frozenset is to cache bad mutations
        if pos_p_mut_changes:
            mut_positions = frozenset(slow_rand_weighted_mut_positions(genome_size, p_mutations))
        else:
            mut_positions = frozenset(get_rand_positions(genome_size, k_mut / genome_size))

        # Check bad mutations
        t_sk_ev_0 = time.time()
        if len(mut_positions) < 3:
            if mut_positions in bad_mutations:
                n_skipped_evaluations += 1
                t_sk_tot += time.time() - t_sk_ev_0
                continue
            t_sk_tot += time.time() - t_sk_ev_0

        # Evaluation (mutation, phenotype and evaluation)
        t_ev_0 = time.time()
        child = flip_mutate(mut_positions, father)
        child_im_recipe = polygons_encoder.decode(child)
        child_phenotype = draw_polygons(image_size, child_im_recipe['polygons'],
            background_color=child_im_recipe['background'],
            target_image_mode=options.image_mode)
        child_evaluation = evaluator.evaluate(child_phenotype)
        n_evaluations += 1
        t_ev_tot += time.time() - t_ev_0

        if child_evaluation < father_evaluation:
            # IMPROVEMENT
            tt = time.time()
            delta_evaluation = father_evaluation - child_evaluation
            best_image = child_phenotype
            father_evaluation = child_evaluation
            father = child

            if pos_p_mut_changes:
                for pos in mut_positions:
                    new_p = min(p_mutations[pos] * MUT_POS_LEARNING_RATE, 1.0)
                    delta = new_p - p_mutations[pos]
                    p_mutations[pos] = new_p
                    p_mutations[-pos] -= delta
                    if pos < genome_size - 1:
                        p_mutations[pos + 1] += delta
                        p_mutations[randrange(genome_size)] -= delta
                    if pos > 0:
                        p_mutations[pos - 1] += delta
                        p_mutations[randrange(genome_size)] -= delta

            bad_mutations = set()
            good_mutation_counter.update(mut_positions)
            et = tt - t0
            speed = '{:.3f} it/s'.format(iteration / et)
            print('Success: {ev:,} - {np} polygons - {it:,} it/{t:.1f}m ({v})'.format(
                it=iteration, ev=child_evaluation, np=len(child_im_recipe['polygons']),
                t=et / 60, v=speed))
            dt = tt - last_saved_t
            delta_saved_ev = last_saved_ev - child_evaluation
            if dt > min_save_dt and delta_saved_ev >= VISIBLE_DELTA_EV:

                save_progress()

                last_saved_t = time.time()
                last_saved_ev = child_evaluation
                if dt < MIN_SAVE_DT:
                    min_save_dt = min_save_dt * 2
                print('Next saving after {:.1f} s'.format(min_save_dt))
        else:
            k_mut += K_MUT_INCREASE
            k_mut = min(k_mut, genome_size / 2)

            if pos_p_mut_changes:
                # Modifica la probabilita' di mutazione delle singole posizioni
                for pos in mut_positions:
                    new_p = p_mutations[pos] / MUT_POS_LEARNING_RATE
                    delta = p_mutations[pos] - new_p
                    p_mutations[pos] -= delta
                    p_mutations[-pos] += delta

            failed_iterations += 1
            if len(mut_positions) < 3:
                bad_mutations.add(mut_positions)
            bad_mutation_counter.update(mut_positions)

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
        impl_name + version + '-' + os.path.basename(drawer__file__)
    )
    with open('{}.bench.txt'.format(filename), 'a') as fp:
        fp.write('{}; {}; {}\n'.format(father_phenotype.size, father_phenotype.mode, speed))
    print(drawer__file__)
    print('{:,} iterations in {:.2f} s'.format(iteration, et))
    print(speed)


def get_options():
    parser = argparse.ArgumentParser()
    parser.add_argument('target', help='target image path')
    parser.add_argument('-p', '--n-polygons', type=int, default=64,
        help='number of polygons to use')
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
