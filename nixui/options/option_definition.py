import dataclasses
import functools
import os
import subprocess

from nixui.options import nix_eval, syntax_tree, types
from nixui.utils.singleton import Singleton
from nixui.utils import hash_by_json


Unresolvable = Singleton('Unresolvable')
Undefined = Singleton('Undefined')


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class Path:
    path: str = None
    cwd: str = None

    def eval_full_path(self):
        return os.path.join(
            os.path.normpath(self.cwd),
            os.path.normpath(self.path)
        )


class OptionDefinition:
    """
    A unified representation of an expression, with @properties providing both the python and string form

    Can be constructed using either a python object, an expression string, or an expression ast node
    Properties are dynamically loaded to reduce unnecessary computations

    Conversions from passed value to @property
    - ast node -> expression string
    - ast node -> object
    - expression string -> ast node -> object
    - object -> expression string
    - object -> object type

    Note that there is no @property for ast_node

    Some conversions require context to be passed. The context dict can have the following values:
    - cwd: Used to get the absolute path from a relative path
    - todo: ???
    """
    def __init__(self, context=None, **kwargs):
        assert kwargs != {}
        self.passed = kwargs
        self.context = context or {}

    @classmethod
    def from_object(cls, obj, context=None):
        return cls(obj=obj, context=context)

    @classmethod
    def from_expression_string(cls, expression_string, context=None):
        return cls(expression_string=expression_string, context=context)

    def from_ast_node(cls, ast_node, context=None):
        return cls(ast_node=ast_node, context=context)

    @classmethod
    def undefined(cls):
        return cls(expression_string='')

    @property
    @functools.lru_cache()
    def obj(self):
        if 'obj' in self.passed:
            return self.passed['obj']
        elif not self.expression_string:
            return Undefined
        else:
            return expression_node_to_python_object(
                self._get_ast_node(),
                self.context
            )

    @property
    @functools.lru_cache()
    def obj_type(self):
        return self.get_object_type(self.obj)

    @classmethod
    def get_object_type(cls, obj):
        if isinstance(obj, list):
            subtypes = set([cls.get_object_type(elem) for elem in obj])
            if len(subtypes) == 0:
                return types.ListOfType()
            if len(subtypes) == 1:
                return types.ListOfType(subtypes.pop())
            else:
                return types.ListOfType(types.EitherType(subtypes))
        elif isinstance(obj, bool):
            return types.BoolType()
        elif isinstance(obj, int):
            return types.IntType()
        elif isinstance(obj, float):
            return types.FloatType()
        elif isinstance(obj, str):
            return types.StrType()
        elif isinstance(obj, Path):
            return types.PathType()
        elif obj is None:
            return types.NullType()
        else:
            raise NotImplementedError

    @property
    def expression_string(self):
        if 'expression_string' in self.passed:
            return self.passed['expression_string']
        else:
            return get_formatted_expression(self.passed['obj'])

    @functools.lru_cache()
    def _get_ast_node(self):
        if 'ast_node' in self.passed:
            return self.passed['ast_node']
        tree = syntax_tree.SyntaxTree.from_string(self.passed['expression_string'])
        root_node = tree.elem_ids[tree.root_id]
        assert len(root_node.elems) == 1
        return root_node.elems[0]

    @property
    def is_undefined(self):
        return self.expression_string == ''

    def __repr__(self):
        return f"OptionDefinition(obj={repr(self.obj)}, expression_string={self.expression_string})"

    def __hash__(self):
        return hash((
            self.passed.get('expression_string'),
            hash_by_json.hash_object(self.passed.get('obj'))
        ))

    def __eq__(self, other):
        # optimized __eq__ operator intended to avoid expensive operations
        if self.is_undefined and other.is_undefined:
            return True
        elif self.is_undefined != other.is_undefined:
            return False
        elif tuple(self.passed.keys()) == tuple(other.passed.keys()):
            return self.passed == other.passed
        else:
            return self.expression_string == other.expression_string


#############################
# object to expression string
#############################
def get_formatted_expression(obj):
    return format_expression(
        get_expression(obj)
    )

@functools.lru_cache()
def format_expression(expression_str):
    p = subprocess.run(
        ['nixpkgs-fmt'],
        stdout=subprocess.PIPE,
        input=expression_str,
        encoding='ascii',
        stderr=subprocess.PIPE,  # log_pipe,
    )
    return p.stdout


def get_expression(obj):
    if obj == Undefined:
        return ''
    elif isinstance(obj, bool):
        return str(obj).lower()
    elif isinstance(obj, list):
        space_separated = ' '.join([get_expression(elem) for elem in obj])
        return f"[{space_separated}]"
    elif isinstance(obj, str):
        # TODO: properly escape
        if len(obj.split('\n')) > 1:
            return f"''\n{obj.strip()}\n''"
        else:
            return f'"{obj}"'
    elif isinstance(obj, int) or isinstance(obj, float):
        return str(obj)
    elif obj is None:
        return "null"
    else:
        raise TypeError(str((type(obj), obj)))


#############################
# Expression string to object
#############################
def expression_node_to_python_object(value_node, context):
    if value_node.name == 'NODE_LIST':
        # recursively generate list object
        return [
            expression_node_to_python_object(child_node, context)
            for child_node in value_node.elems
            if isinstance(child_node, syntax_tree.Node)
        ]

    elif value_node.name == 'NODE_STRING':
        assert value_node.elems[0].name == 'TOKEN_STRING_START'
        assert value_node.elems[-1].name == 'TOKEN_STRING_END'
        python_obj = ''
        for child_node in value_node.elems[1:-1]:
            if child_node.name == 'TOKEN_STRING_CONTENT':
                python_obj += child_node.quoted
            elif child_node.name == 'NODE_STRING_INTERPOL':
                return Unresolvable  # TODO: handle string interpolation
            else:
                return Unresolvable  # TODO
        return python_obj

    elif value_node.name == 'NODE_IDENT':
        if len(value_node.elems) == 1 and value_node.elems[0].name == 'TOKEN_IDENT':
            if value_node.elems[0].quoted == 'true':
                return True
            elif value_node.elems[0].quoted == 'false':
                return False
            else:
                return Unresolvable  # TODO

    elif value_node.name == 'NODE_LITERAL':
        if len(value_node.elems) == 1:
            if value_node.elems[0].name == 'NODE_PATH':
                return Unresolvable  # TODO
            if value_node.elems[0].name == 'TOKEN_PATH':
                return Path(
                    value_node.elems[0].quoted,
                    context['module_dir'],
                )
            elif value_node.elems[0].name == 'TOKEN_INTEGER':
                return int(value_node.elems[0].quoted)
            elif value_node.elems[0].name == 'TOKEN_URI':
                return str(value_node.elems[0].quoted)
            elif value_node.elems[0].name == 'TOKEN_FLOAT':
                return float(value_node.elems[0].quoted)

    elif value_node.name == 'NODE_WITH':
        # TODO: handle with statement using rnix-lsp
        return Unresolvable

    else:
        try:
            return nix_eval.nix_instantiate_eval(value_node.to_string())
        except nix_eval.NixEvalError:
            return Unresolvable

    raise ValueError(value_node.to_string())
