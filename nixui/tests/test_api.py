import os
import pytest
from nixui import api

SAMPLES_PATH = 'tests/sample'


@pytest.mark.datafiles(SAMPLES_PATH)
def test_get_option_data():
    return True  # TODO: remove when evaluation doesn't require `nix-build`
    os.environ['CONFIGURATION_PATH'] = os.path.join(SAMPLES_PATH, 'configuration.nix')
    assert api.get_option_data()
