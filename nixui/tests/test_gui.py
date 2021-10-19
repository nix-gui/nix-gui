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
