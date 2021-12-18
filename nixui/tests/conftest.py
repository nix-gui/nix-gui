import os
from distutils.dir_util import copy_tree
import time

import pytest

from nixui.graphics import main_window
from nixui import state_model
from nixui.options.option_tree import OptionTree
from nixui.options.attribute import Attribute


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


class Helpers:
    class timeout(object):
        def __init__(self, seconds):
            self.seconds = seconds
        def __enter__(self):
            self.die_after = time.time() + self.seconds
            return self
        def __exit__(self, type, value, traceback):
            pass
        @property
        def timed_out(self):
            return time.time() > self.die_after


@pytest.fixture
def helpers():
    return Helpers

@pytest.fixture
def samples_path(tmpdir):
    copy_tree(SAMPLES_PATH, str(tmpdir))
    return tmpdir


@pytest.fixture
def statemodel(samples_path):
    os.environ['CONFIGURATION_PATH'] = os.path.abspath(os.path.join(samples_path, 'configuration.nix'))
    return state_model.StateModel()


@pytest.fixture
def nix_gui_main_window(statemodel, qtbot):
    nix_gui_mw = main_window.NixGuiMainWindow(statemodel)
    yield nix_gui_mw
    nix_gui_mw.close()


@pytest.fixture
def option_tree():
    os.environ['CONFIGURATION_PATH'] = os.path.abspath(os.path.join(SAMPLES_PATH, 'configuration.nix'))
    statemodel = state_model.StateModel()
    return statemodel.option_tree


@pytest.fixture
def minimal_option_tree():
    return OptionTree(
        {
            Attribute('myList'): {'type_string': 'list of strings'},
            Attribute('myAttrs'): {'type_string': 'attribute set of submodules'},
            Attribute('myAttrs."<name>"'): {},
        },
        {}
    )


@pytest.fixture
def minimal_state_model(mocker, minimal_option_tree):
    mocker.patch('nixui.state_model.api.get_option_tree', return_value=minimal_option_tree)
    return state_model.StateModel()
