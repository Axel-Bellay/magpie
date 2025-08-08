import io
import math
import pathlib
import random
import time

import magpie.settings
import magpie.utils


from magpie.core import Patch, Variant
from magpie.core.errors import ProtocolError
from magpie.core.experimental.abstract_protocol import AbstractProtocol


class SoftwareImrovementProtocol(AbstractProtocol):

    def __init__(self, algorithm, software):
        self.algorithm = algorithm
        self.software = software
        self.config = {}

        self.report = {}
        self.report['initial_patch'] = None
        self.report['reference_patch'] = None
        self.report['reference_fitness'] = None
        self.report['best_fitness'] = None
        self.report['best_patch'] = None
        self.report['stop'] = None

        self.result = {'stop': None, 'best_patch': None}

    def run(self, config):
        logger = self.algorithm.software.logger

        if self.algorithm is None:
            msg = 'Search not specified'
            raise AssertionError(msg)

        # setup search
        self.algorithm.setup(config)

        # log config just in case
        with io.StringIO() as ss:
            config.write(ss)
            ss.seek(0)
            msg = '==== CONFIG ====\n%s'
            if magpie.settings.color_output:
                msg = f'\033[1m{msg}\033[0m'
            logger.debug(msg, ss.read())

        # run the algorithm a single time
        logger.debug('')  # because CONFIG above is also debug
        msg = '==== SEARCH: %s ===='
        if magpie.settings.color_output:
            msg = f'\033[1m{msg}\033[0m'
        logger.info(msg, self.algorithm.__class__.__name__)

        self.log_warmup()
        self.warmup()

        self.algorithm.run()
        self.result.update(self.report)

        self.end_protocol()
        self.log_result()



    # Runs the evaluation pipeline(evaluate_variant method) on an empty software variant, as many times as defined in
    # config['warmup'], to give the search algorithm initial best fitness values to shoot for(initial best patch
    # will be an empty one). The evaluation run defining the initial best fitness will be choosen depending
    # on config['warmup_strategy']
    def warmup(self):
        #TODO : Documentation
        patch = Patch([])
        variant = Variant(self, patch)
        if self.report['initial_patch'] is None:
            self.report['initial_patch'] = patch
        if self.report['reference_patch'] is None:
            self.report['reference_patch'] = patch
        warmup_values = []
        for _ in range(max(self.config['warmup'] or 1, 1), 0, -1):
            run = self.software.evaluate_variant(variant, force=True)
            self.log_evaluation(variant, run, 'WARM', force_success=True)
            if run.status != 'SUCCESS':
                step = run.status.split('_')[0].lower()
                self.report['stop'] = f'failed to {step} target software'
                return
            warmup_values.append(run.fitness)
        if self.config['warmup_strategy'] == 'last':
            current_fitness = warmup_values[-1]
        elif self.config['warmup_strategy'] == 'min':
            current_fitness = min(warmup_values)
        elif self.config['warmup_strategy'] == 'max':
            current_fitness = max(warmup_values)
        elif self.config['warmup_strategy'] == 'mean':
            current_fitness = sum(warmup_values) / len(warmup_values)
        elif self.config['warmup_strategy'] == 'median':
            current_fitness = sorted(warmup_values)[len(warmup_values) // 2]
        else:
            msg = 'Unknown warmup strategy'
            raise ValueError(msg)
        run.fitness = current_fitness
        self.cache_set(variant.diff, run)
        self.log_evaluation(variant, run, 'BEST', force_success=True)
        self.report['reference_fitness'] = current_fitness
        if self.report['best_patch'] is None:
            self.report['best_fitness'] = current_fitness
            self.report['best_patch'] = patch
        else:
            variant = Variant(self, self.report['best_patch'])
            run = self.software.evaluate_variant(variant, force=True)
            self.log_evaluation(variant, run, 'BEST', force_success=True)
            if self.dominates(run.fitness, current_fitness):
                self.report['best_fitness'] = run.fitness
            else:
                self.report['best_patch'] = patch
                self.report['best_fitness'] = current_fitness

    def get_from_report(self, field):
        return self.report[field]

    def receive(self, data):
        if data['variant'] or data['run'] is None:
            raise ProtocolError()
        self.log_evaluation(data['variant'], data['run'], data['counter'], data['accept'], data['best'], data['force_success'])

    def set_search(self, algorithm):
        self.algorithm = algorithm

    #hook_warmup
    def log_warmup(self):
        self.hook_reset_batch()
        self.stats['wallclock_start'] = self.stats['wallclock_warmup'] = time.time()
        msg = '~~~~ WARMUP ~~~~'
        if magpie.settings.color_output:
            msg = f'\033[1m{msg}\033[0m'
        self.software.logger.info(msg)

    #hook_start
    def log_start(self):
        # TODO: check that every possible edit can be created and simplify create_edit
        self.stats['wallclock_start'] = time.time() # discards warmup time
        self.software.logger.info('')
        msg = '~~~~ START ~~~~'
        if magpie.settings.color_output:
            msg = f'\033[1m{msg}\033[0m'
        self.software.logger.info(msg)

    # hook evaluation
    def log_evaluation(self, variant, run, counter=None, accept=False, best=False, force_success=False):
        if counter is None:
            counter = self.aux_log_counter()
        data = self.aux_log_data(variant.patch, run, counter, self.report['reference_fitness'], accept, best)
        self.aux_log_print(data, run, accept, best)
        if force_success and run.status != 'SUCCESS':
            self.software.diagnose_error(run)

    #hook_end
    def end_protocol(self):
        self.stats['wallclock_end'] = time.time()
        self.stats['wallclock_total'] = self.stats['wallclock_end'] - self.stats['wallclock_start']
        if self.report['best_patch']:
            variant = Variant(self.software, self.report['best_patch'])
            self.report['diff'] = variant.diff
        msg = '~~~~ END ~~~~'
        if magpie.settings.color_output:
            msg = f'\033[1m{msg}\033[0m'
        self.software.logger.info(msg)

    def log_result(self):
        # print the report
        self.software.logger.info('')
        msg = '==== REPORT ===='
        if magpie.settings.color_output:
            msg = f'\033[1m{msg}\033[0m'
        self.software.logger.info(msg)
        self.software.logger.info('Termination: %s', self.result['stop'])
        for handler in self.software.logger.handlers:
            if handler.__class__.__name__ == 'FileHandler':
                self.software.logger.info('Log file: %s', handler.baseFilename)
        if self.result['best_fitness'] and self.result['best_patch'] and self.result['best_patch'].edits:
            base_path = pathlib.Path(magpie.settings.log_dir) / self.search.software.run_label
            patch_file = f'{base_path}.patch'
            diff_file = f'{base_path}.diff'
            self.software.logger.info('Patch file: %s', patch_file)
            self.software.logger.info('Diff file: %s', diff_file)
            tmp = self.result['reference_fitness']
            if not isinstance(tmp, list):
                tmp = [tmp]
            self.software.logger.info('Reference fitness: %s', ' '.join([magpie.settings.log_format_fitness.format(x) for x in tmp]))
            self.software.logger.debug('Raw reference fitness: %s', ' '.join([str(x) for x in tmp]))
            tmp = self.result['best_fitness']
            if not isinstance(tmp, list):
                tmp = [tmp]
            self.software.logger.info('Best fitness: %s', ' '.join([magpie.settings.log_format_fitness.format(x) for x in tmp]))
            self.software.logger.debug('Raw best fitness: %s', ' '.join([str(x) for x in tmp]))

            self.software.logger.info('')
            msg = '==== BEST PATCH ====\n%s'
            diff = self.result['diff']
            if magpie.settings.color_output:
                msg = '\033[1m==== BEST PATCH ====\033[0m\n%s'
                diff = self.color_diff(diff)
            self.software.logger.info(msg, self.result['best_patch'])

            self.software.logger.info('')
            msg = '==== DIFF ====\n%s'
            diff = self.result['diff']
            if magpie.settings.color_output:
                msg = '\033[1m==== DIFF ====\033[0m\n%s'
                diff = self.color_diff(diff)
            self.software.logger.info(msg, diff)

            # for convenience, save best patch and diff to separate files
            with pathlib.Path(patch_file).open('w') as f:
                f.write(str(self.result['best_patch']) + '\n')
            with pathlib.Path(diff_file).open('w') as f:
                f.write(self.result['diff'])

        # cleanup temporary software copies
        self.search.software.clean_work_dir()

    def aux_log_counter(self):
        return str(self.stats['steps'] + 1)

    #Logs a patch and it's evaluation's run data(status, fitness, number of the run, etc.) into a 'data' dict and returns it
    def aux_log_data(self, patch, run, counter, baseline, accept, best):
        #TODO : documentation.
        data = {}
        data['counter'] = counter or self.aux_log_counter()
        data['status'] = run.status
        data['best'] = '*' if best else '+' if accept else ' '
        data['rawfitness'] = data['fitness'] = 'None'
        if run.fitness is not None:
            tmp = run.fitness
            if not isinstance(run.fitness, list):
                tmp = [tmp]
            data['rawfitness'] = ' '.join([str(x) for x in tmp])
            data['fitness'] = ' '.join([magpie.settings.log_format_fitness.format(x) for x in tmp])
        data['ratio'] = '--'
        if run.fitness is not None and baseline is not None:
            if isinstance(run.fitness, list):
                tmp = [fit / base if base != 0 else math.inf for fit, base in zip(run.fitness, baseline)]
            else:
                tmp = [run.fitness / baseline]
            data['ratio'] = ' '.join([magpie.settings.log_format_ratio.format(x) for x in tmp])
        data['extra'] = 'extra'
        data['log'] = run.log or ''
        data['patch'] = str(patch)
        data['patchifaccept'] = magpie.settings.log_format_patchif.format(patch=data['patch']) if accept else ''
        data['patchifbest'] = magpie.settings.log_format_patchif.format(patch=data['patch']) if best else ''
        data['diff'] = run.variant.diff
        data['diffifaccept'] = magpie.settings.log_format_diffif.format(diff=data['diff']) if accept else ''
        data['diffifbest'] = magpie.settings.log_format_diffif.format(diff=data['diff']) if best else ''
        data['size'] = f'{len(patch.edits) if patch else 0} edit(s)'
        data['cached'] = ''
        if run.cached:
            if run.updated:
                data['cached'] = '[part.cached]'
            else:
                data['cached'] = '[cached]'
        return data

    def aux_log_print(self, data, run, accept, best):
        """
            Prints data dict parameter into the software's attribute's logger,
            after adding the appropriate colour by calling the aux_log_color method with the run, accept and best
            parameters as argument.

            Returns
           -------
           None
        """
        if magpie.settings.log_format_info:
            msg = magpie.settings.log_format_info.format(**data)
            if magpie.settings.color_output:
                msg = self.aux_log_color(msg, run, accept=accept, best=best)
            self.software.logger.info(msg)
        if magpie.settings.log_format_debug:
            msg = magpie.settings.log_format_debug.format(**data)
            self.software.logger.debug(msg)

    def aux_log_color(self, msg, run, accept=False, best=False):
        """
           Apply ANSI color codes to `msg` based on the run's status and flags.

           Color logic:
               - No color applied if `magpie.settings.color_output` is False.
               - Black  (code 30): run is cached and not updated.
               - Green  (code 32): `best` is True (best result so far).
               - Yellow (code 33): `accept` is True (accepted but not necessarily best).
               - Red    (code 31): run status is not 'SUCCESS' (error or failure).
               - Default: no color.

           Parameters
           ----------
           msg : str
               The message to colorize.
           run : object
               An object with attributes:
                   - cached (bool): whether the run is cached.
                   - updated (bool): whether the run has been updated.
                   - status (str): run status string (e.g., 'SUCCESS').
           accept : bool, optional
               Whether the run has been accepted (default: False).
           best : bool, optional
               Whether the run yields the best fitness result so far (default: False).

           Returns
           -------
           str
               The message with ANSI color codes applied (if enabled).
        """
        if magpie.settings.color_output is False:
            return msg
        if run.cached and not run.updated:
            return f'\033[30m{msg}\033[0m'
        if best:
            return f'\033[32m{msg}\033[0m'
        if accept:
            return f'\033[33m{msg}\033[0m'
        if run.status != 'SUCCESS':
            return f'\033[31m{msg}\033[0m'
        return msg