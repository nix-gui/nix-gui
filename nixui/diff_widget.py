from PyQt5 import QtWidgets, QtCore

import difflib

from nixui import generic_widgets


class DiffedOptionListSelector(generic_widgets.ScrollListStackSelector):
    def __init__(self, updates, *args, **kwargs):
        self.updates_map = {u.option: (str(u.old_value), str(u.new_value)) for u in updates}
        super().__init__(*args, **kwargs)

        # hack: make text box 3x the width of the list view
        self.stack.setMinimumWidth(self.item_list.width() * 3)

    def insert_items(self):
        for option in self.updates_map:
            it = self.ItemCls(option)
            self.item_list.addItem(it)

    def change_item(self):
        option = self.item_list.currentItem().text()
        old_value, new_value = self.updates_map[option]

        diff = difflib.unified_diff(
            old_value.splitlines(1),
            new_value.splitlines(1),
            lineterm=''
        )
        # blank lines and control lines
        diff = [line.strip() for line in diff][3:]

        diff_str = '\n'.join(diff)

        view = QtWidgets.QPlainTextEdit(diff_str)
        view.setReadOnly(True)

        # monospace
        font = view.document().defaultFont()
        font.setFamily("Courier New")
        view.document().setDefaultFont(font)

        old_widget = self.current_widget
        self.stack.addWidget(view)
        self.stack.setCurrentWidget(view)
        self.stack.removeWidget(old_widget)
        self.current_widget = view


class DiffDialog(QtWidgets.QDialog):
    def __init__(self, statemodel, *args, **kwargs):
        super().__init__(*args, **kwargs)

        diff_table = DiffedOptionListSelector(statemodel.get_update_set())

        btn_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        btn_box.accepted.connect(self.accept)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(diff_table)
        layout.addWidget(btn_box)

        self.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)

        self.setLayout(layout)
