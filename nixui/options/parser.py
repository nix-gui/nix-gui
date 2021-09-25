import uuid

from nixui.utils.logger import logger
from nixui.utils import cache
from nixui.options import syntax_tree, nix_eval
from nixui.options.option_definition import OptionDefinition, Unresolvable


def inject_expressions(module_path, option_expr_map):
    tree = syntax_tree.SyntaxTree(module_path)
    option_expr_map = dict(option_expr_map)

    # mapping of option to the node which contains its expression
    option_expr_nodes_map = get_key_value_nodes(module_path, tree)

    # node which contains options
    returned_attr_set_node = get_returned_attr_set_node(module_path, tree)

    comment_str = '\n\n# Attribute defined by Nix-Gui\n'

    for option, expression in option_expr_map.items():
        # update option expressions where they exist
        if option in option_expr_nodes_map:
            key_node, value_node = option_expr_nodes_map[option]
            token = syntax_tree.Token(id=uuid.uuid4(), name='INJECTION', position=None, quoted=expression)
            tree.replace(value_node, token)
            node_to_prefix_comment = tree.get_parent(
                tree.get_parent(token, node=True),
                node=True
            )
            # insert comment
            tree.insert(
                node_to_prefix_comment,
                syntax_tree.Token(id=uuid.uuid4(), name='INJECTION', position=None, quoted=comment_str),
                index=node_to_prefix_comment.elems.index(tree.get_parent(token, node=True))
            )
        # add new option definitions where they don't exist
        else:
            quoted = f'{option} = {expression};'
            token = syntax_tree.Token(id=uuid.uuid4(), name='INJECTION', position=None, quoted=quoted)
            tree.insert(returned_attr_set_node, token, index=1)
            # insert comment
            tree.insert(
                tree.get_parent(token, node=True),
                syntax_tree.Token(id=uuid.uuid4(), name='INJECTION', position=None, quoted=comment_str),
                index=1
            )
    return tree.to_string()


def apply_indentation(string, num_spaces):
    return '\n'.join([
        (' ' * num_spaces) + line
        for line in string.split('\n')
    ])


@cache.cache(return_copy=True, retain_hash_fn=cache.first_arg_path_hash_fn)
def get_all_option_values(module_path):
    logger.info(f'Retrieving option values for module "{module_path}"'
    # get option_expr_map for module_path
    option_expr_map = {}
    tree = syntax_tree.SyntaxTree(module_path)
    for attr_loc, (key_node, value_node) in get_key_value_nodes(module_path, tree).items():
        option_expr_map[attr_loc] = OptionDefinition.from_expression_string(
            value_node.to_string()
        )

    # get imports node from syntax tree and recurse if possible
    imports_node = get_imports_node(module_path, tree)
    if imports_node is None:
        return option_expr_map

    # extract definition from imports_node
    _, imports_value_node = [e for e in imports_node.elems if isinstance(e, syntax_tree.Node)]
    imports_definition = OptionDefinition.from_expression_string(
        imports_value_node.to_string(),
        {'module_dir': os.path.dirname(module_path)}
    )
    # for each valid parsable import, recurse
    for i, import_path in enumerate(imports_definition.obj):
        if import_path == Unresolvable:
            logger.error(f'failed to load element {i} of \n{imports_definition.expression_string}')
            continue
        full_import_path = import_path.eval_full_path()
        try:
            # TODO: this isn't the correct way to merge attributes between modules, it needs to be implemented
            option_expr_map.update(get_all_option_values(full_import_path))
        except nix_eval.NixEvalError as e:
            logger.error(e)  # TODO: ensure all legal import elements are resolved and don't `continue`
            continue

    return option_expr_map


def get_imports_node(module_path, tree):
    import_pos = nix_eval.get_modules_import_position(module_path)
    if import_pos is None:
        return None
    return tree.get_node_at_line_column(
        import_pos['line'],
        import_pos['column'],
        legal_type='NODE_KEY_VALUE'
    )


def get_returned_attr_set_node(module_path, tree):
    """
    Get the NODE_ATTR_SET containing the attributes which are returned by the module
    """
    # TODO: fix HACK, currently we assume the node containing `imports` is the returned attr set
    #       but this may not always be the case?
    imports_node = get_imports_node(module_path, tree)
    imports_key_node, _ = [e for e in imports_node.elems if isinstance(e, syntax_tree.Node)]
    imports_key_value_node = tree.get_parent(imports_key_node)
    returned_attr_set_node = tree.get_parent(imports_key_value_node)
    return returned_attr_set_node


def get_key_value_nodes(module_path, tree):
    mapping = {}
    for attribute, attr_data in nix_eval.get_modules_defined_attrs(module_path).items():
        definition_node = tree.get_node_at_line_column(
            attr_data['position']['line'],
            attr_data['position']['column'],
            legal_type='NODE_KEY_VALUE'
        )
        # TODO: rework Node as well so it's more obvious what's going on here:
        # `key_node, value_node = definition_node.get_children(t=Node)`
        key_node, value_node = [e for e in definition_node.elems if isinstance(e, syntax_tree.Node)]
        mapping[attribute] = (key_node, value_node)
    return mapping
