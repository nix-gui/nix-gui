import collections
import json
import functools
import re


import containers


#############################
# utility functions / caching
#############################
@functools.lru_cache(1)
def get_options_dict():
    return json.load(open('./release_out/share/doc/nixos/options.json'))


@functools.lru_cache(1)
def get_option_tree():
    options = get_options_dict()
    options_tree = containers.Tree()

    for option_name, opt in options.items():
        options_tree.add_leaf(option_name.split('.'), opt)

    return options_tree


def get_used_types():
    argumented_types = ['one of', 'integer between', 'string matching the pattern']
    types = collections.Counter()
    for v in get_options_dict().values():
        types.update([v['type']])
        continue
        new_types = []
        for t in v['type'].split(' or '):
            for arg_t in argumented_types:
                if arg_t in t:
                    new_types.append(arg_t)
                    break
            else:
                new_types.append(t)
        types.update(new_types)

    return types


#####
# api
#####
def full_option_name(parent_option, sub_option):
    if parent_option and sub_option:
        return '.'.join([parent_option, sub_option])
    elif parent_option:
        return parent_option
    elif sub_option:
        return sub_option
    else:
        return None


def get_next_branching_option(option):
    # 0 children = leaf -> exit
    # more than 1 child = branch -> exit
    branch = [] if option is None else option.split('.')
    node = get_option_tree().get_node(branch)

    while len(node.get_children()) == 1:
        key = node.get_children()[0]
        node = node.get_node([key])
        branch += [key]
    return '.'.join(branch)

@functools.lru_cache(1000)
def get_child_options(parent_option):
    # child options sorted by count
    # TODO: sort by hardcoded priority per reodme too
    if parent_option is None:
        child_options = get_option_tree().get_children([])
    else:
        branch = parent_option.split('.')
        child_options = [f'{parent_option}.{o}' for o in get_option_tree().get_children(branch)]
    return sorted(child_options, key=lambda x: -get_option_count(x))



def get_option_count(parent_option):
    branch = [] if parent_option is None else parent_option.split('.')
    return get_option_tree().get_count(branch)


def get_type(option):
    branch = [] if option is None else option.split('.')
    tree = get_option_tree().get_node(branch)
    return tree.get_leaf().get('type', 'PARENT')


def get_leaf(option):
    branch = [] if option is None else option.split('.')
    node = get_option_tree().get_node(branch)
    return node.get_leaf()
