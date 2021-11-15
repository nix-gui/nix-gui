from PyQt5 import QtWidgets

from nixui.graphics import option_display
from nixui.options import types

import pytest


SAMPLES_PATH = 'tests/sample'


@pytest.mark.slow
def test_integration_load_all_field_widgets(nix_gui_main_window):
    nav_interface = nix_gui_main_window.centralWidget()
    statemodel = nix_gui_main_window.statemodel

    def assert_legal_parent_type(type_obj):
        legal_types = (types.AnythingType, types.AttrsType, types.AttrsOfType, types.SubmoduleType, types.ListOfType)
        if type(type_obj) in legal_types:
            pass
        elif isinstance(type_obj, types.EitherType) and any([type(subtype) in legal_types for subtype in type_obj.subtypes]):
            pass
        else:
            raise Exception(type_obj)

    for attr in statemodel.option_tree.iter_attributes():
        print(type(attr), attr)

        nav_interface.set_option_path(attr)

        not_individual_option_display = (
            isinstance(nav_interface.fields_view.current_widget, QtWidgets.QLabel) or
            len(nav_interface.fields_view.current_widget.elements) != 1
        )
        if not_individual_option_display:
            assert_legal_parent_type(
                statemodel.option_tree.get_type(attr)
            )
            continue
        else:
            if isinstance(nav_interface.fields_view.current_widget.elements[0], option_display.GenericOptionDisplay):
                display = nav_interface.fields_view.current_widget.elements[0]
                if not display.is_defined_toggle.isChecked():
                    display.is_defined_toggle.setChecked(True)
