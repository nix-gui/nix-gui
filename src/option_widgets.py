from PyQt5 import QtWidgets, QtGui

import api, richtext


class GenericOptionDisplay(QtWidgets.QWidget):
    def __init__(self, option=None, option_type=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert option or option_type

        lay = QtWidgets.QHBoxLayout()

        if option:
            leaf = api.get_leaf(option)
            option_type = leaf['type']
            option_description = leaf['description']
            text = QtWidgets.QLabel(richtext.get_option_html(option, type_label=option_type, description=option_description))
            #doc = QtGui.QTextDocument()
            #doc.setHtml(richtext.get_option_html(option, type_label=option_type, description=option_description))
            #text = QtWidgets.QGraphicsTextItem()
            #text.setDocument(doc)
        else:
            text = QtWidgets.QLabel(option_type)

        lay.addWidget(text)

        # or
        if ' or ' in option_type:
            possible_types = option_type.split(' or ')
            entry_widget = OrEditorWidget(option, list(set(possible_types)))

        # null
        elif option_type == 'null':
            entry_widget = QtWidgets.QLabel('Null')

        # boolean
        elif option_type == 'boolean':
            entry_widget = QtWidgets.QCheckBox()

        # text
        elif option_type == 'string':
            entry_widget = QtWidgets.QTextEdit()
        elif option_type == 'string, not containing newlines or colons':
            entry_widget = QtWidgets.QLineEdit()
            entry_widget.setValidator(
                QtGui.QRegExpValidator(QtGui.QRegExp(r"^[^(:|\n|(\r\n)]*$"))
            )
        elif option_type == 'YAML value':
            entry_widget = QtWidgets.QTextEdit()
            entry_widget.setValidator(
                QtGui.QRegExpValidator(QtGui.QRegExp(r"([ ]+)?((\w+|[^\w\s\r\n])([ ]*))?(?:\r)?(\n)?"))
            )
        elif option_type == 'JSON value':
            entry_widget = QtWidgets.QTextEdit()
            entry_widget.setValidator(
                QtGui.QRegExpValidator(QtGui.QRegExp(r"\{.*\:\{.*\:.*\}\}"))
            )

        # list of
        elif option_type == 'list of strings':
            entry_widget = StringListEditorWidget(option)

        # numbers
        elif option_type in ('integer', 'signed integer'):
            entry_widget = QtWidgets.QLineEdit()
            entry_widget.setValidator(QtGui.QIntValidator())

        # option selection
        elif option_type.startswith('one of '):
            choices = [choice.strip('" ') for choice in option_type.split('one of ', 1)[1].split(',')]
            if len(choices) < 5:
                entry_widget = QtWidgets.QGroupBox()
                entry_lay = QtWidgets.QVBoxLayout(entry_widget)
                for choice in choices:
                    entry_lay.addWidget(QtWidgets.QRadioButton(choice))
            else:
                entry_widget = QtWidgets.QComboBox()
                for choice in choices:
                    entry_widget.addItem(choice)

        else:
            entry_widget = QtWidgets.QLabel(option)

        lay.addWidget(entry_widget)
        self.setLayout(lay)


class OrEditorWidget(QtWidgets.QWidget):
    def __init__(self, option, possible_types):
        super().__init__()

        self.type_btn_group = QtWidgets.QButtonGroup()

        self.entry_stack = QtWidgets.QStackedWidget()

        self.type_radio_box = QtWidgets.QGroupBox()
        self.type_radio_box.setTitle(str(possible_types))
        type_radio_layout = QtWidgets.QVBoxLayout(self.type_radio_box)
        type_radio_layout.addWidget(QtWidgets.QLabel('test'))
        for t in possible_types:
            entry_widget = GenericOptionDisplay(option_type=t)
            btn = QtWidgets.QRadioButton(t)
            btn.clicked.connect(self.set_type)

            type_radio_layout.addWidget(btn)

            self.type_btn_group.addButton(btn, id=len(self.entry_stack))
            self.entry_stack.addWidget(entry_widget)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.type_radio_box)
        layout.addWidget(self.entry_stack)
        self.setLayout(layout)

    def set_type(self, arg):
        self.entry_stack.setCurrentIndex(
            self.type_btn_group.checkedId()
        )


# modified version of https://github.com/abrytanczyk/JPWP---zadania
class StringListEditorWidget(QtWidgets.QWidget):
    def __init__(self, option, validator=None):
        super().__init__()

        # TODO: load option strings
        self.string_list = ['aa', 'bb']
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

        # Insert strings into list
        for item in self.string_list:
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
