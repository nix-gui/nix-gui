import collections
import subprocess
import json


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
    s = ''
    for elem in node.elems:
        if isinstance(elem, Node):
            s += get_full_node_string(elem)
        else:
            s += elem.quoted
    return s


##############
# generate ast
#############
Node = collections.namedtuple('Node', ['name', 'position', 'elems'])
Token = collections.namedtuple('Token', ['name', 'position', 'quoted'])
NumRange = collections.namedtuple('NumRange', ['start', 'end'])

def get_syntax_tree(file_path):
    p = subprocess.Popen(["nix_dump_syntax_tree_json", file_path], stdout=subprocess.PIPE)
    x = json.load(p.stdout)
    p.wait()
    return parse_syntax_tree_dict_node_or_token(x)

def parse_syntax_tree_dict_node_or_token(d):
    start, end = d['text_range']

    if d['kind'].startswith('NODE_'):
        children = [ parse_syntax_tree_dict_node_or_token(child) for child in d['children'] ]
        return Node(d['kind'], NumRange(start, end), children)
    else:
        return Token(d['kind'], NumRange(start, end), d['text'])
