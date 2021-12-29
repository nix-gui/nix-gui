# Run Tests

(outside development environment)

``` bash
$ nix flake check
```

bash

# Smoke Test Dark Theme

(outside development environment)

``` bash
$  nix-shell -p libsForQt5.qtstyleplugin-kvantum --run "QT_STYLE_OVERRIDE=kvantum-dark nix run nix-gui
```

bash

# Development Enviornment

All commands in this section take place in the environment created by
the below subsections commmand.

## Create a Development Environment

``` bash
$ nix develop
```

bash

## Run Nix-Gui

``` bash
$ python -m nixui.main --help
```

bash

## Run a Single Test

``` bash
$ pytest -svv nixui/tests/test_parser.py::test_sane_placement  # run verbosely
```

bash
