let
  inherit (import <nixpkgs> {}) pkgs lib;
in lib.makeExtensible (self: {
  /* Recurse through the declaration tree of a module collecting
     the positions of the declarations within the module

     Type:
       collectDeclarationPositions ::
         AttrSet -> AttrSet -> [{ loc = [String]; position = Position; }]
  */
  collectDeclarationPositions = {module_path, declarations, option_path ? []}:
    lib.concatMap
      # If we can get the children of declaration (isAttrs) and they're within the same module, recurse
      (k:
        let
          pos = builtins.unsafeGetAttrPos k declarations;
          sub_path = option_path ++ [k];
        in
          if (pos.file or "") == module_path
          then (
            [{loc = sub_path; position = pos;}] ++ (
                if builtins.isAttrs declarations."${k}"
                then self.collectDeclarationPositions {
                  module_path = module_path;
                  declarations = declarations."${k}";
                  option_path = sub_path;
                }
                else []
              )
          )
          else []
      )
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
          inherit pkgs;
          name = "";
          config = {};
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

    config = builtins.removeAttrs (evalModuleStub module_path) ["imports"];

    # TODO: find a better way of getting module path
    hacked_module_path = (builtins.unsafeGetAttrPos (builtins.elemAt (builtins.attrNames config) 0) config).file;
  in
    collectDeclarationPositions {module_path = hacked_module_path; declarations = config;};

})
