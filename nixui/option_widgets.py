from operator import eq
from functools import partial, lru_cache
import re

from PyQt5 import QtWidgets, QtGui, QtCore

from nixui import api, richtext, generic_widgets


# tuples of (match fn, widget)
@lru_cache
def get_field_type_widget_map():
    return [
        [
            partial(eq, 'null'),
            NullField,
        ],
        [
            partial(eq, 'boolean'),
            BooleanField,
        ],
        [
            partial(eq, 'string'),
            TextField,
        ],
        [
            lambda f: f.startswith('strings concatenated with '),
            TextField,  # TODO: might waght to use StringListField here?
        ],
        [
            partial(eq, 'string, not containing newlines or colons'),
            partial(SingleLineTextField, regexp=r"^[^(:|\n|(\r\n)]*$")
        ],
        [
            partial(eq, 'YAML value'),
            partial(TextField, regexp=r"([ ]+)?((\w+|[^\w\s\r\n])([ ]*))?(?:\r)?(\n)?")
        ],
        [
            partial(eq, 'JSON value'),
            partial(TextField, regexp=r"\{.*\:\{.*\:.*\}\}")
        ],
        [
            partial(eq, 'signed integer'),
            IntegerField,
        ],
        [
            partial(eq, 'integer'),
            IntegerField,
        ],
        [
            partial(eq, 'unsigned integer, meaning >=0'),
            partial(IntegerField, minimum=0),
        ],
        [
            partial(eq, 'positive integer, meaning >0'),
            partial(IntegerField, minimum=1),
        ],
        [
            partial(eq, '16 bit unsigned integer; between 0 and 65535 (both inclusive)'),
            partial(IntegerField, minimum=0, maximum=65535),
        ],
        [
            lambda f: f.startswith('one of '),
            OneOfField,
        ],
        [
            partial(eq, 'list of strings'),
            StringListField,
        ],
        [
            partial(eq, 'reference'),
            ReferenceField,
        ],
        [
            partial(eq, 'expression'),
            ExpressionField
        ],
    ]


def get_field_widget(field_type, option):
    for type_label_validator, widget_constructor in get_field_type_widget_map():
        if type_label_validator(field_type):
            return widget_constructor(option)
    else:
        return NotImplementedField(option)


def get_field_types(option_type):
    if ' or ' in option_type:
        possible_types = option_type.split(' or ')
    else:
        possible_types = [option_type]

    universal_fields = ['expression', 'reference']

    return possible_types + universal_fields


def get_field_color(field_type):
    field_colors = {
        'expression': QtGui.QColor(193, 236, 245),
        'reference': QtGui.QColor(174, 250, 174),
        None: QtGui.QColor(255, 255, 240),  # default
    }
    return field_colors.get(field_type, field_colors[None])


class GenericOptionDisplay(QtWidgets.QWidget):
    def __init__(self, slotmapper, option, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.slotmapper = slotmapper
        self.option = option
        self.starting_value = None

        field_types = get_field_types(api.get_option_type(option))

        # set title and description
        text = QtWidgets.QLabel(richtext.get_option_html(
            option,
            type_label=api.get_option_type(option),
            description=api.get_option_description(option),
        ))
        text.setWordWrap(True)
        text.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)

        # set type selector
        self.field_type_selector = generic_widgets.ExclusiveButtonGroup(
            choices=[
                (
                    'one of' if t.startswith('one of ') else t,
                    self.set_type,
                    get_field_color(t)
                )
                for t in field_types
            ]
        )
        # TODO: remove this expression and reference editor are done
        self.field_type_selector.btn_group.buttons()[-2].setEnabled(False)
        self.field_type_selector.btn_group.buttons()[-1].setEnabled(False)

        # set fields for entry editing
        self.entry_stack = QtWidgets.QStackedWidget()
        for t in field_types:
            entry_widget = get_field_widget(t, self.option)
            entry_widget.focus_change.connect(self.handle_focus_change)
            self.entry_stack.addWidget(entry_widget)
        self.stacked_widgets = list(map(self.entry_stack.widget, range(self.entry_stack.count())))

        # add all to layout
        description_layout = QtWidgets.QVBoxLayout()
        description_layout.addWidget(text, stretch=3)
        description_layout.addWidget(self.field_type_selector, stretch=1)
        layout = QtWidgets.QHBoxLayout()
        layout.addLayout(description_layout)
        layout.addWidget(self.entry_stack, stretch=8)
        self.setLayout(layout)

        self._load_value()

    def _load_value(self):
        option_value = api.get_option_value(self.option)

        for i, field in enumerate(self.stacked_widgets):
            if field.validate_field(option_value):
                self.field_type_selector.select(i)
                field.load_value(option_value)
                break

        self.starting_value = self.value

    def set_type(self, arg):
        self.entry_stack.setCurrentIndex(
            self.field_type_selector.checked_index()
        )
        self.handle_focus_change()


    def handle_focus_change(self):
        self.slotmapper('value_changed')(self.option, self.value)

    @property
    def value(self):
        return self.entry_stack.currentWidget().current_value

    def contains_focus(self):
        return (
            self.hasFocus() or
            any(w.hasFocus() for w in self.stacked_widgets) or
            any(w.hasFocus() for w in self.field_type_selector.btn_group.buttons())
        )

    def paint_background_color(self, *bg_color_tuple):
        qp = QtGui.QPainter(self)
        r = QtCore.QRect(0, 0, self.width(), self.height())
        qp.fillRect(r, QtGui.QColor.fromRgb(*bg_color_tuple))
        qp.end()

    def paintEvent(self, ev):
        super().paintEvent(ev)
        if self.contains_focus():
            self.paint_background_color(233, 245, 248, 255)
        elif self.starting_value != self.value:
            self.paint_background_color(194, 249, 197, 255)
        else:
            return
        #elif api.default_value(self.option) != api.value(self.option):
        #    TODO: handle cases where changes are non-default AND saved
        # TODO: handle case where field is invalid

        # TODO: change parent navigation widget colors in heirarchy
        self.update()


