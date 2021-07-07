import subprocess

from nixui.utils.logger import LogPipe


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


def get_expression(obj, within_set_or_list=False):
    if isinstance(obj, list):
        space_separated = ' '.join([get_expression(elem) for elem in obj])
        expr = f"[{space_separated}]"
    elif isinstance(obj, str):
        if len(obj.split('\n')) > 1:
            expr = f'''\n{obj.strip()}\n'''
        else:
            expr = f'"{obj}"'  # TODO: properly escape
    elif isinstance(obj, int):
        expr = str(obj)
    elif obj is None:
        expr = "null"
    else:
        raise TypeError(str((type(obj), obj)))

    if not within_set_or_list:
        expr += ";"

    return expr
