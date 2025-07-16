import argparse
import configparser
import pathlib
import sys

from gi.overrides.BlockDev import utils

import magpie
from magpie.bin.utils import recreate_patch


# ================================================================================
# Main function
# ================================================================================


def show_location() :
    target_files = config['software']['target_files'].split()
    for filename in software.target_files:
        if args.filename is not None and args.filename != filename:
            continue
        msg = f'==== {filename} ===='
        if magpie.settings.color_output:
            msg = f'\033[1m{msg}\033[0m'
        print(msg)
        model = software.noop_variant.models[filename]
        for tag in model.locations:
            if args.tag is not None and args.tag != tag:
                continue
            msg = f'~~~~ {tag} ~~~~'
            if magpie.settings.color_output:
                msg = f'\033[1m{msg}\033[0m'
            print(msg)
            for loc in model.locations_names[tag]:
                print(model.show_location(tag, loc))
            print()
    software.clean_work_dir()

def show_patch() :
    patch = recreate_patch(args.patch)
    variant = magpie.core.Variant(software, patch)

    # show patch
    msg = '==== REPORT ===='
    if magpie.settings.color_output:
        msg = f'\033[1m{msg}\033[0m'
    software.logger.info(msg)
    software.logger.info('Patch: %s', patch)
    if args.keep:
        software.logger.info('Artefact: %s', software.work_dir)
        software.write_variant(variant)
    diff = variant.diff
    if magpie.settings.color_output:
        diff = magpie.core.BasicProtocol.color_diff(diff)
    software.logger.info('Diff:\n%s', diff)
    if not args.keep:
        software.clean_work_dir()

def run_visualizer(function) :
    match function:
        case 'show_location' :
            show_location()
        case 'show_patch' :
            show_patch()
        case _ :
            msg = f'"Unknown visualization function {function}"'
            raise RuntimeError(msg)


def parse_arguments(function) :
    parser = argparse.ArgumentParser(description=f'Magpie {function}')
    parser.add_argument('--scenario', type=pathlib.Path, required=True)
    match function :
        case 'show_location' :
            parser.add_argument('--filename', type=str)
            parser.add_argument('--tag', type=str)
        case 'show_patch' :
            parser.add_argument('--patch', type=str, required=True)
            parser.add_argument('--keep', action='store_true')
        case _ :
            print('Unknown visualisation function : ', function)
    return parser.parse_args()

if __name__ == '__main__':
    visualizing_function = sys.argv[1]
    sys.argv = sys.argv[1:]

    args = parse_arguments(visualizing_function)

    config = configparser.ConfigParser()
    config.read_dict(magpie.core.default_scenario)
    config.read(args.scenario)

    magpie.core.pre_setup(config)
    magpie.core.setup(config)
    software = magpie.utils.software_from_string(config['software']['software'])(config)

    run_visualizer(visualizing_function)