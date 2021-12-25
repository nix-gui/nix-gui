# TODO: reorganize this isto parser/parser.py, parser/apply_changes.py, and move syntax_tree.py parser/syntax_tree.py
import datetime as dt

from nixui.utils.logger import logger
from nixui.utils import cache
from nixui.options import syntax_tree, nix_eval
from nixui.options.attribute import Attribute
from nixui.options.option_definition import OptionDefinition


NIX_GUI_COMMENT_STR = ''#'\n\n# Attribute defined by Nix-Gui\n'


def calculate_changed_module(module_path, option_expr_map):
    """
    For each updated option,
        Find the definition node to be changed in the appropriate module (TODO: currently only uses the "root" module)
        Apply the change
        Get a new syntax tree with the applied changes
    Return resulting module string
    """
    option_expr_map = dict(option_expr_map)

    current_datetime = dt.datetime.now()

    tree = syntax_tree.SyntaxTree(module_path)

    for option, definition in sorted(option_expr_map.items(), key=str):
        if definition is None:
            apply_remove_definition(tree, option, current_datetime)
        elif option in get_key_value_nodes(tree):
            apply_update_definition(tree, option, definition.expression_string, current_datetime)
        else:
            apply_add_definition(tree, option, definition.expression_string, current_datetime)

        logger.debug('Applying changes to module, this iterations changes:')
        logger.debug(tree.to_string())

        # new clean instance of the mutated tree
        tree = syntax_tree.SyntaxTree.from_string(tree.to_string())
    return tree.to_string()


def apply_remove_definition(tree, option, current_datetime):
    """
    Given the option foo.bar, find all option definitions in syntax tree which start with foo.bar, and delete them.
    replace with comment `# Nix-Gui removed <option> on <datestamp>`
    """
    matching_attr_nodes = {
        attr: node for attr, node
        in get_key_value_nodes(tree).items()
        if attr.startswith(option)
    }
    # don't redundantly delete child definitions that are already removed by deleting the "base" definition
    valid_matching_attr_nodes = {
        attr: node for attr, node
        in matching_attr_nodes.items()
        if sum(map(attr.startswith, matching_attr_nodes)) <= 1
    }

    for attr, node in valid_matching_attr_nodes.items():
        if attr[:len(option)] == option:
            if not attr.is_list_index(-1):
                # if list index, remove the element, otherwise remove the key in the attribute set too
                node = tree.get_parent(node)
            blank_node = tree.remove(node)

            insert_comment(
                tree,
                blank_node,
                f'# Nix-Gui removed {attr} on {current_datetime}'
            )


def apply_update_definition(tree, option, new_expression_str, current_datetime):
    """
    Find the definition node for `option`, and replace the its child value node with expression_str
    Add `# Changed by Nix-Gui on <datestamp>` after or above the definition
    """
    value_node = get_key_value_nodes(tree)[option]
    # keep reference the same, not the true position
    new_definition_token = syntax_tree.Token(quoted=new_expression_str, id=value_node.id)
    tree.replace(value_node, new_definition_token)

    insert_comment(
        tree,
        new_definition_token,
        f'# Changed by Nix-Gui on {current_datetime}'
    )


