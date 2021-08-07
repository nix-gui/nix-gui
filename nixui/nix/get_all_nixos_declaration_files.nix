with import <nixpkgs/nixos> {configuration={};};

let
  inherit (pkgs) lib;

  inherit (import ./lib.nix { inherit pkgs; }) uniqueStrings;
in
uniqueStrings (
  builtins.map (x: x.declarations)
    (lib.collect
      (x: (x._type or "") == "option")
      options)
)
