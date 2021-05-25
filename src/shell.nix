let
  pkgs = import <nixpkgs> { };

  matplotlib = pkgs.python3Packages.matplotlib.override { enableQt = true; };

in
  pkgs.mkShell {
    buildInputs = [ matplotlib ];

    QT_PLUGIN_PATH = with pkgs.qt5; "${qtbase}/${qtbase.qtPluginPrefix}";

    #shellHook = "python gui.py";
  }
