import os
import pytest
from nixui import state_model


SAMPLES_PATH = 'tests/sample'


@pytest.mark.parametrize('option_loc,new_value', [
    ('sound.enable', False),  # boolean
    ('services.logind.lidSwitch', 'dosomething'),  # string
    ('services.redshift.temperature.day', 1000),  # integer
    ('services.networking.firewall.allowedTCPPorts', [1, 2, 3, 4, 5]),  # list of ints
    #('users.extraUsers.sample.isNormalUser', False),  # modify submodule
])
@pytest.mark.datafiles(SAMPLES_PATH)
def test_load_edit_save(option_loc, new_value):
    """
    Given the option passed,
    - extract the given option from SAMPLES_PATH/configuration.nix via state_model
    - store ins value in memory
    - create a new state_model for SAMPLES_PATH/empty.nix
    - inject options value into empty.nix
    - extract options value from empty.nix in new state_model and compare value to original value from configuration.nix
    """
    os.environ['CONFIGURATION_PATH'] = os.path.abspath(os.path.join(SAMPLES_PATH, 'configuration.nix'))
    os.environ['NIXGUI_CONFIGURATION_PATH_CAN_BE_CORRUPTED'] = 'true'
    # open, update, save
    m0 = state_model.StateModel()
    v0 = m0.get_value(option_loc)
    m0.record_update(option_loc, new_value)
    print(m0.get_update_set())
    m0.persist_updates()

    # reopen, verify
    m1 = state_model.StateModel()
    v1 = m1.get_value(option_loc)
    assert v1 == new_value

    # reset, verify same as original
    m1.record_update(option_loc, v0)
    m1.persist_updates()

    m2 = state_model.StateModel()
    v2 = m2.get_value(option_loc)
    assert v0 == v2
