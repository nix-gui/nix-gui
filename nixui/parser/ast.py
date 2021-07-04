import collections
import parsimonious
import subprocess


###################
# utility functions
###################
def get_node_at_position(node, pos, legal_type=None):
    if node.position.start == pos:
        return node
    for elem in node.elems:
        if isinstance(elem, Node):
            if elem.position.start <= pos <= elem.position.end:
                new_node = get_node_at_position(elem, pos)  # none or list
                if new_node:
                    if legal_type is None or new_node.name == legal_type:
                        return new_node
    return None


def get_full_node_string(node):
    s = b''
    for elem in node.elems:
        if isinstance(elem, Node):
            s += get_full_node_string(elem)
        else:
            s += elem.quoted
    return s


##############
# generate ast
#############
def get_ast(file_path):
    ast_str = get_ast_str(file_path)
    ast_str = ast_str.decode().replace('\\\"', 'EQ')  # TODO 3929: fix hack - can't parse \" properly
    return parse_ast_str(ast_str)


def get_ast_str(file_path):
    res = subprocess.run(
        [
            "dump-ast",
            file_path
        ],
        stdout=subprocess.PIPE,
    )
    return res.stdout


def parse_ast_str(ast_str):
    # parsing the dumped ast string
    tree = AST_DUMP_GRAMMAR.parse(ast_str)
    root_node = NixVisitor().visit(tree)
    assert len(root_node) == 1
    return root_node[0]


Node = collections.namedtuple('Node', ['name', 'position', 'elems'])
Token = collections.namedtuple('Token', ['name', 'position', 'quoted'])
NumRange = collections.namedtuple('NumRange', ['start', 'end'])


AST_DUMP_GRAMMAR = parsimonious.grammar.Grammar("""
    elems =      elem+
    elem =       token / node

    node =       name ws numrange ws lbracket ws elems rbracket ws
    token =      name lpar quoted rpar ws numrange ws

    name =       ~r"[A-Z]+(?:_[A-Z]+)*"
    numrange =   ~r"[0-9]+\.\.[0-9]+"

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
        quoted = quoted.replace('EQ', '\"')  # TODO: fix hack (see note 3929 above)
        quoted = quoted.encode('utf-8')  # unescape
        return Token(name, position, quoted)

    def visit_numrange(self, node, visited_children):
        start, end = node.text.split('..')
        return NumRange(int(start), int(end))

    def generic_visit(self, node, visited_children):
        return node.text
