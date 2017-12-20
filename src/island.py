import time
from collections import Counter
from functools import partial
from hashlib import md5

from evaluator import func_evaluate
from genome import flip_mutate, get_rand_positions


class Island:
    counter = 0

    def __init__(self, polygons_encoder, evaluator, k_mut=1.0):
        self.polygons_encoder = polygons_encoder
        self.evaluator = evaluator
        self.evaluate = partial(func_evaluate, polygons_encoder, evaluator)

        # Mutations
        self.k_mut = k_mut
        genome_size = self.polygons_encoder.genome_size
        self.p_mutations = [self.k_mut / genome_size] * genome_size
        self.good_mutation_counter = Counter()
        self.bad_mutation_counter = Counter()

        # Stats
        self.iteration = 0
        self.t_saved = 0

        genome = self.polygons_encoder.generate()
        self.best = self.evaluate(genome)
        self.adam = genome
        self.id = md5(genome.encode()).hexdigest()
        self.short_id = self.id[:7]

    @property
    def best_evaluation(self):
        return self.best['evaluation']

    def fitness_improved(self, mut_positions, *args, **kwargs):
        # update good mutations
        self.good_mutation_counter.update(mut_positions)

    def fitness_fail(self, mut_positions, *args, **kwargs):
        pass

    def set_best(self, best):
        self.best = best

    def run(self, iterations=100000):
        evaluate = self.evaluate
        genome_size = self.polygons_encoder.genome_size
        mut_rate = self.k_mut / genome_size
        start_iteration = self.iteration

        father_evaluation = self.best['evaluation']
        father_genome = self.best['genome']
        starting_evaluation = father_evaluation

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
            mut_positions = frozenset(get_rand_positions(genome_size, mut_rate))

            # Check cached bad mutations
            t_sk_ev_0 = time.time()
            if len(mut_positions) < 3:
                if mut_positions in bad_mutations:
                    n_skipped_evaluations += 1
                    t_sk_tot += time.time() - t_sk_ev_0
                    continue
                t_sk_tot += time.time() - t_sk_ev_0

            # Evaluation (mutation, phenotype and evaluation)
            t_ev_0 = time.time()
            child_genome = flip_mutate(mut_positions, father_genome)
            child_rv = evaluate(child_genome)
            child_evaluation = child_rv['evaluation']
            n_evaluations += 1
            t_ev_tot += time.time() - t_ev_0

            if child_evaluation < father_evaluation:
                self.fitness_improved(mut_positions, father_evaluation, child_evaluation)

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

        t_ev_mean = t_ev_tot / n_evaluations
        t_ev_avoided = t_ev_mean * n_skipped_evaluations
        self.t_saved = t_ev_avoided - t_sk_tot

        # Return delta evaluation from run start
        return father_evaluation - starting_evaluation
