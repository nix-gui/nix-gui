import json
import subprocess

from nixui.logging import LogPipe, logger


def nix_instantiate_eval(expr, strict=False):
    logger.debug(expr)
    cmd = [
        "nix-instantiate",
        '--eval',
        '-E',
        expr,
        '--json'
    ]
    if strict:
        cmd.append('--strict')

    with LogPipe('INFO') as log_pipe:
        res = subprocess.check_output(cmd, stderr=log_pipe)

    return json.loads(res)


def get_modules_defined_attrs(module_path, attr_loc=[]):
    attributes = {}
    for sub_attr_datapoint in get_subattribute_data(module_path, attr_loc):
        full_attr_loc = attr_loc + [sub_attr_datapoint['name']]
        if sub_attr_datapoint['position'] is not None and sub_attr_datapoint['position']['file'] == module_path:
            if sub_attr_datapoint['type'] != 'set':
                attributes[tuple(full_attr_loc)] = sub_attr_datapoint
            else:
                res = get_modules_defined_attrs(
                    module_path,
                    full_attr_loc
                )
                if not res:
                    attributes[tuple(full_attr_loc)] = sub_attr_datapoint
                else:
                    attributes.update(res)
    return attributes


def eval_attribute(module_path, attribute):
    expr = (
        "(import " +
        module_path +
        " {config = {}; pkgs = import <nixpkgs> {}; lib = import <nixpkgs/lib>;})." +
        attribute
    )
    return nix_instantiate_eval(expr)


def get_subattribute_data(module_path, attr_loc):
    """
    get name, type, and position (line, column, filename)
    of all child-attributes in `attr_loc`'s set
    """
    attr_lookup = ('.' + '.'.join([f'"{a}"' for a in attr_loc])) if attr_loc else ''
    expr = f"""
    let
      loadedmodule = import {module_path} {{config = {{}}; pkgs = import <nixpkgs> {{}}; lib = import <nixpkgs/lib>;}};
    in (
      map
      (x: rec {{
        name = x;
        type = builtins.typeOf (builtins.getAttr x loadedmodule{attr_lookup});
        position = builtins.unsafeGetAttrPos x loadedmodule{attr_lookup};
      }})
      (builtins.attrNames loadedmodule{attr_lookup})
    )
    """
    return nix_instantiate_eval(expr, strict=True)


def eval_attribute_position(module_path, attr_loc):
    attribute_prefix = '.'.join(attr_loc[:-1])
    attribute_end = attr_loc[-1]
    expr = (
        "builtins.unsafeGetAttrPos \"" +
        attribute_end +
        "\" (import " +
        module_path +
        "{config = {}; pkgs = import <nixpkgs> {}; lib = import <nixpkgs/lib>;})" +
        (f'.{attribute_prefix}' if attribute_prefix else '')
    )
    return nix_instantiate_eval(expr)
