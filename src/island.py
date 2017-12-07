from collections import Counter
from collections import namedtuple
from hashlib import md5

from genome import genetic_diff
from genome import slow_rand_weighted_mut_positions
from genome import get_rand_positions
from genome import flip_mutate
from drawer import evaluate
import time


INITIAL_K_MUT = 'initial_k_mut'
K_MUT_INCREASE = 'k_mut_increase'
MUT_POS_LEARNING_RATE = 'mut_pos_learning_rate'
POS_MUT_P_CHANGES = 'positive_mutations_prob_changes'

DEFAULT_MUT_SETTINGS = {
    POS_MUT_P_CHANGES: False,
    INITIAL_K_MUT: 1.0,
    K_MUT_INCREASE: 0.0001,
    MUT_POS_LEARNING_RATE: 1.001,
}


def enhance_p_mutations(p_mutations, mut_positions):
    for pos in mut_positions:
        new_p = min(p_mutations[pos] * MUT_POS_LEARNING_RATE, 1.0)
        delta = new_p - p_mutations[pos]
        p_mutations[pos] = new_p
        p_mutations[-pos] -= delta
        if pos < genome_size - 1:
            p_mutations[pos + 1] += delta
            p_mutations[randrange(genome_size)] -= delta
        if pos > 0:
            p_mutations[pos - 1] += delta
            p_mutations[randrange(genome_size)] -= delta


def reduce_p_mutations(p_mutations, mut_positions):
    # Modifica la probabilita' di mutazione delle singole posizioni
    for pos in mut_positions:
        new_p = p_mutations[pos] / MUT_POS_LEARNING_RATE
        delta = p_mutations[pos] - new_p
        p_mutations[pos] -= delta
        p_mutations[-pos] += delta


class Island:
    counter = 0

    def __init__(self, polygons_encoder, evaluator, mut_settings=DEFAULT_MUT_SETTINGS):
        self.polygons_encoder = polygons_encoder
        self.evaluator = evaluator
        self.mut_settings = mut_settings

        # Mutations
        self.k_mut = self.mut_settings[INITIAL_K_MUT]
        genome_size = self.polygons_encoder.genome_size
        self.p_mutations = [self.k_mut / genome_size] * genome_size
        self.good_mutation_counter = Counter()
        self.bad_mutation_counter = Counter()

        # Stats
        self.iteration = 0

        genome = self.polygons_encoder.generate()
        self.best = evaluate(polygons_encoder, evaluator, genome)
        self.adam = genome
        self.id = md5(genome.encode()).hexdigest()

    @property
    def status(self):
        return dict(
            iteration=self.iteration,
            best=self.best,
        )

    @property
    def best_evaluation(self):
        return self.best['evaluation']

    def fitness_improved(self, mut_positions, *args, **kwargs):
        # update good mutations
        self.good_mutation_counter.update(mut_positions)
        if self.mut_settings[POS_MUT_P_CHANGES]:
            enhance_p_mutations(self.p_mutations, mut_positions)

    def fitness_fail(self, mut_positions, *args, **kwargs):
        #self.k_mut += self.mut_settings[K_MUT_INCREASE]
        #self.k_mut = min(self.k_mut, self.genome_size / 2)

        if self.mut_settings[POS_MUT_P_CHANGES]:
            reduce_p_mutations(self.p_mutations, mut_positions)

    def set_best(self, best):
        self.best = best

    def run(self, iterations=100000):
        t0 = time.time()

        evaluator = self.evaluator
        polygons_encoder = self.polygons_encoder
        genome_size = self.polygons_encoder.genome_size

        k_mut = self.k_mut
        pos_mut_p_changes = self.mut_settings[POS_MUT_P_CHANGES]
        start_iteration = self.iteration

        father_evaluation = self.best['evaluation']
        father_genome = self.best['genome']

        # === Init local variables ===

        # cache stats
        n_evaluations = n_skipped_evaluations = 0
        t_sk_tot = t_ev_tot = 0
        failed_iterations = 0
        bad_mutations = set()

        while self.iteration - start_iteration < iterations:
            self.iteration += 1
            if (self.iteration - start_iteration) == iterations:
                break

            # Generate random mutation positions
            # frozenset is to cache bad mutations
            if pos_mut_p_changes:
                mut_positions = frozenset(slow_rand_weighted_mut_positions(genome_size, p_mutations))  ###
            else:
                mut_positions = frozenset(get_rand_positions(genome_size, k_mut / genome_size))

            # Check cached bad mutations
            t_sk_ev_0 = time.time()  ###
            if len(mut_positions) < 3:
                if mut_positions in bad_mutations:
                    n_skipped_evaluations += 1
                    t_sk_tot += time.time() - t_sk_ev_0
                    continue
                t_sk_tot += time.time() - t_sk_ev_0

            # Evaluation (mutation, phenotype and evaluation)
            t_ev_0 = time.time()
            child_genome = flip_mutate(mut_positions, father_genome)
            child_rv = evaluate(polygons_encoder, evaluator, child_genome)
            child_evaluation = child_rv['evaluation']
            n_evaluations += 1
            t_ev_tot += time.time() - t_ev_0

            if child_evaluation < father_evaluation:
                self.fitness_improved(mut_positions, father_evaluation, child_evaluation)

                # IMPROVEMENT
                tt = time.time()
                et = tt - t0

                self.set_best(child_rv)
                father_evaluation = child_evaluation
                father_genome = child_genome

                # reset bad mutations
                bad_mutations = set()
            else:
                failed_iterations += 1
                if len(mut_positions) < 3:
                    bad_mutations.add(mut_positions)
                self.bad_mutation_counter.update(mut_positions)

                self.fitness_fail(mut_positions, father_evaluation, child_evaluation)

        #bench()

        # print('Bad mutation overhead: {:.4f} s'.format(t_sk_tot))
        # t_ev_mean = t_ev_tot / n_evaluations
        # t_ev_avoided = t_ev_mean * n_skipped_evaluations
        # print('{} skipped evaluation {:.4f} s'.format(n_skipped_evaluations, t_ev_avoided))
        # print('Time saved           : {:.2f} m'.format((t_ev_avoided - t_sk_tot) / 60))

        # print(drawer__file__)
        # print('{:,} iterations in {:.2f} s'.format(iteration, et))
        # print(speed)
