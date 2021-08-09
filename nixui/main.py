import argparse
import json
import os
import sys

from PyQt5 import QtWidgets

from nixui.graphics import main_window
from nixui import state_model


def handle_args():
    parser = argparse.ArgumentParser()
    parser._action_groups.pop()
    required = parser.add_argument_group('required arguments')
    optional = parser.add_argument_group('optional arguments')

    nixos_config = os.environ['NIX_PATH'].split(':')[2].split('=')[1]  # TODO: what is the clean way of getting NIX_PATH nixos-config value
    optional.add_argument(
        "-c",
        "--config-path",
        type=str,
        help="Directory containing impacted configuration file.",
        default=nixos_config,
    )
    optional.add_argument(
        "-n",
        "--no-diskcache",
        help="Cache function results to disk between sessions",
        action='store_true',
    )

    args = parser.parse_args()

    os.environ['CONFIGURATION_PATH'] = args.config_path
    os.environ['USE_DISKCACHE'] = json.dumps(not args.no_diskcache)


def run_program():
    statemodel = state_model.StateModel()

    app = QtWidgets.QApplication(sys.argv)
    nix_gui = main_window.NixGuiMainWindow(statemodel)
    nix_gui.show()
    sys.exit(app.exec())


def main():
    handle_args()
    run_program()


if __name__ == '__main__':
    main()
