module_path:
let
  pkgs = import <nixpkgs> {};
  inherit (pkgs) lib;

  inherit (import ./lib.nix { inherit pkgs; }) recursiveIntersect evalModuleStub;

  nixos = import <nixpkgs/nixos> {configuration={};};

  config = builtins.removeAttrs (evalModuleStub module_path) ["imports"];
in
lib.collect (x: x ? loc) (recursiveIntersect nixos.options config)
