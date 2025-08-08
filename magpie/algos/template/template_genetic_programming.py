import copy
import math
import random

import magpie.core
import magpie.utils
from magpie.algos.template.template_search_algorithm import TemplateSearchAlgorithm


class TemplateGeneticProgramming(TemplateSearchAlgorithm):
    def __init__(self):
        super().__init__()
        self.name = 'Genetic Programming'
        self.config['pop_size'] = 10
        self.config['delete_prob'] = 0.5
        self.config['offspring_elitism'] = 0.1
        self.config['offspring_crossover'] = 0.5
        self.config['offspring_mutation'] = 0.4
        self.config['batch_reset'] = True

        self.offsprings = []
        self.pop = {}

    def reset(self):
        super().reset()
        self.stats['gen'] = 0

        self.offsprings = []
        self.pop = {}

    def setup(self, config):
        super().setup(config)
        sec = config['search.gp']
        self.config['pop_size'] = int(sec['pop_size'])
        self.config['delete_prob'] = float(sec['delete_prob'])
        self.config['offspring_elitism'] = float(sec['offspring_elitism'])
        self.config['offspring_crossover'] = float(sec['offspring_crossover'])
        self.config['offspring_mutation'] = float(sec['offspring_mutation'])
        self.config['uniform_rate'] = float(sec['uniform_rate'])
        tmp = sec['batch_reset'].lower()
        if tmp in ['true', 't', '1']:
            self.config['batch_reset'] = True
        elif tmp in ['false', 'f', '0']:
            self.config['batch_reset'] = False
        else:
            msg = '[search.gp] batch_reset should be Boolean'
            raise magpie.core.ScenarioError(msg)

        tries = magpie.settings.edit_retries
        expected = self.config['pop_size']
        while tries and len(self.offsprings) < expected:
            sol = magpie.core.Patch()
            self.mutate(sol)
            if sol in self.offsprings:
                tries -= 1
                continue
            self.offsprings.append(sol)
        got = len(self.offsprings)
        if got < expected:
            self.report['stop'] = f'unable to fill initial population ({got} unique edits generated < {expected})'
            return

    def aux_log_counter(self):
        gen = self.stats['gen']
        step = self.stats['steps']%self.config['pop_size']+1
        return f'{gen}-{step}'

    def hook_start(self):
        self.replace()

    def main_loop(self):
        self.offsprings = []
        parents = self.select(self.pop)
        # elitism
        copy_parents = copy.deepcopy(parents)
        k = int(self.config['pop_size']*self.config['offspring_elitism'])
        for parent in copy_parents[:k]:
            self.offsprings.append(parent)
        # crossover
        copy_parents = copy.deepcopy(parents)
        k = int(self.config['pop_size']*self.config['offspring_crossover'])
        for parent in copy_parents[:k]:
            sol = copy.deepcopy(random.sample(parents, 1)[0])
            if random.random() > 0.5:
                sol = self.crossover(parent, sol)
            else:
                sol = self.crossover(sol, parent)
            self.offsprings.append(sol)
        # mutation
        copy_parents = copy.deepcopy(parents)
        k = int(self.config['pop_size']*self.config['offspring_mutation'])
        for parent in copy_parents[:k]:
            self.mutate(parent)
            self.offsprings.append(parent)
        # regrow
        while len(self.offsprings) < self.config['pop_size']:
            sol = magpie.core.Patch()
            self.mutate(sol)
            if sol in self.offsprings:
                continue # guaranteed to terminate (valid initial population)
            self.offsprings.append(sol)
        # replace
        self.pop.clear()

        self.replace()

    #Compares produced variant's fitness result with local and global best fitness,
    #and updates report values if necessary.
    def replace(self):
        local_best_fitness = None
        for sol in self.offsprings:
            if self.stopping_condition():
                break
            variant = magpie.core.Variant(self.software, sol)
            run = self.evaluate_variant(variant)
            accept = best = False
            if run.status == 'SUCCESS':
                #why use dominate with a field that as been set to None? Why not just check that it is not None?
                if self.dominates(run.fitness, local_best_fitness):
                    local_best_fitness = run.fitness
                    accept = True
                    if self.dominates(run.fitness, self.report['best_fitness']):
                        #that part is the one I want to give to the protocol class
                        self.report['best_fitness'] = run.fitness
                        self.report['best_patch'] = sol
                        best = True
            self.hook_evaluation(variant, run, accept, best)
            self.pop[sol] = run
            self.stats['steps'] += 1


    def mutate(self, patch):
        if patch.edits and random.random() < self.config['delete_prob']:
            del patch.edits[random.randrange(0, len(patch.edits))]
        else:
            patch.edits.append(self.create_edit(self.software.noop_variant))

    def crossover(self, sol1, sol2):
        c = copy.deepcopy(sol1)
        for edit in sol2.edits:
            c.edits.append(edit)
        return c

    def filter(self, pop):
        return {sol for sol in pop if pop[sol].status == 'SUCCESS'}

    def select(self, pop):
        """ returns possible parents ordered by fitness """
        return sorted(self.filter(pop), key=lambda sol: pop[sol].fitness)

    def hook_main_loop(self):
        self.stats['gen'] += 1
        if self.config['batch_reset']:
            for a in self.config['batch_bins']:
                random.shuffle(a)
            self.hook_reset_batch()

magpie.utils.known_algos['genetic_programming'] = []