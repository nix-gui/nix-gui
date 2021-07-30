module_path:
let
  lib = import <nixpkgs/lib>;
  nixos = import <nixpkgs/nixos> {configuration={};};

  # config-path = ./nixui/tests/sample/configuration.nix;

  config = builtins.removeAttrs (import module_path {config = {}; pkgs = import <nixpkgs> {}; lib = import <nixpkgs/lib>;}) ["imports"];

  recursiveIntersect = xs: ys:
    builtins.mapAttrs (k: ys':
      let
        xs' = xs."${k}";
      in
        if (xs'._type or "") == "option"
        then { inherit (xs') loc; } // { position = builtins.unsafeGetAttrPos k ys; }
        else (recursiveIntersect xs' ys')
    ) ys;
in
lib.collect (x: x ? loc) (recursiveIntersect nixos.options config)
