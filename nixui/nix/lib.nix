let
  inherit (import <nixpkgs> {}) pkgs lib;
in lib.makeExtensible (self: {
  /* Recurse through the option tree and declaration tree of a module
     in parallel, collecting the positions of the declarations in the
     module

     Type:
       collectDeclarationPositions ::
         AttrSet -> AttrSet -> [{ loc = [String]; position = Position; }]
  */
  collectDeclarationPositions = options: declarations:
    lib.concatMap
      (k: if ((options."${k}"._type or "") == "option")
          then [{loc = options."${k}".loc; position = builtins.unsafeGetAttrPos k declarations;}]
          else self.collectDeclarationPositions options."${k}" declarations."${k}")
      (builtins.attrNames declarations);

  /* Extract the declarations of a module
  */
  evalModuleStub = module_path:
    let
      m = import module_path;
    in
      if builtins.isFunction m then
        m {
          inherit lib;
          name = "";
          config = {};
          pkgs = {};
          modulesPath = builtins.dirOf module_path;
        }
      else m;

  /* Get all NixOS options as a list of options with the following schema:
    {
      "option.name": {
        "description": String              # description declared on the option
        "loc": [ String ]                  # the path of the option e.g.: [ "services" "foo" "enable" ]
        "readOnly": Bool                   # is the option user-customizable?
        "type": String                     # either "boolean", "set", "list", "int", "float", or "string"
        "relatedPackages": Optional, XML   # documentation for packages related to the option
      }
    }
  */
  get_all_nixos_options = let
    inherit (import <nixpkgs/nixos> { configuration = {}; }) options;
  in builtins.mapAttrs
    (n: v: builtins.removeAttrs v ["default" "declarations"])
    (pkgs.nixosOptionsDoc { inherit options; }).optionsNix;

  /* Extract all positions of the declarations in a module
  */
  get_modules_defined_attrs = module_path: let
    inherit (self) collectDeclarationPositions evalModuleStub;

    nixos = import <nixpkgs/nixos> {configuration={};};

    config = builtins.removeAttrs (evalModuleStub module_path) ["imports"];
  in
    collectDeclarationPositions nixos.options config;

})
