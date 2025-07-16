import configparser
import argparse
import pathlib
import sys
import functools

import magpie

if __name__ == '__main__':
    print("Bienvenue dans software_improvement.py")

    search_type = sys.argv[1]
    parser = argparse.ArgumentParser(description=f'Magpie {search_type}')
    sys.argv = sys.argv[1:]

    parser.add_argument('--scenario', type=pathlib.Path, required=True)
    parser.add_argument('--algo', type=str)
    parser.add_argument('--seed', type=int)
    args = parser.parse_args()

    config = configparser.ConfigParser()
    config.read_dict(magpie.core.default_scenario)
    config.read(args.scenario)
    magpie.core.pre_setup(config)

    # select GP algorithm
    if args.algo is not None:
        algo = magpie.utils.algo_from_string(args.algo)
        if not magpie.utils.known_algos[search_type].contains(algo) : # Critical point for refactoring
            msg = f'Invalid genetic programming algorithm "{algo.__name__}"'
            raise RuntimeError(msg)
        config['search']['algorithm'] = args.algo
    else:
        algo = magpie.utils.known_algos[search_type][0]
        config['search']['algorithm'] = algo.__name__

    # setup protocol
    magpie.core.setup(config)
    protocol = magpie.utils.protocol_from_string(config['search']['protocol'])()
    protocol.search = algo()
    protocol.software = magpie.utils.software_from_string(config['software']['software'])(config)

    # run experiments
    protocol.run(config)