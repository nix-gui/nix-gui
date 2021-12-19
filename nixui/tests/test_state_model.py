import os
import pytest
from nixui import state_model
from nixui.options.attribute import Attribute
from nixui.options.option_definition import OptionDefinition


SAMPLES_PATH = 'tests/sample'


@pytest.mark.parametrize('option_loc,new_value', [
    (Attribute('sound.enable'), OptionDefinition.from_object(False)),  # boolean
    (Attribute('services.logind.lidSwitch'), OptionDefinition.from_object('dosomething')),  # string
    (Attribute('services.redshift.temperature.day'), OptionDefinition.from_object(1000)),  # integer
    (Attribute('networking.firewall.allowedTCPPorts'), OptionDefinition.from_object([1, 2, 3, 4, 5])),  # list of ints
    (Attribute('users.extraUsers.sample.isNormalUser'), OptionDefinition.from_object(False)),  # modify submodule
])
@pytest.mark.datafiles(SAMPLES_PATH)
def test_load_edit_save(option_loc, new_value):
    """
    Given the option passed,
    - extract the given option from SAMPLES_PATH/configuration.nix via state_model
    - store ins value in memory
    - create a new state_model
    - extract options value from state_model and compare value to original value from configuration.nix
    """
    os.environ['CONFIGURATION_PATH'] = os.path.abspath(os.path.join(SAMPLES_PATH, 'configuration.nix'))
    # open, update, save
    m0 = state_model.StateModel()
    v0 = m0.get_definition(option_loc)
    m0.change_definition(option_loc, new_value)
    m0.persist_changes()

    # reopen, verify
    m1 = state_model.StateModel()
    v1 = m1.get_definition(option_loc)
    assert v1 == new_value

    # reset, verify same as original
    m1.change_definition(option_loc, v0)
    m1.persist_changes()

    m2 = state_model.StateModel()
    v2 = m2.get_definition(option_loc)
    assert v0 == v2


def test_get_update_set_simple(statemodel):
    statemodel.change_definition(
        Attribute('sound.enable'),
        OptionDefinition.from_object(False)
    )
    statemodel.persist_changes()
    statemodel.change_definition(
        Attribute('sound.enable'),
        OptionDefinition.from_object(True)
    )
    updates = statemodel.option_tree.get_changes()
    assert len(updates) == 1
    update = list(updates.values())[0]
    assert update.obj == True


def test_get_update_set_defined_by_descendent(statemodel):
    # test depends on sample/configuration.nix
    """
      services = {

        # test list of submodules
        bookstack.nginx.listen = [
          {
            addr = "195.154.1.1";
            port = 443;
            ssl = true;
          }
          {
            addr = "192.154.1.1";
            port = 80;
          }
        ];
        ...
    """
    statemodel.change_definition(
        Attribute('services.bookstack.nginx.listen."[0]".addr'),
        OptionDefinition.from_object('10.0.0.1')
    )
    statemodel.change_definition(
        Attribute('services.bookstack.nginx.listen."[1]".port'),
        OptionDefinition.from_object(101)
    )
    updates = statemodel.option_tree.get_changes()
    assert len(updates) == 2

    assert updates[Attribute('services.bookstack.nginx.listen."[0]".addr')].obj == "10.0.0.1"
    assert updates[Attribute('services.bookstack.nginx.listen."[1]".port')].obj == 101


def test_change_definition_simple(minimal_state_model):
    start_hash = hash(minimal_state_model.option_tree)

    minimal_state_model.add_new_option(Attribute('myAttrs'))
    assert Attribute('myAttrs.newAttribute') in set(minimal_state_model.option_tree.iter_attributes())

    # assert undefined
    assert minimal_state_model.get_definition(Attribute('myAttrs.newAttribute')).is_undefined

    # change
    minimal_state_model.change_definition(Attribute('myAttrs.newAttribute'), OptionDefinition.from_object(5))
    assert minimal_state_model.get_definition(Attribute('myAttrs.newAttribute')).obj == 5

    # revert
    minimal_state_model.undo()
    assert minimal_state_model.get_definition(Attribute('myAttrs.newAttribute')).is_undefined

    assert hash(minimal_state_model.option_tree) == start_hash


def test_add_new_option_simple(minimal_state_model):
    start_hash = hash(minimal_state_model.option_tree)

    minimal_state_model.add_new_option(Attribute('myAttrs'))
    assert len(set(minimal_state_model.option_tree.iter_attributes())) == 4
    assert Attribute('myAttrs.newAttribute') in set(minimal_state_model.option_tree.iter_attributes())

    # revert
    minimal_state_model.undo()
    assert len(set(minimal_state_model.option_tree.iter_attributes())) == 3
    assert Attribute('myAttrs.newAttribute') not in set(minimal_state_model.option_tree.iter_attributes())

    assert hash(minimal_state_model.option_tree) == start_hash


def test_rename_option_simple(minimal_state_model):
    start_hash = hash(minimal_state_model.option_tree)

    # rename
    minimal_state_model.rename_option(Attribute('myAttrs'), Attribute('myAttrs2'))
    assert Attribute('myAttrs') not in set(minimal_state_model.option_tree.iter_attributes())
    assert Attribute('myAttrs2') in set(minimal_state_model.option_tree.iter_attributes())

    # revert
    minimal_state_model.undo()
    assert Attribute('myAttrs') in set(minimal_state_model.option_tree.iter_attributes())
    assert Attribute('myAttrs2') not in set(minimal_state_model.option_tree.iter_attributes())

    assert hash(minimal_state_model.option_tree) == start_hash


def test_remove_option_simple(minimal_state_model):
    minimal_state_model.add_new_option(Attribute('myAttrs'))
    start_hash = hash(minimal_state_model.option_tree)

    # remove
    minimal_state_model.remove_option(Attribute('myAttrs.newAttribute'))
    assert Attribute('myAttrs.newAttribute') not in set(minimal_state_model.option_tree.iter_attributes())

    # revert
    minimal_state_model.undo()
    assert Attribute('myAttrs.newAttribute') in set(minimal_state_model.option_tree.iter_attributes())

    assert hash(minimal_state_model.option_tree) == start_hash
