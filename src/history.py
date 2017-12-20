"""
Encapsulate disk history handling.
"""
import datetime
import os
import pickle
import shutil
import time
from copy import deepcopy
from hashlib import sha1
from pprint import pformat

p_join = os.path.join

DATA_FILENAME = 'status.pkl'
STATS_FILENAME = 'stats.csv'
GNUPLOT_FILENAME = 'plot'
PLOT_FILENAME = 'plot.png'


def _get_id(options):
    """
    Obtain an id based on the option dictionary.
    """
    history_id = sha1(str(options.__dict__).encode()).hexdigest()[:7]
    return history_id


def _get_history_dirpath(options, history_id):
    target = options.target
    target_name = os.path.splitext(os.path.basename(target))[0]
    history_dirname = 'history_' + history_id
    history_dirpath = p_join(os.path.dirname(target), target_name, history_dirname)
    return history_dirpath


def get_cleared_options(options):
    cleared_options = deepcopy(options)
    del cleared_options.restart
    return cleared_options


class HistoryIO:
    """
    Handle evolution history persistency and resume.
    """
    def __init__(self, options):
        self.options = options
        self.cleared_options = get_cleared_options(options)
        self.id = _get_id(self.cleared_options)
        self.dirpath = _get_history_dirpath(options, self.id)
        self.filepath = self._path(DATA_FILENAME)
        self.opt_txt_fp = self._path('options.txt')
        self.stats_filepath = self._path('stats.csv')
        self.gnuplot_script_path = self._path(GNUPLOT_FILENAME)
        self.plot_path = self._path(PLOT_FILENAME)
        self.status = {}

    def _path(self, *args):
        return p_join(self.dirpath, *args)

    def init(self):
        if os.path.exists(self.dirpath):
            print('Erasing {}...'.format(self.dirpath))
            for i in range(10, 0, -1):
                print('{}...'.format(i))
                time.sleep(1)
            shutil.rmtree(self.dirpath, ignore_errors=True)

        print('Creating', self.dirpath)
        os.makedirs(self.dirpath)

        shutil.copy(self.options.target, self.dirpath)
        # Store also the options dictioray as human reference
        with open(self.opt_txt_fp, 'w') as fp:
            fp.write(pformat(self.cleared_options.__dict__))

    def exists(self):
        rv = os.path.exists(self.filepath)
        if rv:
            print(self.dirpath, 'exists')
        else:
            print(self.dirpath, 'does NOT exist')
        return rv

    def resume(self):
        with open(self.filepath, 'rb') as fp:
            status = pickle.load(fp)
        self._check_options()
        return status

    def _check_options(self):
        """
        Check that txt saved options matches with __init__ options argument.
        """
        txt = open(self.opt_txt_fp).read()
        assert self.cleared_options.__dict__ == eval(txt)

    def save_island_best_image(self, island):
        iteration = island.iteration
        target = island.evaluator.target_filepath
        ev = island.best_evaluation
        now = datetime.datetime.now()
        dirpath = p_join(self.dirpath, island.id)
        os.makedirs(dirpath, exist_ok=True)
        dst = p_join(
            dirpath,
            '{name}_t{t}_i{i}-mse{mse:.3f}.png'.format(
                name=os.path.basename(target),
                t=now.strftime('%Y%m%d%H%M%S'),
                i=iteration,
                mse=ev,
            )
        )
        island.best['phenotype'].save(dst)
        return dst

    def save(self, status):
        with open(self.filepath, 'wb') as fp:
            pickle.dump(status, fp)

    def init_stats(self, status, plot=False):
        islands = status['islands']
        row = ['iteration', 'best crossover'] + ['is_' + isla.short_id for isla in islands]
        self.write_stats_row('w', row)

        if plot:
            self.init_plot(status)

    def init_plot(self, status):
        islands = status['islands']
        script_lines = [
            'set terminal png',
            "set output '{png}'".format(png=self.plot_path),
        ]
        islands_lines = []
        islands_lines.append(
            "plot '{csv}' using 1:2 title 'cross' with linespoints".format(csv=self.stats_filepath)
        )
        islands_lines.extend([
            "'{}' using 1:{} title 'is-{}' with linespoints".format(
                self.stats_filepath, i + 3, islands[i].short_id) for i in range(len(islands))
        ])
        script = '\n'.join(script_lines) + '\n' + ', \\\n'.join(islands_lines)
        with open(self.gnuplot_script_path, 'w') as fp:
            fp.write(script)

    def update_stats(self, status, plot=False):
        islands = status['islands']
        offspring_ev = status['best_ev_offspring']['evaluation']
        row = [islands[0].iteration, offspring_ev] + [isla.best_evaluation for isla in islands]
        self.write_stats_row('a', row)

        if plot:
            self.update_plot()

    def update_plot(self):
        os.system("gnuplot '{}'".format(self.gnuplot_script_path))

    def write_stats_row(self, mode, row):
        row_string = '    '.join(['{:>13}'.format(cell) for cell in row])
        with open(self.stats_filepath, mode) as fp:
            fp.write(row_string + '\n')
