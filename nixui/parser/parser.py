import collections

from nixui.parser import ast
from nixui import nix_eval


def get_all_option_values(root_module_path):
    option_expr_map = {}
    for module_path in [root_module_path]:
        get_col_line_index = get_column_line_index_map(module_path)
        syntax_tree = ast.get_ast(module_path)
        for attr_loc, attr_data in nix_eval.get_modules_defined_attrs(module_path).items():
            character_index = get_col_line_index(
                attr_data['position']['line'] - 1,
                attr_data['position']['column'] - 1
            )  # 'line' and 'column' are 1-indexed
            definition_node = ast.get_node_at_position(
                syntax_tree,
                character_index,
                'NODE_KEY_VALUE'
            )
            key_node, value_node = [e for e in definition_node.elems if isinstance(e, ast.Node)]
            value_expr = ast.get_full_node_string(value_node)
            option_expr_map[attr_loc] = value_expr
    return option_expr_map


def get_column_line_index_map(path):
    line_index_map = {}
    index = 0
    with open(path) as f:
        for i, line in enumerate(f.readlines()):
            line_index_map[i] = index
            index += len(line.encode("utf8"))

    mapper = lambda line, col: line_index_map[line] + col
    return mapper


def get_imported_modules(module_path):
    return nix_eval.eval_attribute(module_path, "imports")
