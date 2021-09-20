import pytest

import json
import os
import random

from PyQt5 import QtWidgets

from nixui.graphics import main_window
from nixui.options.attribute import Attribute
from nixui import state_model


SAMPLES_PATH = 'tests/sample'


@pytest.mark.datafiles(SAMPLES_PATH)
def test_integration_load_option_fields(qtbot):
    os.environ['CONFIGURATION_PATH'] = os.path.abspath(os.path.join(SAMPLES_PATH, 'configuration.nix'))
    os.environ['USE_DISKCACHE'] = json.dumps(False)

    statemodel = state_model.StateModel()

    nix_gui = main_window.NixGuiMainWindow(statemodel)
    nav_interface = nix_gui.centralWidget()

    for attr, _ in random.sample(list(statemodel.option_tree.iter_attribute_data()), 1000):
        print(attr)
        nav_interface.set_option_path(attr)
