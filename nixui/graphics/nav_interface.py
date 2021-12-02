import collections

from PyQt5 import QtWidgets

from nixui.options import api, types
from nixui.options.attribute import Attribute
from nixui.graphics import generic_widgets, navbar, navlist, option_display_group
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
                    Attribute(option_str)
                )
            elif lookup_key.startswith('search:'):
                search_str = lookup_key.removeprefix('search:')
                self.set_search_query(search_str)
            else:
                raise ValueError
        except ValueError:
            self.revert_to_previous_lookup_key()
            logger.warning(f'Invalid lookup key: {lookup_key}, reverting')

    # TODO: incorporate display_as_single_field and option_type into URI
    # TODO: max_renderable_field_widgets should be part of Preferences
    def set_option_path(self, option_path, option_type=None, display_as_single_field=False, max_renderable_field_widgets=10):
        """
        Update the navlist and option display to show the option path

        If the passed option_path is a container type (AttrsOf, ListOf), render the children in the navlist
        Otherwise render the parent option_path in the navlist with the option_path selected, and
            render the options FieldWidget in the option display

        option_path: The path of the option to be displayed
        option_type: Force the option to be rendered as option_type
        display_as_single_field: Regardless of whether it's a container type, force the option to be displayed as a FieldWidget
        max_renderable_field_widgets: We can display multiple widgets in the option display. If there are fewer descendent
                                      options than this number, render a navlist with option_path selected and all descendents
                                      shown in the option display.
        """
        self.uri_stack.append(f'options:{option_path}')

        self.nav_bar.replace_widget(
            navbar.NavBar.as_option_tree(option_path, self.set_lookup_key, back_enabled=len(self.uri_stack) > 1)
        )
        num_children = len(api.get_option_tree().children(option_path, mode="leaves"))

        # if 10 or fewer options, navlist with lowest level attribute selected and list of editable fields to the right
        # otherwise, show list of attributes within the clicked attribute and blank to the right
        # TODO: option type checking should probably take place in the same place where all type -> field resolving occurs

        # If the current option definition conforms to one of the valid navlist types then construct the navlist with said type
        option_def = api.get_option_tree().get_definition(option_path)
        dynamic_navlist_types = (types.AttrsOfType, types.ListOfType)
        option_type = option_type or api.get_option_tree().get_type(option_path)

        # if the option can legally be a dynamic navlist and its current value is a dynamic navlist, use that type
        if isinstance(option_type, (types.AnythingType, types.EitherType)):
            if any([isinstance(t, dynamic_navlist_types) for t in option_type.subtypes]):
                if any([isinstance(t, dynamic_navlist_types) for t in option_def._type.subtypes]):
                    option_type = option_def._type
        # else if it has a strict type (not Anything or Either), let that type determine whether it qualifies

        show_path_in_navlist = (
            not display_as_single_field and (
                isinstance(option_type, dynamic_navlist_types) or
                (isinstance(option_type, types.AttrsType) and num_children > max_renderable_field_widgets)
            )
        )
        if show_path_in_navlist:
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
                option_display_group.OptionDisplayGroupBox(
                    self.statemodel,
                    self.set_option_path,
                    option_path,
                    only_display_parent=display_as_single_field
                )
            )

    def set_search_query(self, search_str):
        self.uri_stack.append(f'search:{search_str}')

        self.nav_bar.replace_widget(
            navbar.NavBar.as_search_query(search_str, self.set_lookup_key, back_enabled=len(self.uri_stack) > 1)
        )

        self.nav_list.replace_widget(
            navlist.SearchResultListDisplay(
                search_str,
                self.set_option_path,
            )
        )
        self.fields_view.replace_widget(QtWidgets.QLabel(''))
