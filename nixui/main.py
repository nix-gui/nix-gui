import argparse
import cProfile
import pstats
import json
import os
import sys

from PyQt5 import QtWidgets

from nixui.graphics import main_window
from nixui import state_model


def get_nixos_config_path(nix_path=os.environ['NIX_PATH']):
    nixos_configs = [elem for elem in nix_path.split(':') if elem.startswith('nixos-config=')]
    assert len(nixos_configs) <= 1, 'more than one nixos-config defined in NIX_PATH'
    assert len(nixos_configs) > 0, 'no nixos-config defined in NIX_PATH'
    return nixos_configs[0].removeprefix('nixos-config=')

def handle_args():
    parser = argparse.ArgumentParser()
    parser._action_groups.pop()
    required = parser.add_argument_group('required arguments')
    optional = parser.add_argument_group('optional arguments')

    nixos_config = get_nixos_config_path()
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
        help="Cache function results to disk between sessions.",
        action='store_true',
    )
    optional.add_argument(
        "-p",
        "--profile",
        help="Profile application.",
        action='store_true',
    )

    return parser.parse_args()


def run_program():
    statemodel = state_model.StateModel()

    app = QtWidgets.QApplication(sys.argv)
    nix_gui = main_window.NixGuiMainWindow(statemodel)
    nix_gui.show()
    app.exec()


def main():
    args = handle_args()

    os.environ['CONFIGURATION_PATH'] = args.config_path
    os.environ['USE_DISKCACHE'] = json.dumps(not args.no_diskcache)

    if args.profile:
        with cProfile.Profile() as profile:
            run_program()
        p = pstats.Stats(profile)
        p.strip_dirs()
        p.sort_stats('cumtime')
        p.print_stats(50)
    else:
        run_program()


if __name__ == '__main__':
    main()
