import functools
import pickle
import subprocess

from nixui.graphics import package_manager
from nixui.options import nix_eval
from nixui.utils.singleton import Singleton
from nixui.utils.logger import logger


Unresolvable = Singleton('Unresolvable')
Undefined = Singleton('Undefined')


class OptionDefinition:
    """
    A unified representation of an expression, with @properties providing both the python and string form
    """
    def __init__(self, **kwargs):
        assert ('expression_string' in kwargs) != ('obj' in kwargs)  # one or the other but not both
        self.passed = kwargs

    @classmethod
    def from_object(cls, obj):
        return cls(obj=obj)

    @classmethod
    def from_expression_string(cls, expression_string):
        return cls(expression_string=expression_string)

    @classmethod
    def undefined(cls):
        return cls(expression_string='')

    @property
    @functools.lru_cache()
    def obj(self):
        if 'obj' in self.passed:
            return self.passed['obj']
        elif not self.passed['expression_string']:
            return Undefined
        else:
            try:
                return nix_eval.nix_instantiate_eval(self.passed['expression_string'])
            except Exception as e:
                logger.error(e)
                return Unresolvable

    @property
    def expression_string(self):
        if 'expression_string' in self.passed:
            return self.passed['expression_string']
        else:
            return get_formatted_expression(self.passed['obj'])

    @property
    def is_undefined(self):
        return self.expression_string == ''

    def __repr__(self):
        return f"OptionDefinition(obj={repr(self.obj)}, expression_string={self.expression_string})"

    def __hash__(self):
        return hash((
            self.passed.get('expression_string'),
            pickle.dumps(self.passed.get('obj'))
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
    if True:#with LogPipe('INFO') as log_pipe:
        p = subprocess.run(
            ['nixpkgs-fmt'],
            stdout=subprocess.PIPE,
            input=expression_str,
            encoding='ascii',
            stderr=subprocess.PIPE,#log_pipe,
        )
        return p.stdout


def get_expression(obj):
    if obj == Undefined:
        return Undefined
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
    elif isinstance(obj, package_manager.Package):
        return "pkgs.hello"  # TODO
    elif isinstance(obj, int) or isinstance(obj, float):
        return str(obj)
    elif obj is None:
        return "null"
    else:
        raise TypeError(str((type(obj), obj)))
