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
        python = pkgs.python39;
        pythonPackages = python.pkgs;

        nix-dump-syntax-tree-json = with pkgs; rustPlatform.buildRustPackage rec {
           pname = "nix_dump_syntax_tree_json";
           version = "0.1.1";

           src = ./nix_dump_syntax_tree_json;
           cargoHash = "sha256-msKFtspM7PhjhIE5HrApXh2HnEW4KolJayyoY44qbgA=";
        };

        pylspclient = pythonPackages.buildPythonPackage rec {
          pname = "pylspclient";
          version = "0.0.2";
          name = "${pname}-${version}";
          src = builtins.fetchurl {
            url = "https://files.pythonhosted.org/packages/ab/51/d9152f2d86bf8cc2a1dc59be7f9bb771933e26e21e0e96a2bee2547e4a37/pylspclient-0.0.2.tar.gz";
            sha256 = "0ddsf1wx2nq0k80sqsc0q82qd0xhw90z0l791j78fbirfl9gz086";
          };
          doCheck = false;
        };
        treelib = pythonPackages.buildPythonPackage rec {
          pname = "treelib";
          version = "1.6.1";
          name = "${pname}-${version}";
          src = builtins.fetchurl {
            url = "https://files.pythonhosted.org/packages/04/b0/2269c328abffbb63979f7143351a24a066776b87526d79956aea5018b80a/treelib-1.6.1.tar.gz";
            sha256 = "1247rv9fbb8pw3xbkbz04q3vnvvva3hcw002gp1clp5psargzgqw";
          };
          propagatedBuildInputs = [
            pythonPackages.future
          ];
          doCheck = false;
        };

      in {
        packages.nix-gui = pkgs.callPackage
          ({ stdenv, lib, rustPlatform, fetchFromGitHub, enable-profiling ? false }:
            pythonPackages.buildPythonPackage rec {
              pname = "nix-gui";
              version = "0.1.0";
              src = ./.;
              propagatedBuildInputs = [
                pythonPackages.pyqt5
                pythonPackages.pypandoc
                pylspclient
                treelib
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
                pythonPackages.pytest
                pythonPackages.pytest-env
                pythonPackages.pytest-datafiles
                pythonPackages.pytest-mock
                pythonPackages.pytest-qt
              ];
              checkPhase = let
                sample = "${./nixui/tests/sample}";
              in ''
                export QT_QPA_PLATFORM=offscreen
                export QT_PLUGIN_PATH="${pkgs.qt5.qtbase}/${pkgs.qt5.qtbase.qtPluginPrefix}"
                export XDG_RUNTIME_DIR=$NIX_BUILD_TOP

                export HOME=$NIX_BUILD_TOP
                export NIX_STATE_DIR=$NIX_BUILD_TOP
                export NIX_PATH=${pkgs.path}:nixpkgs=${pkgs.path}:nixos-config=${sample}/configuration.nix
                cd nixui
              '' + (if !enable-profiling then ''
                python3 -m pytest -vv
              '' else ''
                python3 -m cProfile -o profile -m pytest
                python3 -c "import pstats; p = pstats.Stats('profile'); p.strip_dirs(); p.sort_stats('cumtime'); p.print_stats(50)"
              '');
            }) { };
        packages.scrape-github = pkgs.callPackage
          ({ stdenv, lib}:
            pythonPackages.buildPythonPackage rec {
              pname = "scrape-github";
              version = "0.1.0";
              src = ./.;
              propagatedBuildInputs = [
                pythonPackages.PyGithub
              ];
              makeWrapperArgs = [
                "--prefix PATH : ${nix-dump-syntax-tree-json}/bin"
              ];
              doCheck = false;
            }) { };
        checks.profile = self.packages.${system}.nix-gui.override { enable-profiling = true; };
        defaultPackage = self.packages.${system}.nix-gui;
        apps = {
          nix-gui = flake-utils.lib.mkApp {
            drv = self.packages."${system}".nix-gui;
          };
          /*
          # DONT ENABLE UNTIL VIRTUAL MACHINE IS SETUP
          scrape-github = flake-utils.lib.mkApp {
            drv = self.packages."${system}".scrape-github;
          };
          */
        };
        defaultApp = self.apps."${system}".nix-gui;

        devShell = pkgs.mkShell {
          QT_PLUGIN_PATH = "${pkgs.qt5.qtbase}/${pkgs.qt5.qtbase.qtPluginPrefix}";
          nativeBuildInputs = [
            python
          ];
          inputsFrom = [
            self.packages."${system}".nix-gui
          ];
        };
      }
    );
}
