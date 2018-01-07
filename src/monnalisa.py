"""
Disegna a caso.

* isole
* multiprocessing
"""
import os
import time
from collections import Counter
from functools import partial
from multiprocessing import Pool, cpu_count

import cli
from drawer import ShapesEncoder
from evaluator import ImageEvaluator, func_evaluate
from genome import genetic_distances
from history import HistoryIO
from island import Island
from mating import mate
from utils import AccumulativeMean

p_join = os.path.join

BASES = '01'


def worker(isola):
    """Just call Island.run() and return Island instance itself."""
    isola.run()
    return isola


def parallelislands(islands, processes):
    """
    Run `islands` across `processes` processes.
    """
    i_t0 = time.time()
    if processes == 1:
        # Don't use Pool
        islands = [worker(isola) for isola in islands]
    else:
        with Pool(processes=processes) as pool:
            islands = pool.map(worker, islands)
    i_elapsed = time.time() - i_t0
    iterations = sum([isola.run_iterations for isola in islands])
    run_speed = iterations / i_elapsed
    print('Islands run_speed: {:.3f} it/s'.format(run_speed))
    return islands, i_elapsed


def optimize_processes(processes, time_per_processes, count_threshold, max_processes):
    """Return number of processes based on `time_per_processes` means.

    :param count_threshold: how many time values to collect for means
    """
    completed = True
    for p_accmean in reversed(time_per_processes.most_common()):
        print(p_accmean)
        if p_accmean[1].count < count_threshold:
            completed = False
    if completed:
        processes = time_per_processes.most_common()[-1][0]
    else:
        processes = processes + 1 if processes < max_processes else 1
    return processes


def main(options):
    """
    Simplest GA main function.
    """
    import pprint
    pprint.pprint(options.__dict__)
    n_shapes = options.n_shapes
    print('target: {}'.format(repr(options.target)))
    print('drawing {} with {} polygons'.format(options.target, n_shapes))

    im_eval = ImageEvaluator(options.target, dst_image_mode=options.target_image_mode, resize=options.resize)
    image_size = im_eval.target_size

    shapes_encoder = ShapesEncoder(
        image_size=image_size,
        image_mode=options.target_image_mode,
        draw_image_mode=options.draw_image_mode,
        shape=options.shape,
        n_shapes=n_shapes,
        symmetry=options.symmetry,
    )
    print('Genome length: {:,}'.format(shapes_encoder.genome_size))
    evaluate = partial(func_evaluate, shapes_encoder, im_eval)

    islands = tuple([Island(shapes_encoder, im_eval, run_iterations=options.crossover_freq) for _ in range(options.n_islands)])
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

    print('{} islands: {}'.format(len(islands), islands))

    # Deciding number of processes to run islands
    max_processes = max(len(islands) * 2, cpu_count() * 2)
    count_threshold = 3
    processes = options.processes
    time_per_processes = Counter()
    for n in range(1, max_processes + 1):
        time_per_processes[n] = AccumulativeMean(round_digits=1)

    t_0 = time.time()
    total_session_iterations = 0
    while True:
        processes = options.processes if options.processes else \
            optimize_processes(processes, time_per_processes, count_threshold, max_processes)
        print('Running {i} island{s} across {p} process{es}'.format(
            i=len(islands), s=(len(islands) > 1) * 's', p=processes, es=(processes > 1) * 'es')
        )
        # =============================================
        # ------------------ ISLANDS ------------------
        # =============================================
        islands, run_speed = parallelislands(islands, processes)
        time_per_processes[processes] += run_speed

        for i_isla, isla in enumerate(islands):
            delta = isla.run_delta_evaluation
            print('i = {i}, it = {it:,}, v = {ev:,} ({d:,})'.format(
                i=i_isla, it=isla.iteration, ev=isla.best['evaluation'], d=delta))

            if delta < 0:
                isla_best_dst = p_join(history_io.dirpath, 'best-island-{}-{}.png'.format(i_isla, isla.id[:7]))
                isla.best['phenotype'].save(isla_best_dst)

        islands_best_ev = [isla.best_evaluation for isla in islands]
        islands_genomes = [isla.best['genome'] for isla in islands]
        gen_diffs = genetic_distances(*islands_genomes)
        print('Variab gen (mean) = {:.3f}'.format(sum(gen_diffs) / len(islands)))

        # =============================================
        # ---------------- CROSSOVER ------------------
        # =============================================
        new_best_ev_offspring = mate(
            islands, best_ev_offspring, evaluate,
            f1_size=options.f1,
            f2_size=options.f2,
            n_crossovers=options.n_crossovers,
        )
        if new_best_ev_offspring:
            print('New best crossover! ev = {:,}'.format(new_best_ev_offspring['evaluation']))
            new_best_ev_offspring['phenotype'].save(p_join(history_io.dirpath, 'best-crossover.png'))
            best_ev_offspring = new_best_ev_offspring

        if best_ev_offspring['evaluation'] < min(islands_best_ev):
            print('crossover is currently the best: {:,}'.format(best_ev_offspring['evaluation']))
        co_genome = best_ev_offspring['genome']

        shapes_encoder.draw_as_svg(co_genome, p_join(history_io.dirpath, 'best-crossover.svg'))

        genetic_dist = [genetic_distances(co_genome, g)[0] for g in islands_genomes]
        for i_isla, distance in enumerate(genetic_dist):
            print('distance best-crossover vs island {}: {:.3f}'.format(i_isla, distance))

        status = {'islands': islands, 'best_ev_offspring': best_ev_offspring}
        history_io.save(status)
        history_io.update_stats(status, plot=True)
        history_io.update_genomes_stuff(status, save_good_mutations=True)

        elapsed = time.time() - t_0
        total_session_iterations += (options.crossover_freq * len(islands))
        speed = total_session_iterations / elapsed
        print('Session mean speed: {:.2f} it/s'.format(speed))


if __name__ == '__main__':
    opts = cli.get_options()
    main(opts)
