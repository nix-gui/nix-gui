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

        nix-dump-syntax-tree-json = with pkgs; rustPlatform.buildRustPackage rec {
           pname = "nix_dump_syntax_tree_json";
           version = "0.1.0";

           src = ./nix_dump_syntax_tree_json;
           cargoHash = "sha256-8yRlG8Paza3sE5GqhB8f0yzF8Pl0CI7F0W8VRhEN6BE=";
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
                pylspclient
                rnix-lsp.defaultPackage."${system}"
              ];
              makeWrapperArgs = [
                "--prefix PATH : ${pkgs.nixpkgs-fmt}/bin"
                "--prefix PATH : ${nix-dump-syntax-tree-json}/bin"
                "--set RUST_LOG trace"
                "--set QT_PLUGIN_PATH ${pkgs.qt5.qtbase}/${pkgs.qt5.qtbase.qtPluginPrefix}"
              ];

              checkInputs = [
                pkgs.nix
                pkgs.nixpkgs-fmt
                nix-dump-syntax-tree-json
                pkgs.python3Packages.pytest
                pkgs.python3Packages.pytest-datafiles
                pytest-profiling
              ];
              checkPhase = let
                sample = "${./nixui/tests/sample}";
              in ''
                export HOME=$TMPDIR
                export NIX_STATE_DIR=/build
                export NIX_PATH=nixpkgs=${pkgs.path}:nixos-config=${sample}/configuration.nix
                cd nixui
                python3 -m cProfile -o profile -m pytest
                python3 -c "import pstats; p = pstats.Stats('profile'); p.strip_dirs(); p.sort_stats('cumtime'); p.print_stats(50)"
              '';
            }) { };
        defaultPackage = self.packages.${system}.nix-gui;
        apps.nix-gui = flake-utils.lib.mkApp {
          drv = self.packages."${system}".nix-gui;
        };
        defaultApp = self.apps."${system}".nix-gui;
      }
    );
}
