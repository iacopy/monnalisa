import time
from collections import Counter
from functools import partial
from hashlib import md5
from random import choice, random, randrange

from evaluator import func_evaluate
from genome import flip_mutate, get_rand_positions
from transpose import transpose


class Island:
    counter = 0

    def __init__(self,
                 shapes_encoder,
                 evaluator,
                 genome=None,
                 run_iterations=1000,
                 k_mut=1.0,
                 p_transposition=0.5,
                 ):
        self.shapes_encoder = shapes_encoder
        self.evaluator = evaluator
        self.evaluate = partial(func_evaluate, shapes_encoder, evaluator)
        self.run_iterations = run_iterations

        # Mutations
        self.k_mut = k_mut
        genome_size = self.shapes_encoder.genome_size
        self.p_mutations = [self.k_mut / genome_size] * genome_size
        self.good_mutation_counter = Counter()
        self.bad_mutation_counter = Counter()
        self.p_transposition = p_transposition
        # Salva le mutazioni buone dell'ultimo ciclo di run
        self.last_run_good_mutations = []

        # Stats
        self.iteration = 0
        self.t_saved = 0

        genome = genome if genome else self.shapes_encoder.generate()
        assert len(genome) == genome_size, '{} != {}'.format(len(genome), genome_size)
        self.best = self.evaluate(genome)
        self.adam = genome
        self.id = md5(genome.encode()).hexdigest()
        self.short_id = self.id[:7]
        self.run_delta_evaluation = 0  # delta evaluation between run end and run start
        self.animation_frames = []

    @property
    def best_evaluation(self):
        return self.best['evaluation']

    def fitness_improved(self, mutation, *args, **kwargs):
        """Function called in case of fitness improvement."""
        # update good mutations
        self.last_run_good_mutations.append((self.iteration, mutation))
        if mutation[0] == 'flip':
            self.good_mutation_counter.update(mutation[1])

    def fitness_fail(self, mutation, *args, **kwargs):
        """Function called in case of fitness decreased."""
        pass

    def set_best(self, best):
        self.best = best

    def run(self):
        t_0 = time.time()

        self.last_run_good_mutations = []

        evaluate = self.evaluate
        genome_size = self.shapes_encoder.genome_size
        mut_rate = self.k_mut / genome_size
        start_iteration = self.iteration

        father_evaluation = self.best['evaluation']
        father_genome = self.best['genome']
        starting_evaluation = father_evaluation

        # === Init local variables ===
        # cache stats
        n_evaluations = n_skipped_evaluations = 0
        t_sk_tot = t_ev_tot = 0
        failed_iterations = successful_iterations = 0
        bad_mutations = set()
        while self.iteration - start_iteration < self.run_iterations:
            self.iteration += 1
            if (self.iteration - start_iteration) == self.run_iterations:
                break

            rand = random()
            if rand <= self.p_transposition:
                inverted = choice([True, False])
                if rand <= self.p_transposition / 2:
                    start, end, dst = sorted([randrange(genome_size), randrange(genome_size), randrange(genome_size)])
                else:
                    dst, start, end = sorted([randrange(genome_size), randrange(genome_size), randrange(genome_size)])
                transposing = list(father_genome)
                transpose(transposing, start, end, dst, replicative=False, inverted=inverted)
                child_genome = ''.join(transposing)
                mutation = ('T', (start, end, dst, False, inverted))
            else:
                # Generate random mutation positions
                # frozenset is to cache bad mutations
                mut_positions = frozenset(get_rand_positions(genome_size, mut_rate))
                mutation = ('F', tuple(mut_positions))

                # Check cached bad mutations
                t_sk_ev_0 = time.time()
                if len(mut_positions) < 3:
                    if mut_positions in bad_mutations:
                        n_skipped_evaluations += 1
                        t_sk_tot += time.time() - t_sk_ev_0
                        continue
                    t_sk_tot += time.time() - t_sk_ev_0

                child_genome = flip_mutate(mut_positions, father_genome)

            # Evaluation (mutation, phenotype and evaluation)
            t_ev_0 = time.time()
            child_rv = evaluate(child_genome)
            child_evaluation = child_rv['evaluation']
            n_evaluations += 1
            t_ev_tot += time.time() - t_ev_0

            if child_evaluation < father_evaluation:
                successful_iterations += 1
                self.fitness_improved(mutation, father_evaluation, child_evaluation)

                self.set_best(child_rv)
                father_evaluation = child_evaluation
                father_genome = child_genome

                # reset bad mutations
                bad_mutations = set()
            else:
                failed_iterations += 1
                if mutation[0] == 'F':
                    if len(mut_positions) < 3:
                        bad_mutations.add(mut_positions)
                    self.bad_mutation_counter.update(mut_positions)

                self.fitness_fail(mutation, father_evaluation, child_evaluation)

        t_ev_mean = t_ev_tot / n_evaluations
        t_ev_avoided = t_ev_mean * n_skipped_evaluations
        self.t_saved = t_ev_avoided - t_sk_tot

        self.run_delta_evaluation = father_evaluation - starting_evaluation

        t = time.time() - t_0
        print('Improvements/total = {:,}/{:,} ({:.01%})'.format(
            successful_iterations, self.run_iterations, successful_iterations / self.run_iterations))
        print('Island {} run: {:.2f} ({:.2f} it/s)'.format(self.short_id, t, self.run_iterations / t))

