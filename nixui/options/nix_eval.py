import json
import subprocess

from nixui.utils.logger import LogPipe, logger
from nixui.utils.cache import cache
from string import Template


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


@cache(return_copy=True, retain_hash_fn=get_nixpkgs_version)
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
    return nix_instantiate_eval("""
        with import <nixpkgs/nixos> {};
        builtins.mapAttrs
           (n: v: builtins.removeAttrs v ["default" "declarations"])
           (pkgs.nixosOptionsDoc { inherit options; }).optionsNix
    """,
        strict=True
    )


def get_modules_defined_attrs(module_path, attr_loc=[]):
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
        tuple(v['name']): {"position": v['position']}
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
