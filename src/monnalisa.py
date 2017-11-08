from __future__ import division
from collections import Counter
from drawer import PolygonsEncoder
from drawer import ImageEvaluator
from drawer import draw_polygons
from genome import flip_mutate
from genome import rand_positions
from drawer import __file__ as drawer__file__
import sys
import time
import os


BASES = '01'
N_POLYGONS = 5
STOP = 200000
SAVE_INTERVAL = STOP / 10
MIN_SAVE_DT = 60
VISIBLE_DELTA_EV = 10 ** 6


def main(target, n_polygons, min_sides=3, max_sides=4, image_mode='RGB'):
    """
    Simplest GA main function.
    """
    min_save_dt = 0.5
    print('drawing {} with {} polygons'.format(target, n_polygons))

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
        mutations_dst = os.path.join(evaluator.target_dst_dir, 'p{}-mut+.txt'.format(n_polygons))
        with open(mutations_dst, 'w') as fp:
            fp.write('Genome length: {}\n'.format(polygons_encoder.genome_size))
            g_mut = sum(good_mutation_counter.values())
            b_mut = sum(bad_mutation_counter.values())
            fp.write('Positive mutations: {:,}\n\n'.format(g_mut))
            fp.write('Negative mutations: {:,}\n\n'.format(b_mut))
            fp.write('Success rate: {:.4%}\n\n'.format(g_mut / b_mut))
            for position in range(polygons_encoder.genome_size):
                fp.write('{:<5}: {}\n'.format(
                    position,
                    good_mutation_counter.get(position, 0) * '+' + bad_mutation_counter.get(position, 0) * '-'
                    )
                )
        print('saved {} and {}'.format(dst, stats_filepath))

        print('Bad mutation overhead: {:.4f} s'.format(t_sk_tot))
        t_ev_mean = t_ev_tot / n_evaluations
        t_ev_avoided = t_ev_mean * n_skipped_evaluations
        print('{} skipped evaluation {:.4f} s'.format(n_skipped_evaluations, t_ev_avoided))
        print('Time saved           : {:.2f} m'.format((t_ev_avoided - t_sk_tot) / 60))

    print('target: {}'.format(repr(target)))
    print('n_polygons: {}'.format(n_polygons))
    n_total_sides = n_polygons * max_sides
    print('n_total_sides: {}'.format(n_total_sides))

    evaluator = ImageEvaluator(target)
    image_size = evaluator.target_size
    polygons_encoder = PolygonsEncoder(
        image_size, n_total_sides, min_sides=min_sides, max_sides=max_sides)
    genome_size = polygons_encoder.genome_size
    father = polygons_encoder.generate()
    father_im_recipe = polygons_encoder.decode(father)
    father_phenotype = draw_polygons(image_size, father_im_recipe['polygons'],
        background_color=father_im_recipe['background'], image_mode=image_mode)
    father_evaluation = evaluator.evaluate(father_phenotype)
    best_image = father_phenotype

    iteration = 0
    n_evaluations = n_skipped_evaluations = 0
    t_sk_tot = t_ev_tot = 0
    failed_iterations = 0
    good_mutation_counter = Counter()
    bad_mutation_counter = Counter()
    bad_mutations = set()
    t0 = time.time()
    last_saved_t = t0
    last_saved_ev = father_evaluation
    while father_evaluation:
        iteration += 1
        if iteration == STOP:
            break

        # frozenset is to cache bad mutations
        mut_positions = frozenset(rand_positions(genome_size, 1.0 / genome_size))

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
            background_color=child_im_recipe['background'], image_mode=image_mode)
        child_evaluation = evaluator.evaluate(child_phenotype)
        n_evaluations += 1
        t_ev_tot += time.time() - t_ev_0

        if child_evaluation < father_evaluation:
            tt = time.time()
            best_image = child_phenotype
            father_evaluation = child_evaluation
            father = child

            bad_mutations = set()
            good_mutation_counter.update(mut_positions)
            delta_evaluation = father_evaluation - child_evaluation
            delta_saved_ev = last_saved_ev - child_evaluation
            et = tt - t0
            speed = '{:.3f} it/s'.format(iteration / et)
            print('Success: {ev:,} - {it:,}it/{t:.1f}m ({v})'.format(
                it=iteration, ev=child_evaluation, t=et / 60, v=speed))
            dt = tt - last_saved_t
            if dt > min_save_dt and delta_saved_ev >= VISIBLE_DELTA_EV:

                save_progress()

                last_saved_t = time.time()
                last_saved_ev = child_evaluation
                if dt < MIN_SAVE_DT:
                    min_save_dt = min_save_dt * 2
                print('Next saving after {:.1f} s'.format(min_save_dt))
        else:
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


if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) == 2:
        target, n_polygons = args
    elif len(args) == 1:
        target, n_polygons = args[0], N_POLYGONS
    elif len(args) == 0:
        target, n_polygons = 'images/monnalisa.png', N_POLYGONS
    print('n_polygons =', n_polygons)
    main(target, int(n_polygons))
