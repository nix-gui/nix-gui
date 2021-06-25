from dataclasses import dataclass
import collections
import functools
import itertools
import json
import os
import shutil
import subprocess
import tempfile
import glob
import parsimonious

from nixui.containers import Tree


def get_imported_modules():
    #TODO: hack - fix to use the actual imported files
    return ['/etc/nixos/configuration.nix'] + glob.glob("/etc/nixos/*.nix")


def parse_file(path):
    ast_str = get_ast(path).decode().replace('\\\"', 'ESCAPEQUOTE')  # TODO: fix hack - can't parse \" properly
    tree = parse_ast_str(ast_str)
    res = process_node(tree)
    import pdb;pdb.set_trace()


def get_ast(file_name):
    res = subprocess.run(
        [
            "dump-ast",
            file_name
        ],
        stdout=subprocess.PIPE,
    )
    return res.stdout


def get_option_values(scope=None):
    return parse_file('/etc/nixos/configuration.nix')
    for mod_path in get_imported_modules():
        ast_str = get_ast(mod_path).decode().replace('\\\"', 'ESCAPEQUOTE')  # TODO 3929: fix hack - can't parse \" properly
        tree = parse_ast_str(ast_str)
        context = process_node(tree)
        return context


def parse_ast_str(ast_str):
    # parsing the dumped ast string
    print(ast_str)
    tree = AST_DUMP_GRAMMAR.parse(ast_str)
    root_node = NixVisitor().visit(tree)
    assert len(root_node) == 1
    return root_node[0]


#####
# lex
#####
Node = collections.namedtuple('Node', ['name', 'position', 'elems'])
Token = collections.namedtuple('Token', ['name', 'position', 'quoted'])
NumRange = collections.namedtuple('NumRange', ['start', 'end'])


AST_DUMP_GRAMMAR = parsimonious.grammar.Grammar("""
    elems =      elem+
    elem =       token / node

    node =       name ws numrange ws lbracket ws elems rbracket ws
    token =      name lpar quoted rpar ws numrange ws

    name =       ~r"[A-Z]+(?:_[A-Z]+)*"
    numrange =  ~r"[0-9]+\.\.[0-9]+"

    lpar =       "("
    rpar =       ")"
    lbracket =   "{"
    rbracket =   "}"
    ws =         ~r"\s*"

    quoted =     ~r'"[^\"]+"'
""")


class NixVisitor(parsimonious.nodes.NodeVisitor):
    def visit_elems(self, node, visited_children):
        """ Returns the overall output. """
        return visited_children

    def visit_elem(self, node, visited_children):
        """ Returns the overall output. """
        token_or_node, = visited_children
        return token_or_node

    def visit_node(self, node, visited_children):
        """ Returns the overall output. """
        name, _, position, _, _, _, elems, _, _ = visited_children
        return Node(name, position, elems)

    def visit_token(self, node, visited_children):
        """ Returns the overall output. """
        name, _, quoted, _, _, position, _ = visited_children
        quoted = quoted[1:-1]  # strip quote symbols (TODO: move this to the grammar)
        quoted = quoted.replace('ESCAPEQUOTE', '\"')  # TODO: fix hack (see note 3929 above)
        quoted = quoted.encode('utf-8').decode('unicode_escape')  # unescape
        return Token(name, position, quoted)

    def visit_numrange(self, node, visited_children):
        return node.text.split('..')

    def generic_visit(self, node, visited_children):
        return node.text


"""
Parse Dependency Graph
----------------------

To establish which variables must be evaluated we create an Evaluation Dependency Graph.

This graph can be used to determine, for example, the "true" resolution of a package.
E.g. if pythonPackages.numpy were installed based on a configuration file, we wouldn't know whether
pythonPackages.numpy, python3Packages.numpy, or python38Packages.numpy was the intended installation target
through evaluation of the expression. We must parse the nix expression.

We create a mapping between variable names and the variables / attributes necessary to evaluate the specific variable.
E.g. `services.dbus.packages = [ pkgs.gnome3.gnome_terminal foo ]` would turn into the following mapping:
services.dbus.packages -> [(node where `pkgs` is defined), (node where `foo` is defined)

Resources:
- https://github.com/NixOS/nix/blob/master/src/libexpr/parser.y

TODO: copy dict so scope isn't mutated unexpectedly
"""


