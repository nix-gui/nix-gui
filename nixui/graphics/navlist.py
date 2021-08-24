import collections
import csv

from PyQt5 import QtWidgets, QtCore, QtGui

from nixui.graphics import icon, richtext
from nixui.options.attribute import Attribute
from nixui.options import api, option_definition


class GenericNavListDisplay:
    def __new__(cls, statemodel, option_path, set_option_path_fn, selected=None):
        option_type = api.get_option_tree().get_type(option_path)
        if option_type.startswith('attribute set of '):
            return DynamicAttrsOf(statemodel, option_path, set_option_path_fn, selected)
        elif option_type.startswith('list of '):
            return DynamicListOf(statemodel, option_path, set_option_path_fn, selected)
        else:
            return StaticAttrsOf(option_path, set_option_path_fn, selected)


class OptionScrollListSelector(QtWidgets.QListWidget):
    def __init__(self, base_option_path, set_option_path_fn=None):
        super().__init__()

        # change selected callback
        self.base_option_path = base_option_path
        self.set_option_path_fn = set_option_path_fn
        self.itemClicked.connect(self.set_option_path_callback)

        # load options
        options = api.get_option_tree().children(base_option_path)
        self.option_item_map = {}
        for option in options:
            item = ChildCountOptionListItem(option)
            self.addItem(item)
            self.option_item_map[option.get_end()] = item

        self._setup_scroll_list_selector_theme()  # form look and feel

    def _setup_scroll_list_selector_theme(self):
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.MinimumExpanding)
        self.setItemDelegate(richtext.HTMLDelegate())
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setMinimumWidth(self.sizeHintForColumn(0))

    def set_current_option(self, option_path):
        self.setCurrentItem(
            self.option_item_map[option_path]
        )

    def set_option_path_callback(self, *args, **kwargs):
        if self.set_option_path_fn:
            attr = Attribute.from_insertion(
                self.base_option_path,
                self.currentItem().option.get_end()
            )
            self.set_option_path_fn(attr)


