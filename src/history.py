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
        self.filepath = p_join(self.dirpath, DATA_FILENAME)
        self.opt_txt_fp = p_join(self.dirpath, 'options.txt')
        self.status = {}

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
