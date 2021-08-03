from PyQt5 import QtWidgets, QtCore, QtGui

from nixui.graphics import richtext, icon


class ReplacableWidget(QtWidgets.QStackedWidget):
    def __init__(self, starting_widget=None):
        super().__init__()

        starting_widget = starting_widget or QtWidgets.QLabel()
        self.current_widget = starting_widget

        self.addWidget(self.current_widget)

    def replace_widget(self, widget):
        old_widget = self.current_widget
        self.addWidget(widget)
        self.setCurrentWidget(widget)
        self.removeWidget(old_widget)
        self.current_widget = widget


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
        self.btn_group.buttons()[idx].click()

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
        self.add_btn.setIcon(icon.get_icon('plus.png'))
        self.add_btn.clicked.connect(self.add_clicked)

        self.edit_btn = QtWidgets.QPushButton("", self)
        self.edit_btn.setIcon(icon.get_icon('edit.png'))
        self.edit_btn.clicked.connect(self.edit_clicked)

        self.remove_btn = QtWidgets.QPushButton("", self)
        self.remove_btn.setIcon(icon.get_icon('trash.png'))
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


class ScrollListStackSelector(QtWidgets.QWidget):
    ItemCls = QtWidgets.QListWidgetItem
    ListCls = QtWidgets.QListWidget

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.current_item = None

        # setup stack
        self.current_widget = QtWidgets.QLabel()
        self.stack = QtWidgets.QStackedWidget()
        self.stack.addWidget(self.current_widget)

        self.item_list = self.ListCls()
        self.insert_items()
        self.item_list.currentItemChanged.connect(self.change_selected_item)
        self.item_list.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.MinimumExpanding)
        self.item_list.setItemDelegate(richtext.HTMLDelegate())

        self.item_list.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.item_list.setMinimumWidth(self.item_list.sizeHintForColumn(0))

        self.nav_layout = QtWidgets.QVBoxLayout()
        if self.get_title():
            self.nav_layout.addWidget(
                QtWidgets.QLabel(self.get_title())
            )
        self.nav_layout.addWidget(self.item_list)

        self.hbox = QtWidgets.QHBoxLayout()
        self.hbox.setSpacing(0)
        self.hbox.setContentsMargins(0, 0, 0, 0)
        self.hbox.addLayout(self.nav_layout)
        self.hbox.addWidget(self.stack)

        self.set_layout()

    def get_title(self):
        return None

    def set_layout(self):
        self.setLayout(self.hbox)


class OptionListItem(QtWidgets.QListWidgetItem):
    def __init__(self, option, icon_path=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.option = option

        self.set_text()
        if icon_path:
            self.setIcon(QtGui.QIcon(icon_path))

    def set_text(self):
        self.setText(richtext.get_option_html(self.option))


class EditableOptionListItem(QtWidgets.QListWidgetItem):
    def __init__(self, option, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.option = option
        self.previous_option = option
        self.setFlags(self.flags() | QtCore.Qt.ItemIsEditable)
        self.set_text()

    def set_text(self):
        self.setText(str(self.option.get_end()))

    def setData(self, index, value):
        # is valid attribute name?
        if re.match(r'^[a-zA-Z\_][a-zA-Z0-9\_\'\-]*$', value):
            self.previous_option = self.option
            self.option = attribute.Attribute.from_insertion(self.option.get_set(), value)
            super().setData(index, value)
