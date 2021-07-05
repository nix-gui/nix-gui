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

    return {
        tuple(v['name']): {"position": v['position']}
        for v in nix_instantiate_eval("""
let
  config = import <nixos-config> {config = {}; pkgs = import <nixpkgs> {}; lib = import <nixpkgs/lib>;};
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
              builtins.isNull pos || (pos.file != builtins.toString <nixos-config>)
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
          """, strict=True)
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
