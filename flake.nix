{
  description = "Nix Configuration GUI";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs";
    flake-utils.url = "github:numtide/flake-utils";
    rnix-parser.url = "github:nix-community/rnix-parser";
  };

  outputs = { self, nixpkgs, rnix-parser, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
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
                rnix-parser
              ];
              makeWrapperArgs = [ "--set RUST_LOG trace" ];
            }) { };
        defaultPackage = self.packages.${system}.nix-gui;
        apps.nix-gui = flake-utils.lib.mkApp {
          drv = self.packages."${system}".nix-gui;
        };
        defaultApp = self.apps."${system}".nix-gui;
      }
    );
}
