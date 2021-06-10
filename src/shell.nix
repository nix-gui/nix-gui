

let
  pkgs = import <nixpkgs> { };

  matplotlib = pkgs.python3Packages.matplotlib.override { enableQt = true; };


  rnix = pkgs.rustPlatform.buildRustPackage rec {
    pname = "rnix";
    version = "0.9.0";

    src = pkgs.fetchFromGitHub {
      owner = "nix-community";
      repo = "rnix-parser";
      rev = "83a0fcf6bffc75f87513061dfd83a8dbc809997d";
      sha256 = "059y30ysnmism5zsyp0a7klw4xz5n1bl1xkhdbfq5n74jv9shavw";
    };

    cargoPatches = [ ./rnix-cargo.lock ];
    cargoSha256 = "00gmcwavhc5sy8yy4im6l68fmf5cc1aj2lim9qidli9ivg1m4n84";

    #cargoLock = builtins.readFile ./Cargo.lock;

    installPhase = ''
      mkdir -p $out/source
      chmod -R +w $out/source
      cp -r ./* $out/source
      cp -r ${./Cargo.lock} $out/source/Cargo.lock
    '';
  };

  inputs = {
    rnix-lsp.url = github:nix-community/rnix-lsp;
  };

in
  pkgs.mkShell {
    buildInputs = [ matplotlib rnix pkgs.cargo pkgs.python3Packages.parsimonious ];
    runtimeDependencies = [rnix];

    RNIX_PARSER_PATH = "${rnix}/source";

    QT_PLUGIN_PATH = with pkgs.qt5; "${qtbase}/${qtbase.qtPluginPrefix}";
  }
