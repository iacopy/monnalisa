import argparse
import os
import sys

STOP = 10 ** 6


def get_options():
    """
    Parse arguments from command line.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('target', help='target image path')
    parser.add_argument('--resize', type=int, default=128,
        help='resize target image smaller while keeping aspect ratio [default: %(default)s]')
    parser.add_argument('-n', '--n-shapes', type=int, default=64,
        help='number of shapes to use [default: %(default)s]')
    parser.add_argument('-s', '--shape', default='t',
        help='shapes used to draw: t=triangle, q=quad, r=rect, c=circle, e=ellipse, l=line [default: %(default)s]')
    parser.add_argument('--symmetry', default='', help='Symmetry elements [default: %(default)s]')
    parser.add_argument('-i', '--n-islands', type=int, default=2,
        help='number of islands [default: %(default)s]')
    parser.add_argument('-c', '--crossover-freq', type=int, default=1000,
        help='number of separate islands iterations between crossover [default: %(default)s]')
    parser.add_argument('-o', '--n-crossovers', type=int, default=3,
        help='number of for crossover reproductions for each couple of partners [default: %(default)s]')
    parser.add_argument('--f1', type=int, default=64, help='f1 generation size')
    parser.add_argument('--f2', type=int, default=128, help='f2 generation size')
    parser.add_argument('-t', '--p-transposition-replicative', type=float, default=0.0,
        help='probability that a transposition was replicative (increasing genome length) [default: %(default)s]')
    parser.add_argument('--iterations', type=int, default=STOP,
        help='number of iterations [default: %(default)s]')
    parser.add_argument('-d', '--draw-image_mode', default='RGBA', help='[default: %(default)s]')
    parser.add_argument('-m', '--target-image_mode', default='RGB', help='[default: %(default)s]')
    parser.add_argument('--p-position', action='store_true',
        help='enable single position probability mutations (experimental)')
    parser.add_argument('--restart', default=False, action='store_true',
        help='do not resume existing history, but *erase* it and restart [default=%(default)s]')
    parser.add_argument('-p', '--processes', type=int, default=0,
        help='number of processes in which islands runs are distributed (0 = auto) [default=%(default)s]')

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
