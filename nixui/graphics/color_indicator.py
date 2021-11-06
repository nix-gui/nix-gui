from PyQt5 import QtGui

from nixui.options.option_definition import OptionDefinition


def get_edit_state_color_indicator(tree, option_path):
    """
    Select color based on whether the option path or any child paths have been changed
    in_memory_definition: green
    configured_definition exists: yellow
    system_default_definition: white
    """
    # TODO use icons to diff memory/configuration definition change
    # in memory definition change
    if option_path in tree.get_change_set_with_ancestors():
        return QtGui.QPalette().color(QtGui.QPalette().Highlight)
    # in configuration definition change
    elif option_path in tree.get_change_set_with_ancestors(get_configured_changes=True):
        return QtGui.QPalette().color(QtGui.QPalette().Highlight)
    else:
        return QtGui.QPalette().color(QtGui.QPalette().Window)
