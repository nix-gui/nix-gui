import pytest
from nixui import state_model


SAMPLES_PATH = 'tests/sample'


@pytest.mark.parametrize('option_loc,new_value', [
    (['sound', 'enable'], False),
])
@pytest.mark.datafiles(SAMPLES_PATH)
def test_save_option_value(option_loc, new_value):
    """
    Given the option passed,
    - extract the given option from SAMPLES_PATH/configuration.nix via state_model
    - store ins value in memory
    - create a new state_model for SAMPLES_PATH/empty.nix
    - inject options value into empty.nix
    - extract options value from empty.nix in new state_model and compare value to original value from configuration.nix
    """
    # open, update, save
    m0 = state_model.StateModel()
    v0 = m0.get_value(option_loc)
    m0.record_update(option_loc, new_value)
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


def test_update_submodule():
    pass


def test_update_list_of():
    pass
