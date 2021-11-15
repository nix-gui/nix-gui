import json
import subprocess
import functools
import importlib.resources
from contextlib import contextmanager
from string import Template
import os
import sys

from nixui.utils.logger import logger
from nixui.utils import cache
from nixui.options.attribute import Attribute

env_nix_instantiate = os.environ.copy()
env_nix_instantiate["NIXPKGS_ALLOW_UNFREE"] = "1"
# note: we dont install unfree pkgs, just get the metadata
# fix parse error when NIXPKGS_ALLOW_UNFREE=0

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

    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env_nix_instantiate,
    )
    out, err = p.communicate()

    if p.returncode == 0:
        try:
            return json.loads(out)
        except json.decoder.JSONDecodeError as e:
            logger.error(f"Failed to decode output:\n{out}")
            raise e
    else:
        if retry_show_trace_on_error and not show_trace:
            return nix_instantiate_eval(expr, strict, show_trace=True)
        else:
            logger.debug(f"nix-instantiate -> returncode {p.returncode}, len(out) {len(out)}")
            try:
                err_str = err.decode('utf-8')
            except UnicodeDecodeError:
                err_str = repr(err)
            raise NixEvalError(err_str)


@contextmanager
def find_library(name):
    with importlib.resources.path('nixui.nix', 'lib.nix') as f:
        yield f'(import {f}).{name}'


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
    """
    Get a JSON representation of the modules attributes and positions.
    Schema is:
    list of dicts containing
    - "loc": [ String ]  # the path of the option e.g.: [ "services" "foo" "enable" ]
    - "position" :       # dict containing "column", "line" and "file" (path) of option (see `unsafeGetAttrPos`)
    """
    with find_library('get_modules_defined_attrs') as fn:
        leaves = nix_instantiate_eval(f'{fn} {module_path}', strict=True)

    # if descendant and ancestor have same position (e.g. `boot.initrd` and `boot`) only keep the child
    position_loc_map = {}
    for leaf in leaves:
        attr = Attribute(leaf['loc'])
        position_tuple = (leaf['position']['column'], leaf['position']['line'], leaf['position']['file'])
        if position_tuple in position_loc_map:
            if position_loc_map[position_tuple].startswith(attr):
                pass
            elif attr.startswith(position_loc_map[position_tuple]):
                position_loc_map[position_tuple] = attr
            else:
                raise ValueError(f'{position_loc_map[position_tuple]} and {attr} have same position, but incompatible paths')
        else:
            position_loc_map[position_tuple] = attr

    return {
        Attribute(v['loc']): {"position": v['position']}
        for v in leaves
        if Attribute(v['loc']) in position_loc_map.values()
    }



@cache.cache(return_copy=True, retain_hash_fn=cache.first_arg_path_hash_fn)
def get_modules_import_position(module_path):
    with find_library('evalModuleStub') as fn:
        return nix_instantiate_eval(f'builtins.unsafeGetAttrPos "imports" ({fn} {module_path})', strict=True)
