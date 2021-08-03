from PyQt5 import QtWidgets, QtCore

from nixui.options import api
from nixui.options.attribute import Attribute

from nixui.graphics import generic_widgets, navbar, navlist, field_widgets


class OptionNavigationInterface(QtWidgets.QWidget):
    def __init__(self, statemodel, starting_option_path=Attribute()):
        super().__init__()

        self.statemodel = statemodel

        # widgets
        self.nav_bar = generic_widgets.ReplacableWidget()
        self.nav_list = generic_widgets.ReplacableWidget()
        self.fields_view = generic_widgets.ReplacableWidget()

        # layout: flat nav bar on top, below is option list on left, option display stack on right
        hbox = QtWidgets.QHBoxLayout()
        hbox.setSpacing(0)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(self.nav_list, 1)
        hbox.addWidget(self.fields_view, 2)

        nav_hbox = QtWidgets.QHBoxLayout()
        nav_hbox.setSpacing(0)
        nav_hbox.setContentsMargins(0, 0, 0, 0)

        # hack to make nav bar left aligned taking 1/3rd of window
        nav_hbox.addWidget(self.nav_bar, 1)
        nav_hbox.addWidget(QtWidgets.QLabel(''), 2)

        vbox = QtWidgets.QVBoxLayout()
        vbox.setSpacing(0)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.addLayout(nav_hbox, 0)
        vbox.addLayout(hbox, 1)

        self.setLayout(vbox)

        self.set_option_path(starting_option_path)

    def set_option_path(self, option_path):
        self.nav_bar.replace_widget(
            navbar.NavBar(option_path, self.set_option_path)
        )
        # if 10 or fewer options, navlist with lowest level attribute selected and list of editable fields to the right
        # otherwise, show list of attributes within the clicked attribute and blank to the right
        num_children = len(api.get_option_tree().children(option_path, recursive=True))
        if num_children <= 10:
            self.nav_list.replace_widget(
                navlist.GenericNavListDisplay(
                    self.statemodel,
                    option_path.get_set(),
                    self.set_option_path,
                    selected=option_path.get_end()
                )
            )
            if num_children == 1:
                self.fields_view.replace_widget(
                    field_widgets.GenericOptionDisplay(
                        self.statemodel,
                        option_path
                    )
                )
            else:
                self.fields_view.replace_widget(
                    FieldsGroupBox(
                        self.statemodel,
                        option_path
                    )
                )
        else:
            self.nav_list.replace_widget(
                navlist.GenericNavListDisplay(
                    self.statemodel,
                    option_path,
                    self.set_option_path,
                )
            )
            self.fields_view.replace_widget(QtWidgets.QLabel(''))


class FieldsGroupBox(QtWidgets.QWidget):
    def __init__(self, statemodel, option=None, is_base_viewer=True, *args, **kwargs):
        super().__init__(*args, **kwargs)

        group_box = QtWidgets.QGroupBox()
        group_box.setTitle(str(option))

        vbox = QtWidgets.QVBoxLayout()

        for child_option_path in api.get_option_tree().children(option):
            if len(api.get_option_tree().children(child_option_path, recursive=True)) > 1:
                vbox.addWidget(FieldsGroupBox(
                    statemodel,
                    child_option_path,
                    is_base_viewer=False
                ))
            else:
                vbox.addWidget(field_widgets.GenericOptionDisplay(
                    statemodel,
                    child_option_path
                ))
            vbox.addWidget(generic_widgets.SeparatorLine())

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

        self.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
