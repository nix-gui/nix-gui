import collections
import functools
import os

from nixui.options import parser, nix_eval, object_to_expression, option_tree
from nixui.utils import store, cache


#############################
# utility functions / caching
############################
@functools.lru_cache()
def get_option_tree():
    return option_tree.OptionTree(
        nix_eval.get_all_nixos_options(),
        parser.get_all_option_values(os.environ['CONFIGURATION_PATH'])
    )


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
