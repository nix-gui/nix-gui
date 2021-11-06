import collections

from PyQt5 import QtWidgets, QtCore

from nixui.options import api, types
from nixui.options.attribute import Attribute
from nixui.graphics import generic_widgets, navbar, navlist, option_display
from nixui.utils.logger import logger


class OptionNavigationInterface(QtWidgets.QWidget):
    def __init__(self, statemodel, starting_lookup_key='options:'):
        super().__init__()
        self.statemodel = statemodel

        # history of lookup keys
        self.uri_stack = collections.deque()

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

    def revert_to_previous_lookup_key(self):
        current_uri = self.uri_stack.pop()
        previous_uri = self.uri_stack.pop()
        self.set_lookup_key(previous_uri)
        logger.info(f'reverted from "{current_uri}" to previous URI: "{previous_uri}"')

    def set_lookup_key(self, lookup_key=None):
        if lookup_key is None:
            return self.revert_to_previous_lookup_key()

        try:
            if lookup_key.startswith('options:'):
                option_str = lookup_key.removeprefix('options:')
                self.set_option_path(
                    Attribute.from_string(option_str)
                )
            elif lookup_key.startswith('search:'):
                search_str = lookup_key.removeprefix('search:')
                self.set_search_query(search_str)
            else:
                raise ValueError
        except ValueError:
            self.revert_to_previous_lookup_key()
            logger.warning(f'Invalid lookup key: {lookup_key}, reverting')

    # TODO: remove option_type, or incorporate it into URI
    def set_option_path(self, option_path, option_type=None):
        self.uri_stack.append(f'options:{option_path}')

        self.nav_bar.replace_widget(
            navbar.NavBar.as_option_tree(option_path, self.set_lookup_key)
        )
        num_children = len(api.get_option_tree().children(option_path, mode="leaves"))

        # if 10 or fewer options, navlist with lowest level attribute selected and list of editable fields to the right
        # otherwise, show list of attributes within the clicked attribute and blank to the right
        # TODO: option type checking should probably take place in the same place where all type -> field resolving occurs
        option_type = option_type or api.get_option_tree().get_type(option_path)
        option_definition = api.get_option_tree().get_definition(option_path)
        navlist_types = (types.AttrsType, types.AttrsOfType, types.ListOfType)
        qualified_for_navlist = (
            type(option_type) in navlist_types or
            (
                isinstance(option_type, types.AnythingType) and
                type(option_definition._type) in navlist_types
            ) or (
                isinstance(option_type, types.EitherType) and
                any([type(t) in navlist_types for t in option_definition._type])
            )
        )
        if qualified_for_navlist or num_children > 10:
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
            self.fields_view.replace_widget(
                FieldsGroupBox(
                    self.statemodel,
                    self.set_option_path,
                    option_path,
                )
            )

    def set_search_query(self, search_str):
        self.uri_stack.append(f'search:{search_str}')

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

        self.elements = []

        option_paths = api.get_option_tree().children(option)
        group_box = QtWidgets.QGroupBox()

        if option_paths:
            group_box.setTitle(str(option))
        else:
            option_paths = [option]

        vbox = QtWidgets.QVBoxLayout()
        for child_option_path in option_paths:
            if len(api.get_option_tree().children(child_option_path)) > 1:
                fields_group_box = FieldsGroupBox(
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
