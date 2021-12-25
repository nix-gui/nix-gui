from PyQt5 import QtWidgets

import difflib

from nixui.graphics import generic_widgets


class DiffedOptionListSelector(generic_widgets.ScrollListStackSelector):
    ItemCls = generic_widgets.OptionListItem  # TODO: remove break dependency with generic_widgets.py

    def __init__(self, updates, *args, **kwargs):
        self.updates_map = {
            attr: (
                old_definition.expression_string if old_definition is not None else None,
                new_definition.expression_string if new_definition is not None else None
            )
            for attr, (old_definition, new_definition) in updates.items()
        }
        super().__init__(*args, **kwargs)

        # hack: make text box 3x the width of the list view
        self.stack.setMinimumWidth(self.item_list.width() * 3)

    def insert_items(self):
        for option in self.updates_map:
            it = self.ItemCls(option)
            self.item_list.addItem(it)

    def change_selected_item(self):
        option = self.item_list.currentItem().option
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


class DiffDialogBase(QtWidgets.QDialog):
    def __init__(self, statemodel, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.statemodel = statemodel

        diff_table = DiffedOptionListSelector(statemodel.get_diffs())

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(diff_table)
        layout.addWidget(self.init_btn_box())

        self.setSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)

        self.setLayout(layout)


class DiffDialog(DiffDialogBase):
    def init_btn_box(self):
        btn_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        btn_box.accepted.connect(self.accept)
        return btn_box


class SaveDialog(DiffDialogBase):
    def init_btn_box(self):
        btn_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Save)
        btn_box.accepted.connect(self.save)
        btn_box.rejected.connect(self.reject)
        return btn_box

    def save(self):
        self.statemodel.persist_changes()
        self.accept()
