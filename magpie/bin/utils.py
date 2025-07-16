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
    protocol = magpie.utils.protocol_from_string(config['search']['protocol'])()
    protocol.search = magpie.utils.element_from_string(config['search']['algorithm'], magpie.utils.known_algos[search])()
    protocol.software = magpie.utils.software_from_string(config['software']['software'])(config)

    return protocol