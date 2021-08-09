import re

from PyQt5 import QtWidgets, QtCore

from nixui.options.attribute import Attribute
from nixui.options import api
from nixui.graphics import generic_widgets, icon, richtext


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

        # form look and feel
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


class ChildCountOptionListItem(generic_widgets.OptionListItem):
    def set_text(self):
        child_count = len(api.get_option_tree().children(self.option))
        self.setText(richtext.get_option_html(self.option, child_count))


class EditableListItem(QtWidgets.QListWidgetItem):
    def __init__(self, option, icon_path=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.option = option
        self.previous_option = option
        self.setFlags(self.flags() | QtCore.Qt.ItemIsEditable)
        self.set_text()

    def set_text(self):
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
