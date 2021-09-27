import json
import subprocess
import functools
import pkgutil
from contextlib import contextmanager
from string import Template

from nixui.utils.logger import logger
from nixui.utils import cache
from nixui.options.attribute import Attribute


cache_by_unique_installed_nixos_nixpkgs_version = cache.cache(
    lambda: nix_instantiate_eval("with import <nixpkgs/nixos> { configuration = {}; }; pkgs.lib.version")
)


class NixEvalError(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__([self.msg])

    def __str__(self):
        return f'NixEvalError("""\n{self.msg}\n""")'


def nix_instantiate_eval(expr, strict=False, show_trace=False, retry_show_trace_on_error=True):
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
    if show_trace:
        cmd.append('--show-trace')

    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out, err = p.communicate()

    if out:
        return json.loads(out)
    else:
        if retry_show_trace_on_error and not show_trace:
            return nix_instantiate_eval(expr, strict, show_trace=True)
        else:
            try:
                err_str = err.decode('utf-8')
            except:  # TODO: appropriate decode error
                err_str = err.decode('ISO-8859-1')
            raise NixEvalError(err_str)


@contextmanager
def find_library(name):
    expr = pkgutil.get_data('nixui', 'nix/lib.nix')
    yield f'(import {expr}).{name}'


@cache_by_unique_installed_nixos_nixpkgs_version
def get_all_nixos_options():
    """
    Get a JSON representation of `<nixpkgs/nixos>` options.
    The schema is as follows:
    {
      "option.name": {
        "description": String              # description declared on the option
        "loc": [ String ]                  # the path of the option e.g.: [ "services" "foo" "enable" ]
        "readOnly": Bool                   # is the option user-customizable?
        "type": String                     # either "boolean", "set", "list", "int", "float", or "string"
        "relatedPackages": Optional, XML   # documentation for packages related to the option
      }
    }
    """
    with find_library('get_all_nixos_options') as fn:
        res = nix_instantiate_eval(fn, strict=True)
    # TODO: remove key from this expression, it isn't used
    return {Attribute(v['loc']): v for v in res.values()}


@cache.cache(return_copy=True, retain_hash_fn=cache.first_arg_path_hash_fn)
def get_modules_defined_attrs(module_path):
    with find_library('get_modules_defined_attrs') as fn:
        leaves = nix_instantiate_eval(f'{fn} {module_path}', strict=True)

    return {
        Attribute(v['loc']): {"position": v['position']}
        for v in leaves
    }


@cache.cache(return_copy=True, retain_hash_fn=cache.first_arg_path_hash_fn)
def get_modules_import_position(module_path):
    # TODO: should be part of lib.nix
    expression = f"""
    builtins.unsafeGetAttrPos "imports"
    (import {module_path} {{
      config = {{}};
      pkgs = import <nixpkgs> {{}};
      lib = {{}};
      modulesPath = builtins.dirOf {module_path};
    }})
    """
    return nix_instantiate_eval(expression, strict=True)
