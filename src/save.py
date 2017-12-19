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
    return dst