def apply_add_definition(tree, option, expression_str, current_datetime):
    """
    Find the place to inject a new option definition, and insert the syntax constructing
    remainder of the attribute path (the "suffix") containing the expression string.
    Add # Nix-Gui changed `option` on <datestamp> after or above the definition
    """
    attr_node_map = get_key_value_nodes(tree)

    # get longest shared base path in order to find attribute sets the new definition can
    # be placed in OR definitions which the attribute should be placed *near*
    longest_shared_base_path_attr = Attribute([])
    valid_attr_paths = list(attr_node_map)
    for i in range(len(option)):
        closest_matching_attr_paths = valid_attr_paths
        valid_attr_paths = [ap for ap in valid_attr_paths if ap[:i] == option[:i]]
        if not valid_attr_paths:
            break
        longest_shared_base_path_attr = option[:i]
    else:
        closest_matching_attr_paths = valid_attr_paths

    if longest_shared_base_path_attr in attr_node_map:
        # if longest shared base path has an attribute set or list, write within that
        # collection. Insert the definition at the end before the closing `}` or `]`

        parent_node = attr_node_map[longest_shared_base_path_attr]
        assert parent_node.name in ('NODE_LIST', 'NODE_ATTR_SET')

        # rule: place the inserted definition before the last whitespace in the parent definition
        # append same indent / whitespace as the first element in the definition contains
        assert parent_node.elems[0].name in ('TOKEN_SQUARE_B_OPEN', 'TOKEN_CURLY_B_OPEN')
        if parent_node.elems[1].name == 'TOKEN_WHITESPACE':
            whitespace_prefix = parent_node.elems[1].quoted
        else:
            whitespace_prefix = ' '

        # rule: insert before last whitespace if it exists
        assert parent_node.elems[-1].name in ('TOKEN_SQUARE_B_CLOSE', 'TOKEN_CURLY_B_CLOSE')
        insertion_idx = -2 if parent_node.elems[-2].name == 'TOKEN_WHITESPACE' else -1

        # insert
        insertion_node = syntax_tree.Node()
        tree.insert(parent_node, syntax_tree.Token(quoted=whitespace_prefix), insertion_idx)
        tree.insert(parent_node, insertion_node, insertion_idx)
        attr_suffix = option[len(longest_shared_base_path_attr):]
    else:
        # if longest shared base path doesn't have an attribute set,
        # write immediately below the first attribute set with a common attribute set
        previous_line_path = sorted(closest_matching_attr_paths, key=len)[0]
        previous_line_node = tree.get_parent(attr_node_map[previous_line_path])
        previous_line_whitespace = tree.get_previous_token(previous_line_node)
        if previous_line_whitespace.name == 'TOKEN_WHITESPACE':
            whitespace_prefix = previous_line_whitespace.quoted.split('\n')[-1]
        else:
            whitespace_prefix = ' '
        insertion_node = syntax_tree.Node()
        tree.insert(
            previous_line_node,
            syntax_tree.Token(quoted='\n' + whitespace_prefix),
        )
        tree.insert(
            previous_line_node,
            insertion_node,
        )
        attr_suffix = option

    # insert definition and comment
    inserted_definition_node = get_node_for_attribute_suffix(
        tree,
        attr_suffix,
        expression_str,
        structure_exists=True
    )
    tree.insert(
        insertion_node,
        inserted_definition_node,
    )
    insert_comment(
        tree,
        inserted_definition_node,
        f'# Changed by Nix-Gui on {current_datetime}'
    )


def get_node_for_attribute_suffix(tree, attr_suffix, expression_str, structure_exists=False):
    if not attr_suffix:
        return syntax_tree.Token(quoted=expression_str)

    # insert multiple sequential non-list keys, or a single key
    attr_group = []
    for attr_key in attr_suffix:
        if Attribute.get_attr_key_list_index(attr_key) is None:
            attr_group.append(attr_key)
        else:
            break

    if attr_group:
        # insert as last attribute in set
        attr_key = '.'.join(attr_group)
        return syntax_tree.Node(elems=[
            syntax_tree.Token(quoted=f'{attr_key} = ' if structure_exists else f'{{ {attr_key} = '),
            get_node_for_attribute_suffix(tree, attr_suffix[len(attr_group):], expression_str),
            syntax_tree.Token(quoted=';' if structure_exists else '; }'),
        ])
    else:
        # prepend whitespace to lone list element
        if structure_exists:
            return get_node_for_attribute_suffix(tree, attr_suffix[1:], expression_str)
        else:
            return syntax_tree.Node(elems=[
                syntax_tree.Token(quoted=' ' if structure_exists else '[ '),
                get_node_for_attribute_suffix(tree, attr_suffix[1:], expression_str),
                syntax_tree.Token(quoted=' ' if structure_exists else ' ]'),
            ])


def insert_comment(tree, inline_node, comment_str):
    eol_token = tree.get_token_at_end_of_line(inline_node)

    # if there already is a nix-gui change comment, remove it
    possible_comment_str = tree.get_previous_token(eol_token).to_string()
    if possible_comment_str.startswith('# Changed by Nix-Gui on') or possible_comment_str.startswith('# Added by Nix-Gui on'):
        tree.get_previous_token(eol_token).quoted = ''
    elif inline_node.to_string().strip():
        # add 2 spaces before comment if line isn't empty
        comment_str = '  ' + comment_str

    # replace eol token with comment str
    eol_token.quoted = eol_token.quoted.replace('\n', comment_str + '\n', 1)
    eol_token.name = 'MODIFIED_IN_NIX_GUI'


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
        full_attribute_path = Attribute.from_insertion(parent_attribute, f"[{i}]")
        yield full_attribute_path, elem_node

        if elem_node.name == 'NODE_ATTR_SET':
            yield from recursively_get_node_attr_set_data(full_attribute_path, elem_node)
        elif elem_node.name == 'NODE_LIST':
            yield from recursively_get_node_list_data(full_attribute_path, elem_node)


def recursively_get_node_attr_set_data(parent_attribute, node):
    for key_value_node in [elem for elem in node.elems if elem.name == 'NODE_KEY_VALUE']:
        key_node, value_node = [e for e in key_value_node.elems if isinstance(e, syntax_tree.Node)]
        full_attribute_path = Attribute(
            parent_attribute.loc +
            Attribute(key_node.to_string()).loc
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
