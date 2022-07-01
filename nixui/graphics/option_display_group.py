from PyQt5 import QtWidgets, QtCore

from nixui.options import api
from nixui.graphics import generic_widgets, option_display


class OptionDisplayGroupBox(QtWidgets.QWidget):
    def __init__(self, statemodel, set_option_path_fn, option=None, is_base_viewer=True, only_display_parent=False):
        super().__init__()

        self.elements = []

        group_box = QtWidgets.QGroupBox()

        if only_display_parent:
            option_paths = [option]
        else:
            option_paths = api.get_option_tree().children(option)

        if option_paths:
            group_box.setTitle(str(option))
        else:
            option_paths = [option]

        vbox = QtWidgets.QVBoxLayout()
        for child_option_path in option_paths:
            if not only_display_parent and len(api.get_option_tree().children(child_option_path)) > 1:
                fields_group_box = OptionDisplayGroupBox(
                    statemodel,
                    set_option_path_fn,
                    child_option_path,
                    is_base_viewer=False
                )
                self.elements.append(fields_group_box)
                vbox.addWidget(fields_group_box)
            else:
                option_disp = option_display.GenericOptionDisplay(
                    statemodel,
                    set_option_path_fn,
                    child_option_path
                )
                self.elements.append(option_disp)
                vbox.addWidget(option_disp)
            vbox.addWidget(generic_widgets.SeparatorLine())

        if is_base_viewer:
            vbox.addStretch()
        group_box.setLayout(vbox)

        lay = QtWidgets.QHBoxLayout()
        if is_base_viewer:
            scroll_area = QtWidgets.QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            lay.addWidget(scroll_area)
            scroll_area.setWidget(group_box)
        else:
            lay.addWidget(group_box)

        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        self.setLayout(lay)
