from PyQt5 import QtWidgets, QtCore

from nixui.options import api, types
from nixui.options.attribute import Attribute
from nixui.graphics import generic_widgets, navbar, navlist, option_display
from nixui.utils.logger import logger


class OptionNavigationInterface(QtWidgets.QWidget):
    def __init__(self, statemodel, starting_lookup_key='options:'):
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

        vbox = QtWidgets.QVBoxLayout()
        vbox.setSpacing(0)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.addWidget(self.nav_bar, 0)
        vbox.addLayout(hbox, 1)

        self.setLayout(vbox)

        self.set_lookup_key(starting_lookup_key)

    def set_lookup_key(self, lookup_key):
        if lookup_key.startswith('options:'):
            option_str = lookup_key.removeprefix('options:')
            self.set_option_path(
                Attribute.from_string(option_str)
            )
        elif lookup_key.startswith('search:'):
            search_str = lookup_key.removeprefix('search:')
            self.set_search_query(search_str)
        else:
            logger.warning('Invalid lookup key, doing nothing.')

    def set_option_path(self, option_path, option_type=None):
        self.nav_bar.replace_widget(
            navbar.NavBar.as_option_tree(option_path, self.set_lookup_key)
        )
        num_children = len(api.get_option_tree().children(option_path, mode="leaves"))
        if option_type is None:
            option_type = types.from_nix_type_str(
                api.get_option_tree().get_type(option_path)
            )

        # if 10 or fewer options, navlist with lowest level attribute selected and list of editable fields to the right
        # otherwise, show list of attributes within the clicked attribute and blank to the right
        # TODO: option type checking should probably take place in the same place where all type -> field resolving occurs
        if option_type in (types.AttrsType, types.AttrsOfType, types.ListOfType) or num_children > 10:
            self.nav_list.replace_widget(
                navlist.GenericNavListDisplay(
                    self.statemodel,
                    self.set_option_path,
                    option_path,
                    option_type
                )
            )
            self.fields_view.replace_widget(QtWidgets.QLabel(''))
        else:
            self.nav_list.replace_widget(
                navlist.GenericNavListDisplay(
                    self.statemodel,
                    self.set_option_path,
                    option_path.get_set(),
                    selected=option_path.get_end()
                )
            )
            if num_children <= 1:
                self.fields_view.replace_widget(
                    option_display.GenericOptionDisplay(
                        self.statemodel,
                        self.set_option_path,
                        option_path
                    )
                )
            else:
                self.fields_view.replace_widget(
                    FieldsGroupBox(
                        self.statemodel,
                        self.set_option_path,
                        option_path,
                    )
                )

    def set_search_query(self, search_str):
        self.nav_bar.replace_widget(
            navbar.NavBar.as_search_query(search_str, self.set_lookup_key)
        )

        self.nav_list.replace_widget(
            navlist.SearchResultListDisplay(
                search_str,
                self.set_option_path,
            )
        )
        self.fields_view.replace_widget(QtWidgets.QLabel(''))


class FieldsGroupBox(QtWidgets.QWidget):
    def __init__(self, statemodel, set_option_path_fn, option=None, is_base_viewer=True, *args, **kwargs):
        super().__init__(*args, **kwargs)

        group_box = QtWidgets.QGroupBox()
        group_box.setTitle(str(option))

        vbox = QtWidgets.QVBoxLayout()

        for child_option_path in api.get_option_tree().children(option):
            if len(api.get_option_tree().children(child_option_path)) > 1:
                vbox.addWidget(FieldsGroupBox(
                    statemodel,
                    set_option_path_fn,
                    child_option_path,
                    is_base_viewer=False
                ))
            else:
                vbox.addWidget(option_display.GenericOptionDisplay(
                    statemodel,
                    set_option_path_fn,
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
