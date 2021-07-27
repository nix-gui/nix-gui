from nixui.options.option_definition import OptionDefinition


def test_expr_string_from_obj():
    d = OptionDefinition.from_object(True)
    assert d.expression_string.strip() == "true"


def test_obj_from_expr_string():
    d = OptionDefinition.from_expression_string('if true then "bla" else "foo"')
    assert d.obj == "bla"
