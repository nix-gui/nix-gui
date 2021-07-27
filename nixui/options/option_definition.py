import functools

from nixui.options import object_to_expression, nix_eval
from nixui.utils.singleton import Singleton
from nixui.utils.logger import logger


Unresolvable = Singleton()


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

    @property
    @functools.lru_cache()
    def obj(self):
        if 'obj' in self.passed:
            return self.passed['obj']
        else:
            try:
                return nix_eval.nix_instantiate_eval(self.passed['expression_string'])
            except Exception as e:
                logger.error(e)
                return Unresolvable

    @property
    @functools.lru_cache()
    def expression_string(self):
        if 'expression_string' in self.passed:
            return self.passed['expression_string']
        else:
            return object_to_expression.get_formatted_expression(self.passed['obj'])
