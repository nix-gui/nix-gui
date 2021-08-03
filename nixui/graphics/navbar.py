from functools import partial

from PyQt5 import QtWidgets

from nixui.options.attribute import Attribute


class FocusChangeTextLineEdit(QtWidgets.QLineEdit):
    def __init__(self, unfocused_text, focused_text, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unfocused_text = unfocused_text
        self.focused_text = focused_text
        self.setText(unfocused_text)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.setText(self.focused_text)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.setText(self.unfocused_text)


class NavBar(QtWidgets.QWidget):
    """
    Horizontal Layout:
    - Back arrow (previous path)
    - Up arrow (up a path)
    - Path Textbox: (foo.bar.baz converted to Foo > Bar > Baz until clicked)
    - Searchbox

    TODO:
    - implement ListOf
    - move undo toolbar item here
    - delete search toolbar item
    """
    def __init__(self, option_path, set_option_fn, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.set_option_fn = set_option_fn

        # create widgets and define behavior
        back_btn = QtWidgets.QPushButton('◀')
        back_btn.clicked.connect(lambda: print('not implemented'))

        up_btn = QtWidgets.QPushButton('▲')
        up_btn.clicked.connect(lambda: set_option_fn(option_path.get_set()))

        path_textbox = FocusChangeTextLineEdit(
            unfocused_text=' » '.join(['options'] + list(option_path)),
            focused_text=str(option_path),
        )
        path_textbox.returnPressed.connect(
            lambda: set_option_fn(Attribute.from_string(path_textbox.text()))
        )

        searchbox = QtWidgets.QLineEdit()
        searchbox.setPlaceholderText('Search...')
        searchbox.returnPressed.connect(lambda: print('not implemented'))

        # add to layout
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(back_btn, 0)
        hbox.addWidget(up_btn, 0)
        hbox.addWidget(path_textbox, 4)
        hbox.addWidget(searchbox, 1)

        hbox.setSpacing(3)
        hbox.setContentsMargins(2, 2, 2, 2)

        self.setLayout(hbox)
