from nixui.options import syntax_tree, nix_eval



def get_all_option_values(root_module_path):
    option_expr_map = {}
    for module_path in [root_module_path]:
        get_col_line_index = get_column_line_index_map(module_path)
        tree = syntax_tree.get_syntax_tree(module_path)
        for attr_loc, attr_data in nix_eval.get_modules_defined_attrs(module_path).items():
            character_index = get_col_line_index(
                attr_data['position']['line'] - 1,
                attr_data['position']['column'] - 1
            )  # 'line' and 'column' are 1-indexed
            definition_node = syntax_tree.get_node_at_position(
                tree,
                character_index,
                'NODE_KEY_VALUE'
            )
            key_node, value_node = [e for e in definition_node.elems if isinstance(e, syntax_tree.Node)]
            value_expr = syntax_tree.get_full_node_string(value_node)
            option_expr_map[attr_loc] = value_expr
    return option_expr_map


def get_column_line_index_map(path):
    line_index_map = {}
    line_index = 0
    with open(path) as f:
        for i, line in enumerate(f.readlines()):
            line_index_map[i] = {}

            character_index = line_index
            for j, c in enumerate(line):
                line_index_map[i][j] = character_index
                character_index += len(c.encode("utf8"))

            line_index += len(line.encode("utf8"))

    mapper = lambda line, col: line_index_map[line][col]
    return mapper


def get_imported_modules(module_path):
    return nix_eval.eval_attribute(module_path, "imports")
