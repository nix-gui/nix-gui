import os
import pytest
from nixui import state_model
from nixui.options.attribute import Attribute
from nixui.options.option_definition import OptionDefinition


SAMPLES_PATH = 'tests/sample'


@pytest.mark.parametrize('option_loc,new_value', [
    (Attribute.from_string('sound.enable'), OptionDefinition.from_object(False)),  # boolean
    (Attribute.from_string('services.logind.lidSwitch'), OptionDefinition.from_object('dosomething')),  # string
    (Attribute.from_string('services.redshift.temperature.day'), OptionDefinition.from_object(1000)),  # integer
    (Attribute.from_string('networking.firewall.allowedTCPPorts'), OptionDefinition.from_object([1, 2, 3, 4, 5])),  # list of ints
    #(Attribute.from_string('users.extraUsers.sample.isNormalUser'), OptionDefinition.from_object(False)),  # modify submodule
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
    os.environ['NIXGUI_CONFIGURATION_PATH_CAN_BE_CORRUPTED'] = 'true'
    # open, update, save
    m0 = state_model.StateModel()
    v0 = m0.get_definition(option_loc)
    m0.record_update(option_loc, new_value)
    m0.persist_updates()

    # reopen, verify
    m1 = state_model.StateModel()
    v1 = m1.get_definition(option_loc)
    assert v1 == new_value

    # reset, verify same as original
    m1.record_update(option_loc, v0)
    m1.persist_updates()

    m2 = state_model.StateModel()
    v2 = m2.get_definition(option_loc)
    assert v0 == v2
