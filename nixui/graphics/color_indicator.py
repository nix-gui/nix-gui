from PyQt5 import QtGui

from nixui.options.option_definition import OptionDefinition


def get_edit_state_color_indicator(tree, option_path):
    """
    Select color based on whether the option path or any child paths have been changed
    in_memory_definition: green
    configured_definition exists: yellow
    system_default_definition: white
    """
    undefined = OptionDefinition.undefined()

    configured_definition_exists = False
    in_memory_definition_exists = False

    for child_option_path, data in tree.children(option_path, mode="full").items():
        if data is None:
            continue
        if data.in_memory_definition != undefined:
            in_memory_definition_exists = True
            break
        if data.configured_definition != undefined:
            configured_definition_exists = True

    if in_memory_definition_exists:
        return QtGui.QColor(214, 253, 221)  # light green
    elif configured_definition_exists:
        return QtGui.QColor(245, 241, 197)  # yellow
    else:
        return QtGui.QColor(255, 255, 255)  # white
