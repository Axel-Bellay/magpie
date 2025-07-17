import re

from .known import algos as known_algos
from .known import edits as known_edits
from .known import fitness as known_fitness
from .known import models as known_models
from .known import protocols as known_protocols
from .known import software as known_software

#This search function is repeated 5 times across the file.
#It would be better to have a single one, taking the list it is searching into as an argument.

def element_from_string(s, iterable) :
    for klass in iterable :
        if klass.__name__ == s :
            return klass
    msg = "Could not find element '{}' in '{}'".format(s, iterable)
    raise RuntimeError(msg)

def edit_from_string(s):
    s2 = s.lower().replace('_', '') + 'edit'
    for klass in known_edits:
        if klass.__name__.lower() == s2:
            return klass
    m = re.search(r'(<.+>)', s)
    if m:
        klass = edit_from_string(s.replace(m.group(1), 'Templated'))
        return klass.template(m.group(1))
    msg = f'Unknown edit class "{s}Edit"'
    raise RuntimeError(msg)

def fitness_from_string(s):
    s2 = s.lower().replace('_', '') + 'fitness'
    for klass in known_fitness:
        if klass.__name__.lower() == s2:
            return klass
    m = re.search(r'(<.+>)', s)
    if m:
        klass = fitness_from_string(s.replace(m.group(1), 'Templated'))
        return klass.template(m.group(1))
    msg = f'Unknown fitness class "{s}Fitness"'
    raise RuntimeError(msg)

