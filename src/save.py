import datetime
import os


def save_progress(island, options):
    n_polygons = options.n_polygons
    iteration = island.iteration
    target = island.evaluator.target_filepath
    target_dst_dir = island.evaluator.target_dst_dir
    ev = island.best_evaluation

    now = datetime.datetime.now()
    dirpath = os.path.join(target_dst_dir, island.id)
    os.makedirs(dirpath, exist_ok=True)
    dst = os.path.join(
        dirpath,
        '{name}_p{p}_t{t}_i{i}-mse{mse:.3f}.png'.format(
            name=os.path.basename(target),
            t=now.strftime('%Y%m%d%H%M%S'),
            i=iteration,
            p=n_polygons,
            mse=ev,
        )
    )
    island.best['phenotype'].save(dst)


def save_mutations(evaluator, good_mutation_counter, bad_mutation_counter):
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


def bench():
    speed = '{:.3f} it/s'.format(iteration / et)
    print('Success: {ev:,} - {np} polygons - {it:,} it/{t:.1f}m ({v})'.format(
        it=iteration, ev=child_evaluation, np=len(child_im_recipe['polygons']),
        t=et / 60, v=speed))
    delta_saved_ev = last_saved_ev - child_evaluation
    if dt > min_save_dt and delta_saved_ev >= VISIBLE_DELTA_EV:

        save_progress()

        last_saved_t = time.time()
        last_saved_ev = child_evaluation
        if dt < MIN_SAVE_DT:
            min_save_dt = min_save_dt * 2
        print('Next saving after {:.1f} s'.format(min_save_dt))

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
