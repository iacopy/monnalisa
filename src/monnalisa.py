"""
Disegna a caso.

* isole
* multiprocessing
"""
import os
import time
from functools import partial
from multiprocessing import Pool, cpu_count

import cli
from drawer import ShapesEncoder
from evaluator import ImageEvaluator, func_evaluate
from genome import genetic_distances
from history import HistoryIO
from island import Island
from mating import mate

p_join = os.path.join

BASES = '01'


def worker(isola):
    """Just call Island.run() and return Island instance itself."""
    isola.run()
    return isola


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
    processes = options.processes
    if not processes:
        processes = min(len(islands), cpu_count())
    print('Running across {} process{}'.format(processes, (processes > 1) * 'es'))

    t_0 = time.time()
    total_session_iterations = 0
    while True:
        # =============================================
        # ------------------ ISLANDS ------------------
        # =============================================

        i_t0 = time.time()

        with Pool(processes=processes) as pool:
            islands = pool.map(worker, islands)

        for i_isla, isla in enumerate(islands):
            delta = isla.run_delta_evaluation
            print('i = {i}, it = {it:,}, v = {ev:,} ({d:,})'.format(
                i=i_isla, it=isla.iteration, ev=isla.best['evaluation'], d=delta))

            if delta < 0:
                isla_best_dst = p_join(history_io.dirpath, 'best-island-{}-{}.png'.format(i_isla, isla.id[:7]))
                isla.best['phenotype'].save(isla_best_dst)

        i_elapsed = time.time() - i_t0
        speed = (options.crossover_freq * len(islands)) / i_elapsed
        print('Islands speed: {:.3f} it/s'.format(speed))

        islands_best_ev = [isla.best_evaluation for isla in islands]
        islands_genomes = [isla.best['genome'] for isla in islands]
        gen_diffs = genetic_distances(*islands_genomes)
        print('Variab gen (mean) = {:.3f}'.format(sum(gen_diffs) / len(islands)))

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
