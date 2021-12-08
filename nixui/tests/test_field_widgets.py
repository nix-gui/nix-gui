from nixui.graphics import field_widgets

import pytest

def test_integer_field():
    widget = field_widgets.IntegerField()
    assert widget.current_value == 0