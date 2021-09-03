let
  inherit (import <nixpkgs> {}) pkgs lib;
in lib.makeExtensible (self: {
  collectDeclarationPositions = options: declarations:
    lib.concatMap
      (k: if ((options."${k}"._type or "") == "option")
          then [{loc = options."${k}".loc; position = builtins.unsafeGetAttrPos k declarations;}]
          else self.collectDeclarationPositions options."${k}" declarations."${k}")
      (builtins.attrNames declarations);

  evalModuleStub = module_path: import module_path { inherit lib; name = ""; config = {}; pkgs = {}; };

  get_all_nixos_options = let
    inherit (import <nixpkgs/nixos> { configuration = {}; }) options;
  in builtins.mapAttrs
    (n: v: builtins.removeAttrs v ["default" "declarations"])
    (pkgs.nixosOptionsDoc { inherit options; }).optionsNix;

  get_modules_defined_attrs = module_path: let
    inherit (self) collectDeclarationPositions evalModuleStub;

    nixos = import <nixpkgs/nixos> {configuration={};};

    config = builtins.removeAttrs (evalModuleStub module_path) ["imports"];
  in
    collectDeclarationPositions nixos.options config;

})
