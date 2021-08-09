from nixui.options.option_tree import OptionTree, OptionData
from nixui.options.attribute import Attribute
from nixui.options.option_definition import OptionDefinition


def test_option_tree_simple():
    attr = Attribute(['foo', 'bar'])
    t = OptionTree(
        {attr: {'_type': 'mytype'}},
        {attr: OptionDefinition.from_object('myvalue')},
    )
    assert t.get_type(attr) == 'mytype'
    assert t.get_definition(attr).obj == 'myvalue'


def test_option_tree_simple_attr_set():
    attr = Attribute(['foo', 'bar'])
    t = OptionTree(
        {attr: {'_type': 'attribute set of strings'}},
        {},
    )
    child_attr = Attribute(['foo', 'bar', 'baz'])
    t.set_definition(child_attr, OptionDefinition.from_object('val'))
    assert t.get_type(child_attr) == 'string'
    assert t.get_definition(child_attr).obj == 'val'


def test_option_tree_attr_set_of_submodules():
    pass
