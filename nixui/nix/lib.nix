let
  inherit (import <nixpkgs> {}) pkgs lib;
in lib.makeExtensible (self: {
  recursiveIntersect = xs: ys:
    builtins.mapAttrs (k: ys':
      let
        xs' = xs."${k}";
      in
        if (xs'._type or "") == "option"
        then { inherit (xs') loc; } // { position = builtins.unsafeGetAttrPos k ys; }
        else (self.recursiveIntersect xs' ys')
    ) ys;

  evalModuleStub = module_path: import module_path { inherit lib; name = ""; config = {}; pkgs = {}; };

  get_all_nixos_options = let
    inherit (import <nixpkgs/nixos> { configuration = {}; }) options;
  in builtins.mapAttrs
    (n: v: builtins.removeAttrs v ["default" "declarations"])
    (pkgs.nixosOptionsDoc { inherit options; }).optionsNix;

  get_modules_defined_attrs = module_path: let
    inherit (self) recursiveIntersect evalModuleStub;

    nixos = import <nixpkgs/nixos> {configuration={};};

    config = builtins.removeAttrs (evalModuleStub module_path) ["imports"];
  in
    lib.collect (x: x ? loc) (recursiveIntersect nixos.options config);

})
