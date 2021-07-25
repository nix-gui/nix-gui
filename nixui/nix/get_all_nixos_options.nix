with import <nixpkgs/nixos> {};
builtins.mapAttrs
  (n: v: builtins.removeAttrs v ["default" "declarations"])
  (pkgs.nixosOptionsDoc { inherit options; }).optionsNix
