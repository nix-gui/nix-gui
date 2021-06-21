from PyQt5 import QtWidgets, QtGui, QtCore


class ExclusiveButtonGroup(QtWidgets.QFrame):
    selection_changed = QtCore.pyqtSignal(str)

    def __init__(self, choices=[]):
        super().__init__()

        layout = QtWidgets.QHBoxLayout(self)

        self.btn_group = QtWidgets.QButtonGroup()
        self.btn_group.setExclusive(True)

        for i, (choice, handler, color) in enumerate(choices):
            btn = QtWidgets.QPushButton(choice)
            p = btn.palette()
            p.setColor(btn.backgroundRole(), color)
            btn.setPalette(p)
            btn.setCheckable(True)
            btn.clicked.connect(handler)
            layout.addWidget(btn)
            self.btn_group.addButton(btn, id=i)

        layout.setSpacing(0)

        self.setLayout(layout)

    def select(self, idx):
        self.btn_group.buttons()[idx].setChecked(True)

    def checked_index(self):
        return self.btn_group.checkedId()


def SeparatorLine():
    line = QtWidgets.QFrame()
    line.setFrameShape(QtWidgets.QFrame.HLine)
    line.setFrameShadow(QtWidgets.QFrame.Sunken)
    return line

# modified version of https://github.com/abrytanczyk/JPWP---zadania
class StringListEditorWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()


    def initUI(self):
        layout = QtWidgets.QHBoxLayout(self)
        buttons_layout = QtWidgets.QVBoxLayout(self)

        self.list_widget = QtWidgets.QListWidget(self)
        self.list_widget.itemSelectionChanged.connect(self.item_selection_changed)

        self.add_btn = QtWidgets.QPushButton("", self)
        self.add_btn.setIcon(QtGui.QIcon('icons/plus.png'))
        self.add_btn.clicked.connect(self.add_clicked)

        self.edit_btn = QtWidgets.QPushButton("", self)
        self.edit_btn.setIcon(QtGui.QIcon('icons/edit.png'))
        self.edit_btn.clicked.connect(self.edit_clicked)

        self.remove_btn = QtWidgets.QPushButton("", self)
        self.remove_btn.setIcon(QtGui.QIcon('icons/trash.png'))
        self.remove_btn.clicked.connect(self.remove_clicked)

        buttons_layout.addWidget(self.add_btn)
        buttons_layout.addWidget(self.edit_btn)
        buttons_layout.addWidget(self.remove_btn)
        buttons_layout.addStretch()

        layout.addWidget(self.list_widget)
        layout.addLayout(buttons_layout)

        self.setLayout(layout)

    def add_item(self, item):
        self.list_widget.addItem(QtWidgets.QListWidgetItem(item, self.list_widget))

    def update_buttons(self):
        any_items = self.list_widget.count() > 0

        self.edit_btn.setEnabled(any_items)
        self.remove_btn.setEnabled(any_items)

        self.update_list()

    def update_list(self):
        new_arguments = []
        for i in range(self.list_widget.count()):
            new_arguments.append(self.list_widget.item(i).text())

        self.string_list.clear()
        self.string_list.extend(new_arguments)

    def item_selection_changed(self, *args):
        self.update_buttons()

    def add_clicked(self):
        text, okPressed = QtWidgets.QInputDialog.getText(self, "Add Item", "Item Value:", QtWidgets.QLineEdit.Normal, "")

        if okPressed and text != '' and not str.isspace(text):
            self.list_widget.addItem(QtWidgets.QListWidgetItem(text, self.list_widget))
            self.list_widget.setCurrentRow(self.list_widget.count() - 1)
            self.list_widget.scrollToItem(self.list_widget.currentItem())

            self.update_buttons()

    def edit_clicked(self):
        current = self.list_widget.currentItem()
        original = current.text()
        if str.isspace(original) or original == '':
            self.add_clicked()
        else:
            text, okPressed = QtWidgets.QInputDialog.getText(self, "Edit Item", "Item Value:", QtWidgets.QLineEdit.Normal, original)

            if okPressed and text != '' and not str.isspace(text):
                current.setText(text)
                self.update_buttons()

    def remove_clicked(self):
        current = self.list_widget.currentItem()
        original = current.text()

        if original == '' or \
            str.isspace(original) or \
            QtWidgets.QMessageBox.question(self, "Remove", f"Remove Item: `{original}`",
                                           QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                           QtWidgets.QMessageBox.Yes) == QtWidgets.QMessageBox.Yes:
            self.list_widget.takeItem(self.list_widget.currentRow())
            self.update_buttons()
