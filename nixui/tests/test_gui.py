import json
import os

import pytest

from nixui.graphics import main_window
from nixui import state_model


SAMPLES_PATH = 'tests/sample'


@pytest.mark.slow
def test_integration_load_all_field_widgets(nix_gui_main_window):
    nav_interface = nix_gui_main_window.centralWidget()
    statemodel = nix_gui_main_window.statemodel

    for attr, _ in statemodel.option_tree.iter_attribute_data():
        nav_interface.set_option_path(attr)


def test_set_module_loads(qtbot):
    os.environ['CONFIGURATION_PATH'] = os.path.abspath(os.path.join(SAMPLES_PATH, 'set_configuration.nix'))
    os.environ['USE_DISKCACHE'] = json.dumps(False)

    statemodel = state_model.StateModel()

    nix_gui_mw = main_window.NixGuiMainWindow(statemodel)
    yield nix_gui_mw
    nix_gui_mw.close()
