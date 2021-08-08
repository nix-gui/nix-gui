import argparse
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

    args = parser.parse_args()

    os.environ['CONFIGURATION_PATH'] = args.config_path


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
