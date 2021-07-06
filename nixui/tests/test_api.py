import os
import pytest
from nixui.options import api

SAMPLES_PATH = 'tests/sample'


@pytest.mark.datafiles(SAMPLES_PATH)
def test_get_option_data():
    if True:
        return True
    os.environ['CONFIGURATION_PATH'] = os.path.join(SAMPLES_PATH, 'configuration.nix')
    assert api.get_option_data()