class Field:
    focus_change = QtCore.pyqtSignal()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.focus_change.emit()


class NullField(QtWidgets.QLabel, Field):
    def __init__(self, option, **constraints):
        super().__init__()
        self.option = option
        self.constraints = constraints
        self.loaded_value = None

    @staticmethod
    def validate_field(value):
        return value is None

    def load_value(self, value):
        self.setText('NULL')
        self.loaded_value = value

    @property
    def current_value(self):
        return None

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.focus_change.emit()


class BooleanField(QtWidgets.QCheckBox, Field):
    def __init__(self, option, **constraints):
        super().__init__()
        self.option = option
        self.constraints = constraints
        self.loaded_value = None

    @staticmethod
    def validate_field(value):
        return isinstance(value, bool)

    def load_value(self, value):
        self.setChecked(value)
        self.loaded_value = value

    @property
    def current_value(self):
        return self.isChecked()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.focus_change.emit()


class TextField(QtWidgets.QTextEdit, Field):
    def __init__(self, option, **constraints):
        super().__init__()
        self.option = option
        self.constraints = constraints
        self.loaded_value = None

    def validate_field(self, value):
        if not isinstance(value, str):
            return False
        if 'regexp' in self.constraints:
            return re.match(self.constraints['regexp'], value)
        else:
            return True

    def load_value(self, value):
        self.setText(value)
        self.loaded_value = value

    @property
    def current_value(self):
        return self.toPlainText()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.focus_change.emit()


class SingleLineTextField(QtWidgets.QLineEdit, Field):
    validate_field = TextField.validate_field
    load_value = TextField.load_value
    current_value = TextField.current_value

    def __init__(self, option, **constraints):
        super().__init__()
        self.option = option
        self.constraints = constraints
        self.loaded_value = None

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.focus_change.emit()


class IntegerField(QtWidgets.QSpinBox, Field):
    def __init__(self, option, **constraints):
        super().__init__()
        self.option = option
        self.constraints = constraints
        self.loaded_value = None

    def validate_field(self, value):
        if not isinstance(value, int):
            return False
        minimum = self.constraints.get('minimum', float('-inf'))
        maximum = self.constraints.get('maximum', float('inf'))
        return minimum <= value <= maximum

    def load_value(self, value):
        self.setValue(value)
        self.loaded_value = value

    @property
    def current_value(self):
        return self.value()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.focus_change.emit()

# TODO: load option strings with self.add_item
class StringListField(generic_widgets.StringListEditorWidget, Field):
    def __init__(self, option, **constraints):
        super().__init__()
        self.option = option
        self.constraints = constraints
        self.loaded_value = None

    @staticmethod
    def validate_field(value):
        if not isinstance(value, list):
            return False
        return all([
            isinstance(item, str)
            for item in value
        ])

    def load_value(self, value):
        pass  # TODO
        # self.loaded_value = value

    @property
    def current_value(self):
        pass  # TODO

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.focus_change.emit()


class OneOfRadioFrameField(QtWidgets.QFrame, Field):
    def __init__(self, option, choices):
        super().__init__()
        self.option = option
        self.choices = choices

        self.choice_button_map = {}

        layout = QtWidgets.QVBoxLayout(self)
        for choice in self.choices:
            btn = QtWidgets.QRadioButton(choice)
            self.choice_button_map[choice] = btn
            layout.addWidget(btn)

    def validate_field(self, value):
        return value in self.choices

    def load_value(self, value):
        self.choice_button_map[value].setChecked(True)
        self.loaded_value = value

    @property
    def current_value(self):
        for value, button in self.choice_button_map.items():
            if button.isChecked():
                return value

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.focus_change.emit()


class OneOfComboBoxField(QtWidgets.QComboBox, Field):
    def __init__(self, option, choices):
        super().__init__()
        self.option = option
        self.choices = choices

        for choice in self.choices:
            self.addItem(choice)

    def validate_field(self, value):
        return value in self.choices

    def load_value(self, value):
        self.setCurrentIndex(self.choices.index(value))
        self.loaded_value = value

    @property
    def current_value(self):
        return self.currentText()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.focus_change.emit()


class OneOfField:
    def __new__(cls, option):
        field_type = api.get_option_type(option)
        choices = [choice.strip('" ') for choice in field_type.split('one of ', 1)[1].split(',')]

        if len(choices) < 5:
            return OneOfRadioFrameField(option, choices)
        else:
            return OneOfComboBoxField(option, choices)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.focus_change.emit()


# TODO
class NotImplementedField(QtWidgets.QLabel, Field):
    def __init__(self, option, **constraints):
        super().__init__()
        self.option = option
        self.constraints = constraints
        self.loaded_value = None

    @staticmethod
    def validate_field(value):
        return False

    def load_value(self, value):
        self.setText('TODO')
        self.loaded_value = value

    @property
    def current_value(self):
        return None

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.focus_change.emit()


# TODO
ReferenceField = NotImplementedField
ExpressionField = NotImplementedField
