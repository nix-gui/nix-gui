import pytest

from nixui.options.attribute import Attribute


@pytest.mark.slow
def test_integration_load_option_fields(nix_gui_main_window):
    nav_interface = nix_gui_main_window.centralWidget()
    statemodel = nix_gui_main_window.statemodel

    for i, (attr, _) in enumerate(statemodel.option_tree.iter_attribute_data()):
        nav_interface.set_option_path(attr)
