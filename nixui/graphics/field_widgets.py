from functools import partial, lru_cache
from operator import eq
import re

from PyQt5 import QtWidgets, QtGui, QtCore

from nixui.options import api, option_tree, option_definition
from nixui.graphics import richtext, generic_widgets


# tuples of (match fn, widget)
@lru_cache
def get_field_type_widget_map():
    return [
        [
            partial(eq, option_tree.Undefined),
            UndefinedField,
        ],
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
            TextField,
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
        # fake types, allowing for specialized expressions
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

    return ['undefined'] + possible_types + universal_fields


def get_field_color(field_type):
    field_colors = {
        'undefined': QtGui.QColor(255, 200, 200),
        'expression': QtGui.QColor(193, 236, 245),
        'reference': QtGui.QColor(174, 250, 174),
        None: QtGui.QColor(255, 255, 240),  # default
    }
    return field_colors.get(field_type, field_colors[None])


class GenericOptionDisplay(QtWidgets.QWidget):
    def __init__(self, statemodel, option, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.statemodel = statemodel
        self.option = option
        self.starting_definition = None

        field_types = get_field_types(api.get_option_tree().get_type(option))

        # set title and description
        text = QtWidgets.QLabel(richtext.get_option_html(
            option,
            type_label=api.get_option_tree().get_type(option),
            description=api.get_option_tree().get_description(option),
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
        # TODO: remove this when reference editor is done
        self.field_type_selector.btn_group.buttons()[-1].setEnabled(False)

        # set fields for entry editing
        self.entry_stack = QtWidgets.QStackedWidget()
        for t in field_types:
            entry_widget = get_field_widget(t, self.option)
            entry_widget.stateChanged.connect(self.handle_state_change)
            self.entry_stack.addWidget(entry_widget)
            self.statemodel.slotmapper.add_slot(('update_field', self.option), self._load_definition)
        self.stacked_widgets = list(map(self.entry_stack.widget, range(self.entry_stack.count())))

        # add all to layout
        description_layout = QtWidgets.QVBoxLayout()
        description_layout.addWidget(text, stretch=3)
        description_layout.addWidget(self.field_type_selector, stretch=1)
        layout = QtWidgets.QHBoxLayout()
        layout.addLayout(description_layout)
        layout.addWidget(self.entry_stack, stretch=8)
        self.setLayout(layout)

        self._load_definition()

    def _load_definition(self):
        option_definition = self.statemodel.get_definition(self.option)

        for i, field in enumerate(self.stacked_widgets):
            if field.validate_field(option_definition.obj):
                self.field_type_selector.select(i)
                field.load_value(option_definition.obj)
                break
        else:
            self.field_type_selector.select(len(self.stacked_widgets) - 1)
            expression_field = self.stacked_widgets[-2]
            expression_field.load_value(option_definition.expression_string)

        self.starting_definition = self.definition

    def set_type(self, arg):
        stack_idx = self.field_type_selector.checked_index()
        current_widget = self.entry_stack.widget(stack_idx)
        definition = self.statemodel.get_definition(self.option)
        if isinstance(current_widget, ExpressionField):
            current_widget.load_value(definition.expression_string)
        else:
            current_widget.load_value(definition.obj)
        self.entry_stack.setCurrentIndex(stack_idx)
        self.handle_state_change()

    def handle_state_change(self):
        self.statemodel.slotmapper('form_definition_changed')(self.option, self.definition)

    @property
    def definition(self):
        current_widget = self.entry_stack.currentWidget()
        expression_widget = self.stacked_widgets[-2]
        form_value = self.entry_stack.currentWidget().current_value
        if current_widget == expression_widget:
            return option_definition.OptionDefinition.from_expression_string(form_value)
        else:
            return option_definition.OptionDefinition.from_object(form_value)

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
        elif self.starting_definition != self.definition:
            self.paint_background_color(194, 249, 197, 255)
        else:
            return
        self.update()


class BooleanField(QtWidgets.QCheckBox):
    def __init__(self, option, **constraints):
        super().__init__()
        self.option = option
        self.constraints = constraints
        self.loaded_value = None

    @staticmethod
    def validate_field(value):
        return isinstance(value, bool)

    def load_value(self, value):
        if not self.validate_field(value):
            value = False
        self.setChecked(value)
        self.loaded_value = value

    @property
    def current_value(self):
        return self.isChecked()


class TextField(QtWidgets.QTextEdit):
    stateChanged = QtCore.pyqtSignal(str)

    def __init__(self, option, **constraints):
        super().__init__()
        self.option = option
        self.constraints = constraints
        self.loaded_value = None

        self.textChanged.connect(lambda: self.stateChanged.emit(self.current_value))

    def validate_field(self, value):
        if not isinstance(value, str):
            return False
        if 'regexp' in self.constraints:
            return re.match(self.constraints['regexp'], value)
        else:
            return True

    def load_value(self, value):
        if not self.validate_field(value):
            value = ''
        self.setText(value)
        self.loaded_value = value

    @property
    def current_value(self):
        return self.toPlainText()


class SingleLineTextField(QtWidgets.QLineEdit):
    stateChanged = TextField.stateChanged
    textChanged = TextField.textChanged
    validate_field = TextField.validate_field
    load_value = TextField.load_value
    current_value = TextField.current_value

    def __init__(self, option, **constraints):
        super().__init__()
        self.option = option
        self.constraints = constraints
        self.loaded_value = None


class IntegerField(QtWidgets.QSpinBox):
    stateChanged = QtCore.pyqtSignal(int)

    def __init__(self, option, **constraints):
        super().__init__()
        self.option = option
        self.constraints = constraints
        self.loaded_value = None

        self.valueChanged.connect(self.stateChanged)

    def validate_field(self, value):
        if not isinstance(value, int):
            return False
        minimum = self.constraints.get('minimum', float('-inf'))
        maximum = self.constraints.get('maximum', float('inf'))
        return minimum <= value <= maximum

    def load_value(self, value):
        if not self.validate_field(value):
            value = 0
        self.setValue(value)
        self.loaded_value = value

    @property
    def current_value(self):
        return self.value()


class OneOfRadioFrameField(QtWidgets.QFrame):
    stateChanged = QtCore.pyqtSignal(str)

    def __init__(self, option, choices):
        super().__init__()
        self.option = option
        self.choices = choices

        self.choice_button_map = {}

        layout = QtWidgets.QVBoxLayout(self)
        for choice in self.choices:
            btn = QtWidgets.QRadioButton(choice)
            btn.clicked.connect(lambda: self.stateChanged.emit(self.current_value))
            self.choice_button_map[choice] = btn
            layout.addWidget(btn)

    def validate_field(self, value):
        return value in self.choices

    def load_value(self, value):
        if self.validate_field(value):
            self.choice_button_map[value].setChecked(True)
            self.loaded_value = value
        else:
            for btn in self.choice_button_map.values():
                btn.setChecked(False)

    @property
    def current_value(self):
        for value, button in self.choice_button_map.items():
            if button.isChecked():
                return value


class OneOfComboBoxField(QtWidgets.QComboBox):
    stateChanged = QtCore.pyqtSignal(str)

    def __init__(self, option, choices):
        super().__init__()
        self.option = option
        self.choices = choices

        for choice in self.choices:
            self.addItem(choice)

        self.currentTextChanged.connect(self.stateChanged)

    def validate_field(self, value):
        return value in self.choices

    def load_value(self, value):
        if self.validate_field(value):
            self.setCurrentIndex(self.choices.index(value))
            self.loaded_value = value

    @property
    def current_value(self):
        return self.currentText()


class OneOfField:
    def __new__(cls, option):
        field_type = api.get_option_tree().get_type(option)
        choices = [choice.strip('" ') for choice in field_type.split('one of ', 1)[1].split(',')]

        if len(choices) < 5:
            return OneOfRadioFrameField(option, choices)
        else:
            return OneOfComboBoxField(option, choices)


class ExpressionField(QtWidgets.QTextEdit):
    stateChanged = QtCore.pyqtSignal(str)

    def __init__(self, option, **constraints):
        super().__init__()
        self.option = option
        self.constraints = constraints
        self.loaded_value = None

        self.setFont(QtGui.QFont("Monospace"))

        self.textChanged.connect(lambda: self.stateChanged.emit(self.current_value))

    def validate_field(self, value):
        return isinstance(value, str)

    def load_value(self, value):
        if not self.validate_field(value):
            value = ''
        self.setText(value)
        self.loaded_value = value

    @property
    def current_value(self):
        return self.toPlainText()


class DoNothingField(QtWidgets.QLabel):
    stateChanged = QtCore.pyqtSignal()

    def __init__(self, option, **constraints):
        super().__init__()
        self.loaded_value = None

    @classmethod
    def validate_field(cls, value):
        return value == cls.legal_value

    def load_value(self, value):
        self.setText(self.label_text)
        self.loaded_value = value

    @property
    def current_value(self):
        return self.legal_value


class NullField(DoNothingField):
    legal_value = None
    label_text = 'NULL'


class UndefinedField(NullField):
    legal_value = option_tree.Undefined
    label_text = 'Undefined'


class NotImplementedField(DoNothingField):
    legal_value = None
    label_text = 'Not Implemented'

    @staticmethod
    def validate_field(value):
        return False


ReferenceField = NotImplementedField
