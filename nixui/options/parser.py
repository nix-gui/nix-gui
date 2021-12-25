# TODO: reorganize this isto parser/parser.py, parser/apply_changes.py, and move syntax_tree.py parser/syntax_tree.py

import uuid

from nixui.utils.logger import logger
from nixui.utils import cache
from nixui.options import syntax_tree, nix_eval, attribute
from nixui.options.option_definition import OptionDefinition


NIX_GUI_COMMENT_STR = ''#'\n\n# Attribute defined by Nix-Gui\n'


def calculate_changed_module(module_path, option_expr_map):
    tree = syntax_tree.SyntaxTree(module_path)
    option_expr_map = dict(option_expr_map)

    # mapping of option to the node which contains its expression
    option_expr_nodes_map = get_key_value_nodes(tree)

    for option, definition in option_expr_map.items():
        # update option expressions where they exist
        if definition is None:
            remove_definition(tree, option)
        elif option in option_expr_nodes_map:
            update_definition(tree, option, definition.expression_string, option_expr_nodes_map)
        else:
            add_definition(tree, option, definition.expression_string)
    return tree.to_string()


def remove_definition(tree, option):
    for attr, attr_data in nix_eval.get_modules_defined_attrs(tree.module_path).items():
        if attr[:len(option)] == option:
            definition_node = tree.get_node_at_line_column(
                attr_data['position']['line'],
                attr_data['position']['column'],
                legal_type='NODE_KEY_VALUE'
            )
            tree.remove(definition_node)


def update_definition(tree, option, expression_str, option_expr_nodes_map):
    value_node = option_expr_nodes_map[option]
    token = syntax_tree.Token(id=uuid.uuid4(), name='INJECTION', position=None, quoted=expression_str)
    tree.replace(value_node, token)
    node_to_prefix_comment = tree.get_parent(
        tree.get_parent(token, node=True),
        node=True
    )
    # insert comment
    tree.insert(
        node_to_prefix_comment,
        syntax_tree.Token(id=uuid.uuid4(), name='INJECTION', position=None, quoted=NIX_GUI_COMMENT_STR),
        index=node_to_prefix_comment.elems.index(tree.get_parent(token, node=True))
    )
    return tree


def add_definition(tree, option, expression_str):
    # node which contains options
    returned_attr_set_node = get_returned_attr_set_node(tree)

    quoted = f'{option} = {expression_str};'
    token = syntax_tree.Token(id=uuid.uuid4(), name='INJECTION', position=None, quoted=quoted)
    tree.insert(returned_attr_set_node, token, index=1)
    # insert comment
    tree.insert(
        tree.get_parent(token, node=True),
        syntax_tree.Token(id=uuid.uuid4(), name='INJECTION', position=None, quoted=NIX_GUI_COMMENT_STR),
        index=1
    )
    return tree


def apply_indentation(string, num_spaces):
    return '\n'.join([
        (' ' * num_spaces) + line
        for line in string.split('\n')
    ])


@cache.cache(return_copy=True, retain_hash_fn=cache.first_arg_path_hash_fn)
def get_all_option_values(module_path, allow_errors=True):
    logger.info(f'Retrieving option values for module "{module_path}"')
    # get option_expr_map for module_path
    option_expr_map = {}
    tree = syntax_tree.SyntaxTree(module_path)
    for attr_loc, value_node in get_key_value_nodes(tree).items():
        option_expr_map[attr_loc] = OptionDefinition.from_expression_string(
            value_node.to_string()
        )

    # for each import, recurse
    for import_path in nix_eval.get_modules_evaluated_import_paths(module_path):
        try:
            # TODO: this isn't the correct way to merge attributes between module imports, it needs to be implemented correctly
            option_expr_map.update(get_all_option_values(import_path))
        except (nix_eval.NixEvalError, FileNotFoundError) as e:
            if allow_errors:
                logger.error(e)  # TODO: ensure all legal import elements are resolved and don't `continue`
                continue
            else:
                raise e

    return option_expr_map


def get_imports_node(tree):
    import_pos = nix_eval.get_modules_import_position(tree.module_path)
    if import_pos is None:
        return None
    return tree.get_node_at_line_column(
        import_pos['line'],
        import_pos['column'],
        legal_type='NODE_KEY_VALUE'
    )


def get_returned_attr_set_node(tree):
    """
    Get the NODE_ATTR_SET containing the attributes which are returned by the module
    """
    # TODO: fix HACK, currently we assume the node containing `imports` is the returned attr set
    #       but this may not always be the case?
    imports_node = get_imports_node(tree)
    imports_key_node, _ = [e for e in imports_node.elems if isinstance(e, syntax_tree.Node)]
    imports_key_value_node = tree.get_parent(imports_key_node)
    returned_attr_set_node = tree.get_parent(imports_key_value_node)
    return returned_attr_set_node


def recursively_get_node_list_data(parent_attribute, node):
    for i, elem_node in enumerate([elem for elem in node.elems if isinstance(elem, syntax_tree.Node)]):
        full_attribute_path = attribute.Attribute.from_insertion(parent_attribute, f"[{i}]")
        yield full_attribute_path, elem_node

        if elem_node.name == 'NODE_ATTR_SET':
            yield from recursively_get_node_attr_set_data(full_attribute_path, elem_node)
        elif elem_node.name == 'NODE_LIST':
            yield from recursively_get_node_list_data(full_attribute_path, elem_node)


def recursively_get_node_attr_set_data(parent_attribute, node):
    for key_value_node in [elem for elem in node.elems if elem.name == 'NODE_KEY_VALUE']:
        key_node, value_node = [e for e in key_value_node.elems if isinstance(e, syntax_tree.Node)]
        full_attribute_path = attribute.Attribute(
            parent_attribute.loc +
            attribute.Attribute(key_node.to_string()).loc
        )
        yield full_attribute_path, value_node
        if value_node.name == 'NODE_ATTR_SET':
            yield from recursively_get_node_attr_set_data(full_attribute_path, value_node)
        elif value_node.name == 'NODE_LIST':
            yield from recursively_get_node_list_data(full_attribute_path, value_node)


def get_key_value_nodes(tree):
    mapping = {}
    for attr, attr_data in nix_eval.get_modules_defined_attrs(tree.module_path).items():
        definition_node = tree.get_node_at_line_column(
            attr_data['position']['line'],
            attr_data['position']['column'],
            legal_type='NODE_KEY_VALUE'
        )

        # TODO: rework Node as well so it's more obvious what's going on here:
        # `key_node, value_node = definition_node.get_children(_type=Node)`
        key_node, value_node = [e for e in definition_node.elems if isinstance(e, syntax_tree.Node)]

        if value_node.name == 'NODE_ATTR_SET':
            for sub_attr, sub_value_node in recursively_get_node_attr_set_data(attr, value_node):
                mapping[sub_attr] = sub_value_node
        elif value_node.name == 'NODE_LIST':
            for sub_attr, sub_value_node in recursively_get_node_list_data(attr, value_node):
                mapping[sub_attr] = sub_value_node
        mapping[attr] = value_node
    return mapping
