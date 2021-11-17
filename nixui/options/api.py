import copy
import os

from nixui.options import parser, nix_eval, option_tree, types
from nixui.utils import cache, store, remap_dict


#############################
# utility functions / caching
############################
@cache.cache(cache.first_arg_path_hash_fn, diskcache=False)
def get_option_tree(configuration_path=None):
    if configuration_path is None:
        configuration_path = os.environ['CONFIGURATION_PATH']

    system_option_data_dict = remap_dict.key_remapper(
        nix_eval.get_all_nixos_options(),
        {'system_default': 'system_default_definition'}
    )
    for key, value in system_option_data_dict.items():
        system_option_data_dict[key]['type_string'] = system_option_data_dict[key]['type']
        if 'type' in value:
            system_option_data_dict[key]['type'] = types.from_nix_type_str(system_option_data_dict[key]['type'])
        else:
            system_option_data_dict[key]['type'] = types.AttrsType()

    return option_tree.OptionTree(
        system_option_data_dict,
        parser.get_all_option_values(configuration_path)
    )


###############
# Apply Updates
###############
def apply_updates(option_definition_map):
    """
    option_definition_map: map between option string and python object form of value
    """
    option_expr_str_map = {
        option: option_definition.expression_string
        for option, option_definition in option_definition_map.items()
    }
    module_string = parser.inject_expressions(
        os.environ['CONFIGURATION_PATH'],  # TODO: fix this hack - we should get the module the option is defined in
        option_expr_str_map
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