@dataclass
class Define:
    ident: str
    node: Node
    dependencies: list

    def __hash__(self):
        return hash(self.ident)


def get_child_nodes(node, legal_names=None, only_one=False):
    child_nodes = [elem for elem in node.elems if isinstance(elem, Node)]
    if legal_names:
        child_nodes = [n for n in child_nodes if n.name in legal_names]
    if only_one:
        assert len(child_nodes) == 1, child_nodes
        return child_nodes[0]
    return child_nodes


def get_child_tokens(node, legal_names=None, only_one=False):
    child_tokens = [elem for elem in node.elems if isinstance(elem, Token)]
    if legal_names:
        child_tokens = [t for t in child_tokens if t.name in legal_names]
    if only_one:
        assert len(child_tokens) == 1
        return child_tokens[0]
    return child_tokens


def get_child_attr_names(name):
    # TODO: properly resolve name, right now it just assumes it's `import <nixpkgs>`
    res = subprocess.run(
        [
            "nix-instantiate",
            "--eval",
            "--json",
            "-E",
            "builtins.attrNames (import <nixpkgs> {})",
            "--json",
        ],
        stdout=subprocess.PIPE,
    ).stdout
    return json.loads(res)


def process_node(node, scope=None):
    scope = scope or {}

    print()
    print(node)

    handlers = {
        'NODE_ROOT': process_root_node,
        'NODE_LAMBDA': process_lambda_node,
        'NODE_LET_IN': process_let_in_node,
        'NODE_KEY_VALUE': process_key_value_node,
        'NODE_IDENT': process_ident_node,
        'NODE_KEY': process_key_node,
        'NODE_APPLY': process_apply_node,
        'NODE_ATTR_SET': process_attr_set_node,
        'NODE_SELECT': process_select_node,
        'NODE_STRING': process_string_node,
        'NODE_LIST': process_list_node,
        'NODE_LITERAL': process_literal_node,
        'NODE_WITH': process_with_node,
    }
    return handlers[node.name](node, scope)


def process_root_node(node, scope):
    # TODO: specify this node as a dependency for `config`
    data = []
    for elem in get_child_nodes(node):
        res = process_node(elem, scope)
        if res:
            data.append(res)

    return data


def process_lambda_node(node, scope):
    child_nodes = get_child_nodes(node)
    assert len(child_nodes) == 2
    assert child_nodes[0].name == 'NODE_PATTERN'

    scope.update(process_pattern_node(child_nodes[0], scope))
    # TODO: should the data be merged?
    return process_node(child_nodes[1], scope)


def process_pattern_node(node, scope):
    child_nodes = get_child_nodes(node)
    assert all([child_node.name == 'NODE_PAT_ENTRY' for child_node in child_nodes])

    for child_node in child_nodes:
        grand_child_nodes = get_child_nodes(child_node)
        if get_child_tokens(child_node, 'TOKEN_QUESTION'):
            assert len(grand_child_nodes) == 2
            node_ident = grand_child_nodes[0]
            token_ident = get_child_tokens(node_ident, ['TOKEN_IDENT'], only_one=True)
            scope[token_ident.quoted] = Define(
                token_ident.quoted,
                child_node,
                process_node(grand_child_nodes[1], scope)
            )
        else:
            assert len(grand_child_nodes) == 1
            node_ident = grand_child_nodes[0]
            token_ident = get_child_tokens(node_ident, ['TOKEN_IDENT'], only_one=True)
            scope[token_ident.quoted] = Define(token_ident.quoted, child_node, [])

    return scope


