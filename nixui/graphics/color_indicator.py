from PyQt5 import QtGui


def get_edit_state_color_indicator(tree, option_path):
    """
    Select color based on whether the option path or any child paths have been changed
    in_memory_definition: green
    configured_definition exists: yellow
    system_default_definition: white
    """
    # in memory definition change
    if option_path in tree.get_change_set_with_ancestors():
        return QtGui.QColor(150, 255, 150)  # green
    # in configuration definition change
    elif option_path in tree.get_change_set_with_ancestors(get_configured_changes=True):
        return QtGui.QColor(255, 233, 0)  # yellow
    else:
        return None
