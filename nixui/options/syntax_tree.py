import dataclasses
import collections
import functools
import subprocess
import json
import tempfile
import uuid

from nixui.utils import cache

NumRange = collections.namedtuple('NumRange', ['start', 'end'])


@dataclasses.dataclass
class Token:
    id: uuid.UUID = dataclasses.field(default_factory=uuid.uuid4)
    name: str = 'MODIFIED_IN_NIX_GUI'
    position: NumRange = None
    quoted: str = ''

    def to_string(self):
        return self.quoted


@dataclasses.dataclass
class Node:
    id: uuid.UUID = dataclasses.field(default_factory=uuid.uuid4)
    name: str = 'MODIFIED_IN_NIX_GUI'
    position: NumRange = None
    elems: list = dataclasses.field(default_factory=list)

    def to_string(self):
        return ''.join(elem.to_string() for elem in self.elems)


class SyntaxTree:
    def __init__(self, module_path):
        self.module_path = module_path  # static
        self.tree = self._get_tree(self.module_path)  # mutable, with call to self._load_structures()
        self._load_structures()

    # TODO: use hash and get rid of _load_structures

    @classmethod
    @functools.lru_cache()
    def from_string(cls, expression_string):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp:
            temp.write(expression_string)
            temp.flush()
            return cls(temp.name)

    def _load_structures(self):
        self.flattened_nodes = self._get_flattened_nodes(self.tree)
        self.elem_ids = {elem.id: elem for elem in self.flattened_nodes}
        self.elem_parent_map = self._get_elem_parent_map(self.flattened_nodes)
        self.column_line_index_mapper = self._get_column_line_index_map(self.module_path)
        self.root_id = self._get_root_id(self.elem_parent_map)

    @classmethod
    def _get_tree(cls, module_path):
        p = subprocess.Popen(["nix_dump_syntax_tree_json", module_path], stdout=subprocess.PIPE)
        x = json.load(p.stdout)
        p.wait()
        return cls._parse_syntax_tree_dict_node_or_token(x)

    @classmethod
    def _parse_syntax_tree_dict_node_or_token(cls, d):
        start, end = d['text_range']
        if d['kind'].startswith('NODE_'):
            children = [
                cls._parse_syntax_tree_dict_node_or_token(child)
                for child in d['children']
            ]
            return Node(uuid.uuid4(), d['kind'], NumRange(start, end), children)
        else:
            return Token(uuid.uuid4(), d['kind'], NumRange(start, end), d['text'])

    @classmethod
    def _get_flattened_nodes(cls, node):
        res = []
        for elem in node.elems:
            if isinstance(elem, Node):
                res += cls._get_flattened_nodes(elem)
        return res + [node]

    @staticmethod
    def _get_elem_parent_map(flattened_nodes):
        res = {}
        for node in flattened_nodes:
            for elem in node.elems:
                res[elem.id] = node.id
        return res

    @staticmethod
    def _get_column_line_index_map(module_path):
        line_index_map = {}
        index = 0
        with open(module_path) as f:
            for i, line in enumerate(f.readlines()):
                line_index_map[i] = index
                index += len(line.encode())

        mapper = lambda line, col: line_index_map[line] + col
        return mapper

    @staticmethod
    def _get_root_id(elem_parent_map):
        node = next(iter(elem_parent_map.values()))
        while True:
            new_node = elem_parent_map.get(node)
            if new_node is None:
                return node
            node = new_node
        return node

    def _iter_tokens(self, node=None):
        node = node or self.tree
        for elem in node.elems:
            if isinstance(elem, Token):
                yield elem
            else:
                yield from self._iter_tokens(elem)

    def to_string(self, node=None):
        """
        Get code string from AST
        """
        node = node or self.tree
        s = ''
        for elem in node.elems:
            if isinstance(elem, Node):
                s += self.to_string(elem)
            else:
                s += elem.quoted
        return s

    def get_node_at_position(self, pos, legal_type=None, node=None):
        """
        Get the first node of legal_type at character-offset pos
        """
        node = node or self.tree
        if node.position.start == pos:
            return node
        for elem in node.elems:
            if isinstance(elem, Node):
                if elem.position.start <= pos < elem.position.end:
                    new_node = self.get_node_at_position(pos=pos, legal_type=legal_type, node=elem)  # none or list
                    if new_node:
                        if legal_type is None or new_node.name == legal_type:
                            return new_node
        return None

    def get_node_at_line_column(self, line, column, legal_type=None):
        # 'line' and 'column' are 1-indexed
        character_index = self.column_line_index_mapper(line - 1, column - 1)
        return self.get_node_at_position(character_index, legal_type)

    def get_parent(self, elem):
        parent_id = self.elem_parent_map[elem.id]
        parent = self.elem_ids[parent_id]
        return parent

    def get_previous_token(self, elem):
        if elem == self.tree:
            return None
        parent = self.get_parent(elem)
        elem_idx = parent.elems.index(elem)
        if elem_idx == 0:
            return self.get_previous_token(parent)
        prev_elem = parent.elems[elem_idx - 1]
        while isinstance(prev_elem, Node):
            prev_elem = prev_elem.elems[-1]
        return prev_elem

    def get_token_at_end_of_line(self, inline_node):
        # get token containing first instance of a newline after inline_node
        parent_node = self.get_parent(inline_node)
        inline_node_idx = parent_node.elems.index(inline_node)
        for elem in parent_node.elems[inline_node_idx+1:]:
            if '\n' in elem.to_string():
                break
        else:
            return self.get_token_at_end_of_line(parent_node)
        while isinstance(elem, Node):
            for child_elem in elem.elems:
                if '\n' in child_elem.to_string():
                    elem = child_elem
                    break
        return elem

    def replace(self, to_replace, replace_with):
        parent = self.get_parent(to_replace)
        index = [i for i, elem in enumerate(parent.elems) if elem.id == to_replace.id][0]
        parent.elems[index] = replace_with
        self._load_structures()
        return replace_with

    def remove(self, to_remove):
        return self.replace(
            to_remove,
            Token(
                position=to_remove.position,  # keep reference the same, not the true position
            )
        )

    def insert(self, parent, new_value, index=None, after=None):
        if index is None:
            index = len(parent.elems)
        parent.elems.insert(
            index,
            new_value
        )
        self._load_structures()
