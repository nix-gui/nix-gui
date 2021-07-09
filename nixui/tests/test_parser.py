import os
import pytest
from nixui.options import parser


SAMPLES_PATH = 'tests/sample'


@pytest.mark.datafiles(SAMPLES_PATH)
def test_get_all_option_values():
    assert parser.get_all_option_values(os.path.abspath(os.path.join(SAMPLES_PATH, 'configuration.nix')))
