module_path:
attribute:

let
  module = import module_path {config = {}; pkgs = import <nixpkgs> {}; lib = import <nixpkgs/lib>;}
in
builtins.getAttr attribute module
