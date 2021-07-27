import json
import subprocess
import functools
from string import Template

from nixui.utils.logger import LogPipe, logger
from nixui.utils import cache
from nixui.options.attribute import Attribute


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


def get_nixpkgs_version():
    return nix_instantiate_eval("with import <nixpkgs> {}; lib.version")


@functools.lru_cache()  # TODO: more efficient retain_hash_fn:  @cache(return_copy=True, retain_hash_fn=get_nixpkgs_version)
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
    # TODO: remove key from this expression, it isn't used
    res = nix_instantiate_eval(
        """
        with import <nixpkgs/nixos> {};
        builtins.mapAttrs
           (n: v: builtins.removeAttrs v ["default" "declarations"])
           (pkgs.nixosOptionsDoc { inherit options; }).optionsNix
        """,
        strict=True
    )
    d = {Attribute(v['loc']): v for v in res.values()}
    # TODO: convert system_default text into OptionDefinition via .from_expression_string
    return d


@cache.cache(return_copy=True, retain_hash_fn=cache.first_arg_path_hash_fn)
def get_modules_defined_attrs(module_path):
    leaves_expr_template = Template("""
let
  config = import ${module_path} {config = {}; pkgs = import <nixpkgs> {}; lib = import <nixpkgs/lib>;};
  closure = builtins.tail (builtins.genericClosure {
    startSet = [{ key = builtins.toJSON []; value = {value = config;}; }];
    operator = {key, value}: builtins.filter (x: x != null) (
      if
        builtins.isAttrs value.value
      then
        builtins.map (new_key:
          let
            pos = (builtins.unsafeGetAttrPos new_key value.value);
          in
            if
              builtins.isNull pos || (pos.file != builtins.toString "${module_path}")
            then null
            else {
              key = builtins.toJSON ((builtins.fromJSON key) ++ [new_key]);
              value = {
                value = builtins.getAttr new_key value.value;
                inherit pos;
              };
            }
        ) (builtins.attrNames value.value)
      else []
    );
  });
  leaves = builtins.filter (x: !(builtins.isAttrs x.value.value)) closure;
in
builtins.map (x: {name = builtins.fromJSON x.key; position = x.value.pos;}) leaves
    """)

    leaves = nix_instantiate_eval(leaves_expr_template.substitute(module_path=module_path), strict=True)

    return {
        Attribute(v['name']): {"position": v['position']}
        for v in leaves
    }


def eval_attribute(module_path, attribute):
    expr = (
        "(import " +
        module_path +
        " {config = {}; pkgs = import <nixpkgs> {}; lib = import <nixpkgs/lib>;})." +
        attribute
    )
    return nix_instantiate_eval(expr)


def eval_attribute_position(module_path, attribute):
    expr = (
        "builtins.unsafeGetAttrPos \"" +
        attribute.get_end() +
        "\" (import " +
        module_path +
        "{config = {}; pkgs = import <nixpkgs> {}; lib = import <nixpkgs/lib>;})" +
        (f'.{attribute.get_set()}' if attribute.get_set() else '')
    )
    return nix_instantiate_eval(expr)
