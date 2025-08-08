import abc
import copy
import random

import magpie.core
import magpie.utils
from magpie.algos.template.template_search_algorithm import TemplateSearchAlgorithm


class TemplateLocalSearch(TemplateSearchAlgorithm):
    def __init__(self):
        super().__init__()
        self.name = 'Local Search'
        self.config['delete_prob'] = 0.5
        self.config['max_neighbours'] = None
        self.config['when_trapped'] = 'continue'

        self.current_patch = None
        self.current_fitness = None

    def reset(self):
        super().reset()
        self.stats['neighbours'] = 0

    def setup(self, config):
        super().setup(config)
        sec = config['search.ls']
        self.config['delete_prob'] = float(sec['delete_prob'])
        self.config['max_neighbours'] = int(val) if (val := sec['max_neighbours']) else None
        self.config['when_trapped'] = sec['when_trapped']

    def hook_start(self):
        super().hook_start()
        self.current_patch = self.protocol.get_from_report('best_patch')
        self.current_fitness = self.protocol.get_from_report('bast_fitness')

    def main_loop(self):
        self.current_patch, self.current_fitness = self.explore(self.current_patch, self.current_fitness)

    @abc.abstractmethod
    def explore(self, current_patch, current_fitness):
        pass

    def mutate(self, patch):
        n = len(patch.edits)
        if n == 0:
            if self.config['delete_prob'] == 1:
                self.report['stop'] = 'trapped'
            else:
                patch.edits.append(self.create_edit(self.software.noop_variant))
        elif random.random() < self.config['delete_prob']:
            del patch.edits[random.randrange(0, n)]
        else:
            patch.edits.append(self.create_edit(self.software.noop_variant))

    def check_if_trapped(self):
        if self.config['max_neighbours'] is None:
            return
        if self.stats['neighbours'] < self.config['max_neighbours']:
            return
        if self.config['when_trapped'] == 'stop':
            self.report['stop'] = 'trapped'
        # TODO: restart, others?

magpie.utils.known_algos['local_search'] = []

class TemplateFirstImprovement(TemplateLocalSearch):
    def __init__(self):
        super().__init__()
        self.name = 'First Improvement'
        self.local_tabu = set()

    def explore(self, current_patch, current_fitness):
        # move
        while True:
            patch = copy.deepcopy(current_patch)
            self.mutate(patch)
            if patch not in self.local_tabu:
                break

        # compare
        #this is the part I would like to
        variant = magpie.core.Variant(self.software, patch)
        run = self.evaluate_variant(variant)
        accept = best = False
        if run.status == 'SUCCESS':
            if not self.dominates(current_fitness, run.fitness):
                accept = True
                if self.dominates(run.fitness, self.report['best_fitness']):
                    self.report['best_fitness'] = run.fitness
                    self.report['best_patch'] = patch
                    best = True

        self.hook_evaluation(variant, run, accept, best)

        # accept
        if accept:
            current_patch = patch
            current_fitness = run.fitness
            self.local_tabu.clear()
            self.stats['neighbours'] = 0
        else:
            if len(patch.edits) < len(current_patch.edits):
                self.local_tabu.add(patch)
            self.stats['neighbours'] += 1
            self.check_if_trapped()

        # hook

        # next
        self.stats['steps'] += 1
        return current_patch, current_fitness

magpie.utils.known_algos['local_search'].append(TemplateFirstImprovement)