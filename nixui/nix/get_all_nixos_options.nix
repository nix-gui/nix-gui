with import <nixpkgs/nixos> {configuration={};};
let
  extractPassedOptionAttrs = option: (builtins.mapAttrs (n: _: builtins.unsafeGetAttrPos n option) (builtins.removeAttrs option ["_type"])) // {
    inherit (option) loc;
    type = option.type.description;
  };

  inherit (pkgs.lib) collect isOption isFunction mapAttrs optionalAttrs;
in
builtins.map extractPassedOptionAttrs (collect isOption options)
