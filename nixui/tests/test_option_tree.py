import os

from nixui.options import api, types
from nixui.options.option_tree import OptionTree
from nixui.options.attribute import Attribute
from nixui.options.option_definition import OptionDefinition

import pytest


SAMPLES_PATH = 'tests/sample'


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
        {attr: {'_type': types.AttrsOfType(types.StrType())}},
        {},
    )
    child_attr = Attribute(['foo', 'bar', 'baz'])
    t.set_definition(child_attr, OptionDefinition.from_object('val'))
    assert t.get_type(child_attr) == types.StrType()
    assert t.get_definition(child_attr).obj == 'val'


@pytest.mark.datafiles(SAMPLES_PATH)
def test_set_configuration_loads():
    option_tree = api.get_option_tree(
        os.path.abspath(os.path.join(SAMPLES_PATH, 'set_configuration.nix'))
    )
    for attr, new_definition in option_tree.get_changes(get_configured_changes=True).items():
        # evaluate expression strings
        (attr, new_definition.expression_string)


@pytest.mark.datafiles(SAMPLES_PATH)
def test_list_children_simple():
    option_tree = api.get_option_tree(
        os.path.abspath(os.path.join(SAMPLES_PATH, 'configuration.nix'))
    )
    children = option_tree.children(
        Attribute('networking.firewall.allowedTCPPorts')
    )
    assert [c.configured_definition.obj for c in children.values()] == [80, 443]


@pytest.mark.datafiles(SAMPLES_PATH)
def test_benchmark__hash__(helpers):
    """
    Assert OptionTree hash can be calculated 100,000 times in 1 second
    """
    option_tree = api.get_option_tree(
        os.path.abspath(os.path.join(SAMPLES_PATH, 'configuration.nix'))
    )
    # load in_memory_change_cache with changes
    for i in range(1000):
        option_tree.insert_attribute(Attribute(f'services.unbound.settings.server.foo{i}'))
    option_tree.remove_attribute(Attribute('services.unbound.settings.forward-zone'))
    option_tree.remove_attribute(Attribute('services.bookstack.nginx.listen."[1]"'))
    option_tree.remove_attribute(Attribute('hardware.bluetooth.settings.General'))

    # cache result
    option_tree.count_leaves(Attribute(''))

    # test that recalculating the cache doesn't take long
    root_attr = Attribute('')
    with helpers.timeout(seconds=1) as t:
        for i in range(100000):
            option_tree.count_leaves(root_attr)
            if t.timed_out:
                raise Exception(f'{i} runs before timeout. Calculating OptionTree.__hash__')
