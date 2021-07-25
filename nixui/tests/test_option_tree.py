from nixui.options.option_tree import OptionTree, OptionData
from nixui.options.attribute import Attribute


def test_option_tree_simple():
    attr = Attribute(['foo', 'bar'])
    t = OptionTree(
        {attr: {'_type': 'mytype'}},
        {attr: 'myvalue'},
    )
    assert t.get_type(attr) == 'mytype'
    assert t.get_value(attr) == 'myvalue'


def test_option_tree_simple_attr_set():
    attr = Attribute(['foo', 'bar'])
    t = OptionTree(
        {attr: {'_type': 'attribute set of strings'}},
        {},
    )
    child_attr = Attribute(['foo', 'bar', 'baz'])
    t.set_value(child_attr, 'val')
    assert t.get_type(child_attr) == 'string'
    assert t.get_value(child_attr) == 'val'


def test_option_tree_attr_set_of_submodules():
    pass
