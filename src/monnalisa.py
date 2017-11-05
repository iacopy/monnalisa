from __future__ import division
from drawer import TrianglesEncoder
from drawer import ImageEvaluator
from drawer import draw_triangles
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


def main(target, n_triangles):
    """
    Simplest GA main function.
    """
    min_save_dt = 0.5

    def save_image(image):
        print('Save image...',)
        dst = os.path.join(
            evaluator.target_dst_dir,
            '{name}_i{i}-t{t}-mse{mse:.4f}.png'.format(
                name=os.path.basename(target), i=iteration, t=n_triangles, mse=father_evaluation
            )
        )
        image.save(dst)
        print('saved', dst)

    print('target: {}'.format(repr(target)))
    print('n_triangles: {}'.format(repr(n_triangles)))

    evaluator = ImageEvaluator(target)
    image_size = evaluator.target_size
    triangles_encoder = TrianglesEncoder(image_size, n_triangles)
    genome_size = triangles_encoder.genome_size
    father = triangles_encoder.generate()
    father_triangles = triangles_encoder.decode(father)
    father_phenotype = draw_triangles(image_size, father_triangles)
    father_evaluation = evaluator.evaluate(father_phenotype)
    best_image = father_phenotype

    iteration = 0
    t0 = time.time()
    last_saved = t0
    while father_evaluation:
        iteration += 1
        if iteration == STOP:
            break

        mut_positions = rand_positions(genome_size, 1.0 / genome_size)
        child = flip_mutate(mut_positions, father)
        child_triangles = triangles_encoder.decode(child)
        child_phenotype = draw_triangles(image_size, child_triangles)
        child_evaluation = evaluator.evaluate(child_phenotype)
        if child_evaluation < father_evaluation:
            print('success at {:,}'.format(iteration))
            print(child, child_phenotype, round(child_evaluation, 4))
            best_image = child_phenotype
            father_evaluation = child_evaluation
            father = child

            tt = time.time()
            speed = '{:.3f} it/s'.format(iteration / (tt - t0))
            print(speed)
            dt = tt - last_saved
            if dt > min_save_dt:
                save_image(best_image)
                last_saved = time.time()
                if dt < MIN_SAVE_DT:
                    min_save_dt = min_save_dt * 2
                else:
                    min_save_dt = min_save_dt / 2

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
        fp.write(speed + '\n')
    print(drawer__file__)
    print('{:,} iterations in {:.2f} s'.format(iteration, et))
    print(speed)


if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) == 2:
        target, n_triangles = args
    elif len(args) == 1:
        target, n_triangles = args[0], N_TRIANGLES
    elif len(args) == 0:
        target, n_triangles = 'images/monnalisa.png', N_TRIANGLES

    main(target, int(n_triangles))
