import subprocess

from nixui.utils.logger import LogPipe


def get_formatted_expression(obj):
    return format_expression(
        get_expression(obj)
    )


def format_expression(expression_str):
    with LogPipe('INFO') as log_pipe:
        p = subprocess.Popen(
            ['nixpkgs-fmt'],
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=log_pipe,
        )
        return p.communicate(input=expression_str)[0]


def get_expression(obj, within_set_or_list=False):
    if isinstance(obj, list):
        space_separated = ' '.join([get_expression(elem) for elem in obj])
        expr = f"[{space_separated}]"
    elif isinstance(obj, str):
        expr = f"''{obj}''"  # TODO: properly escape
    elif isinstance(obj, int):
        expr = str(obj)
    elif obj is None:
        expr = "null"

    if not within_set_or_list:
        expr += ";"

    return expr
