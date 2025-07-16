import argparse
import configparser
import functools
import pathlib
import sys

import magpie
from magpie.bin.utils import recreate_patch, make_config, make_protocol

# ================================================================================
# Main function
# ================================================================================

if __name__ == '__main__':

    operation = sys.argv[1]
    parser = argparse.ArgumentParser(description=f'Magpie {operation}')
    print(operation)
    sys.argv = sys.argv[1:]

    parser.add_argument('--scenario', type=pathlib.Path, required=True)
    parser.add_argument('--patch', type=str, required=True)
    parser.add_argument('--seed', type=int)
    args = parser.parse_args()

    # creating necessary data structures
    config = make_config(args.scenario)
    patch = recreate_patch(args.patch)

    # setup
    magpie.core.pre_setup(config)
    config['search']['algorithm'] = magpie.utils.known_algos[operation][0].__name__ #Critical point for refactoring
    print(config['search']['algorithm'])
    magpie.core.setup(config)

    protocol = make_protocol(config, operation)
    protocol.search.debug_patch = patch

    # run experiments
    protocol.run(config)