def process_let_in_node(node, scope):
    let_nodes, in_nodes = [
        [e for e in x[1] if isinstance(e, Node)]
        for x in itertools.groupby(node.elems, lambda x: x.name == 'TOKEN_IN') if not x[0]
    ]

    for node in let_nodes:
        scope.update(process_node(node, scope))

    assert len(in_nodes) == 1
    return process_node(in_nodes[0], scope)


def process_key_value_node(node, scope):
    key_node, value_node = get_child_nodes(node)
    key = process_node(key_node, scope)

    return {key: Define(
        key,
        node,
        process_node(value_node, scope)
    )}


def process_key_node(node, scope):
    if get_child_tokens(node, ['TOKEN_DOT']):
        return '.'.join([
            get_child_tokens(child_node, ['TOKEN_IDENT'], only_one=True).quoted
            for child_node in get_child_nodes(node, ['NODE_IDENT'])
        ])
    else:
        child_node = get_child_nodes(node, ['NODE_IDENT'], only_one=True)
        return get_child_tokens(child_node, ['TOKEN_IDENT'], only_one=True).quoted


def process_string_node(node, scope):
    s = ''
    for token in get_child_tokens(node):
        s += token.quoted

    return s

def process_ident_node(node, scope):
    assert len(get_child_nodes(node)) == 0
    return '.'.join([tok.quoted for tok in get_child_tokens(node, ['TOKEN_IDENT'])])


def process_select_node(node, scope):
    child_nodes = get_child_nodes(node)
    if child_nodes[0].name == 'NODE_SELECT':
        assert len(child_nodes) == 2
        key, dependency = process_select_node(child_nodes[0], scope)
        key = get_child_tokens(child_nodes[-1], ['TOKEN_IDENT'], only_one=True).quoted + '.' + key
    else:
        key = '.'.join([process_ident_node(child_node, scope) for child_node in child_nodes])
        print(key)
        dependency = scope[key.split('.')[0]]

    return key, dependency


def process_apply_node(node, scope):
    # TODO: this needs to add all variables to the scope which result from applying

    res = get_child_nodes(node)
    fn_node = res[0]
    arg_nodes = res[1:]

    for node in res:
        if node.name == 'NODE_IDENT':
            get_child_tokens(fn_node, ['TOKEN_IDENT'], only_one=True).quoted
        elif node.name == 'NODE_LITERAL':
            get_child_tokens(fn_node, only_one=True).quoted
        elif node.name == 'NODE_ATTR_SET':
            pass
        else:
            process_node(node, scope)


def process_attr_set_node(node, scope):
    kv_nodes = get_child_nodes(node)
    assert all([kv_node.name == 'NODE_KEY_VALUE' for kv_node in kv_nodes])

    data = []
    for kv_node in kv_nodes:
        data.append(
            process_key_value_node(kv_node, scope)
        )

    return data


def process_list_node(node, scope):
    elements = []
    for child_node in get_child_nodes(node):
        elements.append(
            process_node(child_node, scope)
        )

    return elements


def process_literal_node(node, scope):
    token = get_child_tokens(node, only_one=True)
    return token.quoted


def process_with_node(node, scope):
    # with cannot override existing scope
    node_ident, node_inner = get_child_nodes(node)
    with_scope_key = process_node(node_ident, scope)

    # TODO: fix this hack, this improperly handles cases where there are two `with` statements importing the same thing
    if with_scope_key not in scope:
        scope[('with', with_scope_key)] = scope[with_scope_key]

    names = get_child_attr_names(with_scope_key)
    with_scope = {}
    for name in names:
        with_scope[name] = Define(
            name,
            node_ident,
            scope
        )
    scope.update(with_scope)

    return process_node(node_inner, scope)


def process_paren_node(node, scope):
    open_paren, child_node, close_paren = get_child_nodes(node)
