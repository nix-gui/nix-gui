module_path:
let
  pkgs = import <nixpkgs> {};
  inherit (pkgs) lib;

  inherit (import ./lib.nix { inherit pkgs; }) recursiveIntersect evalModuleStub;

  nixos = import <nixpkgs/nixos> {configuration={};};

  options = (import module_path {
    inherit pkgs;
    config = {};
    lib = import <nixpkgs/lib>;
    utils = import <nixpkgs/nixos/utils.nix> pkgs;
  }).options;
in
lib.collect (x: x ? loc) (recursiveIntersect nixos.options options)
