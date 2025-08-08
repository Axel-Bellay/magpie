import copy
import math
import random
import time
import abc

import magpie.core
import magpie.utils
from magpie.core import BasicAlgorithm, AbstractAlgorithm


#implementation of the search algorithms of magpie based on the template method pattern.
class TemplateSearchAlgorithm(AbstractAlgorithm):
    def __init__(self):
        self.config = {}
        self.config['possible_edits'] = []
        self.stop = {'wall': None, 'steps': None, 'budget': None, 'fitness': None}
        self.reset()

        self.protocol = None
        self.software = None

    def run(self):
        """
        Template method defining and enforcing structure for the search algorithm.

        Stopping conditions are set by the protocol, and checked here in the
        stopping_conditions() method.

        The main_loop() method is abstract and left to be implemented by the subclasses.

        Additional computation can be added before, after, and at each step of the main loop, by implementing the
        hook methods. If not implemented they will execute following the default implementation described here.

        The algorithm can be stopped at any moment by a keyboard interrupt.

        Returns
        ------
        None
        """
        try:

            self.hook_start()
            while not self.stopping_condition():
                self.hook_main_loop()
                self.main_loop()

        except KeyboardInterrupt:
            self.report['stop'] = 'keyboard interrupt'

        finally:
            self.hook_end()

    #if we need extra calculation before the main loop
    def hook_start(self):
        if not self.config['possible_edits']:
            msg = 'Possible_edits list is empty'
            raise RuntimeError(msg)

    #if wee need extra calculation at each step
    def hook_main_loop(self):
        pass

    #main loop of search algo, to be implemented by subclasses
    @abc.abstractmethod
    def main_loop(self):
        pass

    #if we need extra calculation at the end of the algorithm
    def hook_end(self):
        pass

    # Pics a random edit subclass and creates an edit object of chosen class.
    def create_edit(self, variant=None):
        ref = variant or self.software.noop_variant
        klass = random.choice(self.config['possible_edits'])
        tries = magpie.settings.edit_retries
        while (edit := klass.auto_create(ref)) is None:
            tries -= 1
            if tries == 0:
                msg = f'Unable to create an edit of class {klass.__name__}'
                raise RuntimeError(msg)
        return edit

    def stopping_condition(self):
        """
        Check for all stopping conditions defined in the stop dictionary attribute.

        Those conditions are :
            - Have we exceeded the number of steps?
            - Have we exceeded the time limit?
            - Have we reached the best possible fitness?

        Returns
        ------
        bool
            True if one of the stopping conditions is met, False otherwise.
        """
        if self.report['stop'] is not None:
            return True
        #haven't fouund the attribute referenced anywhere else so it's use is unclear to me
        if self.stop['budget'] is not None:
            if self.stats['budget'] >= self.stop['budget']:
                self.report['stop'] = 'budget'
                return True
        if self.stop['wall'] is not None:
            now = time.time()
            if now >= self.stats['wallclock_start'] + self.stop['wall']:
                self.report['stop'] = 'time budget'
                return True
        if self.stop['steps'] is not None:
            if self.stats['steps'] >= self.stop['steps']:
                self.report['stop'] = 'step budget'
                return True
        if self.stop['fitness'] and self.report['best_fitness']:
            if self.dominates_or_equal(self.report['best_fitness'], self.stop['fitness']):
                self.report['stop'] = 'target fitness reached'
                return True
        return False

    def dominates(self, fit1, fit2):
        """
        Check if a fitness value is dominated.

        Three cases are considered
            I - One of the fitness results is None
                - if fit1 is None it cannot dominate anything
                - if fit2 is None it is automatically dominated by fit1
            II - fit1 is a list(which implies fit2 is a list as well)
            That is the case when a software evaluates his variant on multiple instance of fitness object,
            with those instances possibly of different types. inst1 and inst2 are the result for the fitness object i
            in the list of fitness function held by the software object
                - if inst1 < inst2, and the fitness must be maximized, then fit1 does not dominate fit2
                - if inst1 > inst2, and the fitness must be minimized, then fit1 does not dominate fit2
            III - fit1 and fit2 are simple numbers
            That is the case when a software evaluates his variants on only one instance of fitness object.
            The result is calculated in the same way as in case 2, but this time only on one instance.

        Parameters
        ------
        fit1: numeral value, list
            We check if this fitness value dominates fit2.
        fit2: numeral value, list
            We check if this fitness value is dominated by fit1.

        Returns
        ------
        boolean
            True if fit1 dominates fit2, False otherwise.
        """
        if fit1 is None:
            return False
        if fit2 is None:
            return True
        if isinstance(fit1, list):
            for i, (inst1, inst2) in enumerate(zip(fit1, fit2)):
                if inst1 < inst2:
                    return not self.software.fitness[i].maximize
                if inst1 > inst2:
                    return self.software.fitness[i].maximize
            return False
        if self.fitness[0].maximize:
            return fit1 > fit2
        else:
            return fit1 < fit2

    # Adds tolerance for equality in the dominate method, in the case of evaluation on single fitness object.
    def dominates_or_equal(self, fit1, fit2):
        return self.dominates(fit1, fit2) or fit1 == fit2

    def evaluate_variant(self, variant, force=False):
        """
        Evaluate a software variant by passing it into the execution pipeline of
        the software attribute
        Parameters
        ------
        variant : magpie.core.Variant
              The variant to evaluate
        force : bool, optional
            Whether we want to force execution of the variant parameter, or check if a similar variant as already
            been tested on the same data, in which case we gain time by returning the cached run without running
            the execution pipeline (default : False)
        Returns
        ------
        magpie.core.RunResult
            The RunResults object containing the evaluated variant, the execution status, and it's fitness result.
        """
        cached_run = None
        if self.config['cache_maxsize'] > 0 and not force:
            cached_run = self.software.cache_get(variant.diff)  # potentially partial
        run = self.software.evaluate_variant(variant, cached_run)
        if self.config['cache_maxsize'] > 0:
            self.software.cache_set(variant.diff, run)
        self.stats['budget'] += getattr(run, 'budget', 0) or 0
        return run