class ChildCountOptionListItem(QtWidgets.QListWidgetItem):
    def __init__(self, option, use_fancy_name=True, use_child_count=True, extra_text=None, icon_path=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.option = option

        child_count = len(api.get_option_tree().children(self.option)) if use_child_count else None
        self.setText(
            richtext.get_option_html(
                self.option,
                use_fancy_name,
                child_count,
                extra_text=extra_text
            )
        )

        if icon_path:
            self.setIcon(QtGui.QIcon(icon_path))


class EditableListItem(QtWidgets.QListWidgetItem):
    def __init__(self, option, icon_path=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.option = option
        self.previous_option = option
        self.setFlags(self.flags() | QtCore.Qt.ItemIsEditable)
        self.setText(self.option.get_end())

    def setData(self, index, value):
        self.previous_option = self.option
        self.option = Attribute.from_insertion(self.option.get_set(), value)
        super().setData(index, value)


class StaticAttrsOf(OptionScrollListSelector):
    def __init__(self, option_path, set_option_path_fn, selected=None, *args, **kwargs):
        super().__init__(option_path, set_option_path_fn)
        if selected:
            self.set_current_option(selected)


class DynamicAttrsOf(QtWidgets.QWidget):
    def __init__(self, statemodel, option_path, set_option_path_fn, selected=None, *args, **kwargs):
        super().__init__()

        self.statemodel = statemodel
        self.option_path = option_path

        self.list_widget = OptionScrollListSelector(option_path, set_option_path_fn)
        if selected:
            self.list_widget.set_current_option(selected)

        self.add_btn = QtWidgets.QPushButton("", self)
        self.add_btn.setIcon(icon.get_icon('plus.png'))
        self.add_btn.clicked.connect(self.add_clicked)

        self.remove_btn = QtWidgets.QPushButton("", self)
        self.remove_btn.setIcon(icon.get_icon('trash.png'))
        self.remove_btn.clicked.connect(self.remove_clicked)

        btn_hbox = QtWidgets.QHBoxLayout()
        btn_hbox.addWidget(QtWidgets.QLabel(option_path.get_end()))
        btn_hbox.addWidget(self.add_btn)
        btn_hbox.addWidget(self.remove_btn)

        self.list_widget.itemDoubleClicked.connect(self.list_widget.editItem)
        self.list_widget.itemChanged.connect(self.rename_item)
        self.list_widget.model().rowsRemoved.connect(lambda: self.remove_item)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(btn_hbox)
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

    def remove_item(self, item):
        print('not implemented')

    def rename_item(self, item):
        self.statemodel.rename_option(item.previous_option, item.option)

    def add_clicked(self):
        item = EditableListItem(
            Attribute.from_insertion(self.option_path, 'newAttribute')
        )
        self.list_widget.addItem(item)
        self.statemodel.add_new_option(item.option)
        self.list_widget.editItem(item)

    def remove_clicked(self):
        self.list_widget.takeItem(self.list_widget.currentItem())

    def insert_items(self):
        for option in api.get_option_tree().children(self.option_path):
            it = self.ItemCls(option)
            self.list_widget.addItem(it)


class DynamicListOf(QtWidgets.QWidget):
    def __init__(self, statemodel, option_path, set_option_path_fn, selected=None, *args, **kwargs):
        super().__init__()

        self.statemodel = statemodel
        self.option_path = option_path

        self.list_widget = OptionScrollListSelector(option_path, set_option_path_fn)
        if selected:
            self.list_widget.set_current_option(selected)

        self.add_btn = QtWidgets.QPushButton("", self)
        self.add_btn.setIcon(icon.get_icon('plus.png'))
        self.add_btn.clicked.connect(self.add_clicked)

        self.remove_btn = QtWidgets.QPushButton("", self)
        self.remove_btn.setIcon(icon.get_icon('trash.png'))
        self.remove_btn.clicked.connect(self.remove_clicked)

        self.up_btn = QtWidgets.QPushButton("△", self)
        self.up_btn.clicked.connect(self.up_clicked)

        self.down_btn = QtWidgets.QPushButton("▽", self)
        self.down_btn.clicked.connect(self.down_clicked)

        btn_hbox = QtWidgets.QHBoxLayout()
        btn_hbox.addWidget(QtWidgets.QLabel(option_path.get_end()))
        btn_hbox.addWidget(self.add_btn)
        btn_hbox.addWidget(self.remove_btn)
        btn_hbox.addWidget(self.up_btn)
        btn_hbox.addWidget(self.down_btn)

        self.list_widget.itemDoubleClicked.connect(self.list_widget.editItem)
        self.list_widget.itemChanged.connect(self.rename_item)
        self.list_widget.model().rowsRemoved.connect(lambda: self.remove_item)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(btn_hbox)
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

    def remove_item(self, item):
        print('not implemented')

    def rename_item(self, item):
        self.statemodel.rename_option(item.previous_option, item.option)

    def add_clicked(self):
        item = EditableListItem(
            Attribute.from_insertion(self.option_path, 'newAttribute')
        )
        self.list_widget.addItem(item)
        self.statemodel.add_new_option(item.option)
        self.list_widget.editItem(item)

    def remove_clicked(self):
        self.list_widget.takeItem(self.list_widget.currentItem())

    def up_clicked(self):
        print('up')

    def down_clicked(self):
        print('down')

    def insert_items(self):
        for option in api.get_option_tree().children(self.option_path):
            it = self.ItemCls(option)
            self.list_widget.addItem(it)


class SearchResultListDisplay(QtWidgets.QListWidget):
    _setup_scroll_list_selector_theme = OptionScrollListSelector._setup_scroll_list_selector_theme

    def __init__(self, search_str, set_option_path_fn=None):
        super().__init__()

        self.set_option_path_fn = set_option_path_fn
        self.itemClicked.connect(self.set_option_path_callback)

        # load options
        tree = api.get_option_tree()
        for option_path, matched_operations in self.search_tree_for_options(tree, search_str):
            item = ChildCountOptionListItem(
                option_path,
                use_fancy_name=False,
                use_child_count=False,
                extra_text='Matched ' + ', '.join(matched_operations)
            )
            self.addItem(item)

        self._setup_scroll_list_selector_theme()  # same look and feel as basic nav displays

    def search_tree_for_options(self, tree, search_str):
        # TODO: consider offloading this to nixui/options/search.py
        """
        1) search_str is tokenized
        Example: A search string of
            "foo bar" baz bif
        results in three search tokens

        2) The data of all optionis iterated over, with each token being checked for matches.
        For a given options inclusion, each tokens must match at least one search function.

        Match operations are prioritized in the following order:
        - token is a substring of the attribute path
        - token exactly matches the option type
        - token is in the option description
        - prioritizing in memory definition, then configured definition, then system default definition
          (TODO, awaiting https://github.com/nix-gui/nix-gui/issues/9)
          - token partially matches the unevaluated definition
          - token exactly matches the string form of the evaluated definition
        """
        tokens = set([
            t.lower() for t in
            next(csv.reader([search_str], delimiter=' ', quotechar='"'))
        ])
        attribute_path_score_map = {}
        for attribute_path, data in tree.iter_attribute_data():
            matched_tokens = set()
            matched_operations = collections.OrderedDict([
                ('Attribute Path', 0), ('Type', 0), ('Description', 0),
                ('In Memory Value', 0), ('Configured Value', 0),
                ('System Default Value', 0)
            ])
            for token in tokens:
                if token in str(attribute_path).lower():
                    matched_tokens.add(token)
                    matched_operations['Attribute Path'] += 1
                if data is not None:
                    if data._type != option_definition.Undefined and token in data._type.lower():
                        matched_tokens.add(token)
                        matched_operations['Type'] += 1
                    if data.description != option_definition.Undefined and token in data.description.lower():
                        matched_tokens.add(token)
                        matched_operations['Description'] += 1

            if matched_tokens == tokens:
                attribute_path_score_map[attribute_path] = (
                    tuple(matched_operations.values()),
                    tuple(k for k, v in matched_operations.items() if v > 0)
                )

        return [
            (attribute_path, matched_operations) for
            attribute_path, (score, matched_operations) in
            sorted(
                attribute_path_score_map.items(),
                key=lambda item: item[1][0],
                reverse=True
            )
        ]

    def set_option_path_callback(self, *args, **kwargs):
        if self.set_option_path_fn:
            self.set_option_path_fn(
                self.currentItem().option
            )
