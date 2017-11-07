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
N_TRIANGLES = 5
STOP = 1000000
SAVE_INTERVAL = STOP / 10
MIN_SAVE_DT = 10


def main(target, n_polygons, image_mode='RGB'):
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
            fp.write('Mutated positions: {}\n\n'.format(len(good_mutations)))
            for position, hits in sorted(good_mutations.items()):
                fp.write('{:<5}: {}\n'.format(position, hits * '='))
        print('saved {} and {}'.format(dst, stats_filepath))

    print('target: {}'.format(repr(target)))
    print('n_polygons: {}'.format(n_polygons))
    n_total_sides = n_polygons * 3
    print('n_total_sides: {}'.format(n_total_sides))

    evaluator = ImageEvaluator(target)
    image_size = evaluator.target_size
    polygons_encoder = PolygonsEncoder(
        image_size, n_total_sides, min_sides=3, max_sides=4)
    genome_size = polygons_encoder.genome_size
    father = polygons_encoder.generate()
    father_im_recipe = polygons_encoder.decode(father)
    father_phenotype = draw_polygons(image_size, father_im_recipe['polygons'],
        background_color=father_im_recipe['background'], image_mode=image_mode)
    father_evaluation = evaluator.evaluate(father_phenotype)
    best_image = father_phenotype

    iteration = 0
    failed_iterations = 0
    good_mutations = Counter()
    t0 = time.time()
    last_saved = t0
    while father_evaluation:
        iteration += 1
        if iteration == STOP:
            break

        mut_positions = rand_positions(genome_size, 1.0 / genome_size)
        child = flip_mutate(mut_positions, father)
        child_im_recipe = polygons_encoder.decode(child)
        child_phenotype = draw_polygons(image_size, child_im_recipe['polygons'],
            background_color=child_im_recipe['background'], image_mode=image_mode)
        child_evaluation = evaluator.evaluate(child_phenotype)
        if child_evaluation < father_evaluation:
            good_mutations.update(mut_positions)
            delta_evaluation = father_evaluation - child_evaluation
            best_image = child_phenotype
            father_evaluation = child_evaluation
            father = child

            tt = time.time()
            speed = '{:.3f} it/s'.format(iteration / (tt - t0))
            print('success at {:,}: {:.4f} - {}'.format(iteration, child_evaluation, speed))
            dt = tt - last_saved
            if dt > min_save_dt:

                save_progress()

                last_saved = time.time()
                if dt < MIN_SAVE_DT:
                    min_save_dt = min_save_dt * 2
                else:
                    min_save_dt = min_save_dt / 2
        else:
            failed_iterations += 1

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

    main(target, int(n_polygons))
