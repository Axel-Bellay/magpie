import configparser
import pathlib

import magpie

def recreate_patch(patch : str) :
    if patch.endswith('.patch'):
        with pathlib.Path(patch).open('r') as f:
            patch = f.read().strip()
    return magpie.core.Patch.from_string(patch)

def make_config(scenario) :
    config = configparser.ConfigParser()
    config.read_dict(magpie.core.default_scenario)
    config.read(scenario)

    return config

def make_protocol(config, search) :
    protocol = magpie.utils.element_from_string(config['search']['protocol'], magpie.utils.known_protocols)()
    protocol.search = (
        magpie.utils.element_from_string(config['search']['algorithm'], magpie.utils.known_algos[search])())
    protocol.search.software = (
        magpie.utils.element_from_string(config['software']['software'], magpie.utils.known_software)(config))

    return protocol