import re

from PyQt5 import QtWidgets, QtGui, QtCore

from nixui.options import api, option_tree, option_definition, types
from nixui.graphics import color_indicator, richtext, generic_widgets, toggle_switch


# TODO: fix this hacky handling of `Redirect` (#109)
class Redirect(QtWidgets.QLabel):
    """
    not actual fields or widgets, but encode information to
    allow for redirection when its corresponding button is pressed
    """
    stateChanged = QtCore.pyqtSignal(str)
    def __init__(self, option, *args, **kwargs):
        super().__init__()
        pass


class SubmoduleRedirect(Redirect):
    option_type = types.SubmoduleType
    name = "Submodule"


class ListOfRedirect(Redirect):
    option_type = types.ListOfType
    name = "List of"


class AttrsRedirect(Redirect):
    option_type = types.AttrsType
    name = "Attrs"


class AttrsOfRedirect(Redirect):
    option_type = types.AttrsOfType
    name = "Attrs of"


class BooleanField(toggle_switch.ToggleSwitch):
    name = "Boolean"

    def __init__(self, option, **constraints):
        super().__init__(
            on_text='True',
            off_text='False',
        )
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
    name = "String"
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
    name = "Int"
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
    name = "One of"
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
    name = 'One of'
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
    name = "expression"
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
    name = "Null"
    legal_value = None
    label_text = 'NULL'


class UndefinedField(NullField):
    name = "Undefined"
    legal_value = option_tree.Undefined
    label_text = 'Undefined'


class NotImplementedField(DoNothingField):
    name = "Not Implemented!"
    legal_value = None
    label_text = 'Not Implemented'

    @staticmethod
    def validate_field(value):
        return False


class ReferenceField(NotImplementedField):
    name = "Reference"
