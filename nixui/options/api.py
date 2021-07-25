import collections
import functools
import json
import os
import subprocess

from nixui.options import parser, nix_eval, object_to_expression, attribute
from nixui.utils import tree, store, copy_decorator, cache


NoDefaultSet = ('NO DEFAULT SET',)


#############################
# utility functions / caching
############################
@cache.cache(return_copy=True, retain_hash_fn=cache.configuration_path_hash_fn)
def get_option_data():
    defaults_and_schema = nix_eval.get_all_nixos_options()
    configured_values = parser.get_all_option_values(os.environ['CONFIGURATION_PATH'])
    result = {}
    for option, option_data in defaults_and_schema.items():
        result[option] = dict(option_data)
        if 'default' not in option_data:
            result[option]['default'] = NoDefaultSet
        if option in configured_values:
            result[option]['value_expr'] = configured_values[option]
            try:
                result[option]['value'] = nix_eval.nix_instantiate_eval(configured_values[option])
            except:
                pass
    return result


# TODO: split the above into functions for
# - get option schema
# - get option default
# - get option types


@cache.cache(return_copy=True, retain_hash_fn=cache.configuration_path_hash_fn)
def get_option_values_map():
    # extract actual value
    return {
        option: option_data.get('value', option_data['default'])
        for option, option_data in get_option_data().items()
    }


@cache.cache(return_copy=True, retain_hash_fn=cache.configuration_path_hash_fn)
def get_option_tree():
    options = get_option_data()
    options_tree = tree.Tree()

    for attr, attr_data in options.items():
        options_tree.add_leaf(attr.loc, attr_data)

    return options_tree



@functools.lru_cache(1)
def get_all_packages_map():
    path_name_map = {}
    for package in open('./all_packages_out').readlines():
        pkg_name, pkg_str, store_path = [x.strip() for x in package.split(' ') if x]
        path_name_map[store_path] = pkg_name
    return path_name_map


# TODO: remove
def get_types():
    argumented_types = ['one of', 'integer between', 'string matching the pattern']
    types = collections.Counter()
    for v in get_option_data().values():
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


################
# get values api
################
def get_next_branching_option(option):
    # if an attribute is alone in a set, get the child set recursively
    # 0 children = leaf -> exit
    # more than 1 child = branch -> exit
    node = get_option_tree().get_node(option)
    while len(node.get_children()) == 1:
        node_type = get_option_type(option)
        if node_type.startswith('attribute set of '):
            break
        key = node.get_children()[0]
        node = node.get_node([key])
        option = attribute.Attribute.from_insertion(option, key)
    return option


@functools.lru_cache(1000)
def get_child_options(parent_option):
    # child options sorted by count
    # TODO: sort by hardcoded priority per readme too
    child_options = [
        attribute.Attribute.from_insertion(parent_option, o)
        for o in get_option_tree().get_children(parent_option)
    ]
    return sorted(child_options, key=lambda x: -get_option_count(x))  # TODO: this is a bad sort and difficult to navigate


def get_option_count(parent_option):
    return get_option_tree().get_count(parent_option.loc)


def get_leaf(option):
    node = get_option_tree().get_node(option)
    return node.get_leaf()


def get_option_type(option):
    return get_leaf(option).get('type', 'PARENT')


def get_option_description(option):
    return get_leaf(option)['description']


def get_option_value(option):
    # TODO: fix - actual value it isn't always the default
    if 'value' in get_leaf(option):
        return get_leaf(option)['value']
    elif 'default' in get_leaf(option):
        return get_leaf(option)['default']
    else:
        print()
        print('no default or value found for')
        print(option)
        print(get_leaf(option))


###############
# Apply Updates
###############
def apply_updates(option_value_obj_map):
    """
    option_value_obj_map: map between option string and python object form of value
    """
    option_expr_map = {
        option: object_to_expression.get_formatted_expression(value_obj)
        for option, value_obj in option_value_obj_map.items()
    }
    module_string = parser.inject_expressions(
        os.environ['CONFIGURATION_PATH'],  # TODO: fix this hack - we should get the module the option is defined in
        option_expr_map
    )
    # TODO: once stable set save_path to os.environ['CONFIGURATION_PATH']
    if os.environ.get('NIXGUI_CONFIGURATION_PATH_CAN_BE_CORRUPTED'):
        save_path = os.environ['CONFIGURATION_PATH']
    else:
        save_path = os.path.join(
            store.get_store_path(),
            'configurations',
            os.environ['CONFIGURATION_PATH'].strip(r'/'),
        )
    if not os.path.exists(os.path.dirname(save_path)):
        os.makedirs(os.path.dirname(save_path))
    with open(save_path, 'w') as f:
        f.write(module_string)
    return save_path
