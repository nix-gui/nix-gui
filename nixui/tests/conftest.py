import os
import json

import pytest

from nixui.graphics import main_window
from nixui import state_model


SAMPLES_PATH = 'tests/sample'


def pytest_addoption(parser):
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


@pytest.fixture
def nix_gui_main_window(qtbot):
    os.environ['CONFIGURATION_PATH'] = os.path.abspath(os.path.join(SAMPLES_PATH, 'configuration.nix'))

    statemodel = state_model.StateModel()

    nix_gui_mw = main_window.NixGuiMainWindow(statemodel)
    yield nix_gui_mw
    nix_gui_mw.close()


@pytest.fixture
def option_tree():
    os.environ['CONFIGURATION_PATH'] = os.path.abspath(os.path.join(SAMPLES_PATH, 'configuration.nix'))
    statemodel = state_model.StateModel()
    return statemodel.option_tree
