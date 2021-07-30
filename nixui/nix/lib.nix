{ pkgs }:

let
  inherit (pkgs) lib;

  recursiveIntersect = xs: ys:
    builtins.mapAttrs (k: ys':
      let
        xs' = xs."${k}";
      in
        if (xs'._type or "") == "option"
        then { inherit (xs') loc; } // { position = builtins.unsafeGetAttrPos k ys; }
        else (recursiveIntersect xs' ys')
    ) ys;

  evalModuleStub = module_path: import module_path { inherit lib; name = ""; config = {}; pkgs = {}; };
in {
  inherit recursiveIntersect evalModuleStub;
}
