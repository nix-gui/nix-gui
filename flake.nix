{
  description = "Nix Configuration GUI";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
    rnix-lsp.url = "github:nix-community/rnix-lsp";
  };

  outputs = { self, nixpkgs, rnix-lsp, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        rnix = with pkgs; rustPlatform.buildRustPackage rec {
           pname = "rnix";
           version = "0.9.0";

           src = fetchCrate {
             inherit pname version;
             sha256 = "sha256-xtfTAREOY8kc/DMSm+rtMDoyxrPiYNPXBEtYdrGgWgc=";
           };

           cargoSha256 = "sha256-n65YyV0KGA55Z9vYhyQ4XNOWKRfpbgZ18rgJLYygT+Q=";
           cargoBuildFlags = [ "--example" "dump-ast" ];

           postInstall = ''
            mkdir -p $out/bin
            cp target/${rust.toRustTargetSpec stdenv.hostPlatform}/$cargoBuildType/examples/dump-ast $out/bin
          '';
        };

        pylspclient = pkgs.python3Packages.buildPythonPackage rec {
          pname = "pylspclient";
          version = "0.0.2";
          name = "${pname}-${version}";
          src = builtins.fetchurl {
            url = "https://files.pythonhosted.org/packages/ab/51/d9152f2d86bf8cc2a1dc59be7f9bb771933e26e21e0e96a2bee2547e4a37/pylspclient-0.0.2.tar.gz";
            sha256 = "0ddsf1wx2nq0k80sqsc0q82qd0xhw90z0l791j78fbirfl9gz086";
          };
          doCheck = false;
        };

      in {
        packages.nix-gui = pkgs.callPackage
          ({ stdenv, lib, rustPlatform, fetchFromGitHub }:
            pkgs.python3Packages.buildPythonPackage rec {
              pname = "nix-gui";
              version = "0.1.0";
              src = ./.;
              propagatedBuildInputs = [
                pkgs.python3Packages.pyqt5
                pkgs.python3Packages.parsimonious
                pylspclient
                rnix-lsp.defaultPackage."${system}"
              ];
              makeWrapperArgs = [
                "--prefix PATH : ${rnix}/bin"
                "--set RUST_LOG trace"
                "--set QT_PLUGIN_PATH ${pkgs.qt5.qtbase}/${pkgs.qt5.qtbase.qtPluginPrefix}"
              ];

              checkInputs = [
                pkgs.python3Packages.pytest
                pkgs.python3Packages.pytest-datafiles
              ];
              checkPhase = "cd nixui && pytest";
            }) { };
        defaultPackage = self.packages.${system}.nix-gui;
        apps.nix-gui = flake-utils.lib.mkApp {
          drv = self.packages."${system}".nix-gui;
        };
        defaultApp = self.apps."${system}".nix-gui;
      }
    );
}
