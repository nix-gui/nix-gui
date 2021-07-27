import subprocess

from nixui.utils.logger import LogPipe
from nixui.options.option_tree import Undefined


def get_formatted_expression(obj):
    return format_expression(
        get_expression(obj)
    )


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
    elif isinstance(obj, int) or isinstance(obj, float):
        return str(obj)
    elif obj is None:
        return "null"
    else:
        raise TypeError(str((type(obj), obj)))
