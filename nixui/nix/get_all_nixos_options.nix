with import <nixpkgs/nixos> {configuration={};};
builtins.mapAttrs
  (n: v: builtins.removeAttrs v ["default" "declarations"])
  (pkgs.nixosOptionsDoc { inherit options; }).optionsNix
