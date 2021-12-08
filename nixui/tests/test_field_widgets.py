from nixui.graphics import field_widgets
from nixui.options import option_tree

import pytest

def test_integer_field_default(qapp):
    widget = field_widgets.IntegerField("")
    assert widget.current_value == 0

@pytest.mark.parametrize("value", [(8), (10), (63)])
def test_integer_field_input(qapp, value):
    widget = field_widgets.IntegerField("")
    widget.load_value(value)
    assert widget.current_value == value

def test_text_field_default(qapp):
    widget = field_widgets.TextField("")
    assert widget.current_value == ""

@pytest.mark.parametrize("value", [("Testing 123"), ("Hello World!"), ("Something or other")])
def test_text_field_input(qapp, value):
    widget = field_widgets.TextField("")
    widget.load_value(value)
    assert widget.current_value == value

def test_boolean_field_default(qapp):
    widget = field_widgets.BooleanField("")
    assert widget.current_value == False

@pytest.mark.parametrize("value", [(True), (False)])
def test_boolean_field_input(qapp, value):
    widget = field_widgets.BooleanField("")
    widget.load_value(value)
    assert widget.current_value == value

def test_float_field_default(qapp):
    widget = field_widgets.FloatField("")
    assert widget.current_value == 0.0

@pytest.mark.parametrize("value", [(9.8), (3.14), (10.64)])
def test_float_field_input(qapp, value):
    widget = field_widgets.FloatField("")
    widget.load_value(value)
    assert widget.current_value == value

def test_null_field(qapp):
    widget = field_widgets.NullField("")
    assert widget.current_value == None

def test_undefined_field(qapp):
    widget = field_widgets.UndefinedField("")
    assert widget.current_value == option_tree.Undefined

def test_not_implemented_field(qapp):
    pass