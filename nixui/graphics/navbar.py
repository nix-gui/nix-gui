from functools import partial

from PyQt5 import QtWidgets

from nixui.options.attribute import Attribute


MAGNIFYING_GLASS_UNICODE = "🔍"
TREE_UNICODE = "🌲"


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
    - restructure so rendering is dependent on NavBar.path_textbox, which is never externally changed.
      Rather than OptionNavigationInterface handling all updates, have all changes such as clicking an
      attribute involve changing the lookup key
    - implement ListOf
    - move undo toolbar item here
    - delete search toolbar item
    """
    def __init__(self, set_lookup_key_fn, unfocused_text, focused_text, up_fn=None):
        super().__init__()

        # create widgets and define behavior
        back_btn = QtWidgets.QPushButton('◀')
        back_btn.clicked.connect(lambda: print('not implemented'))

        up_btn = QtWidgets.QPushButton('▲')
        if up_fn is not None:
            up_btn.clicked.connect(up_fn)
        else:
            up_btn.setEnabled(False)

        path_textbox = FocusChangeTextLineEdit(
            unfocused_text=unfocused_text,
            focused_text=focused_text,
        )
        path_textbox.returnPressed.connect(
            lambda: set_lookup_key_fn(path_textbox.text())
        )

        searchbox = QtWidgets.QLineEdit()
        searchbox.setPlaceholderText('Search...')
        searchbox.returnPressed.connect(
            lambda: set_lookup_key_fn(f'search:{searchbox.text()}')
        )

        # add to layout
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(back_btn, 0)
        hbox.addWidget(up_btn, 0)
        hbox.addWidget(path_textbox, 4)
        hbox.addWidget(searchbox, 1)

        hbox.setSpacing(3)
        hbox.setContentsMargins(2, 2, 2, 2)

        self.setLayout(hbox)

    @classmethod
    def as_option_tree(cls, option_path, set_lookup_key_fn):
        return cls(
            set_lookup_key_fn=set_lookup_key_fn,
            unfocused_text=' » '.join([TREE_UNICODE] + list(option_path)),
            focused_text=f'options:{str(option_path)}',
            up_fn=lambda: set_lookup_key_fn(f'options:{option_path.get_set()}')
        )

    @classmethod
    def as_search_query(cls, search_str, set_lookup_key_fn):
        return cls(
            set_lookup_key_fn=set_lookup_key_fn,
            unfocused_text=f'{MAGNIFYING_GLASS_UNICODE} » {search_str}',
            focused_text=f'search:{search_str}',
        )
