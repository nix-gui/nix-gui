import os
import pytest
from nixui.options import api, types


SAMPLES_PATH = 'tests/sample'


@pytest.mark.datafiles(SAMPLES_PATH)
def test_every_type_resolves():
    os.environ['CONFIGURATION_PATH'] = os.path.abspath(os.path.join(SAMPLES_PATH, 'configuration.nix'))
    tree = api.get_option_tree()
    type_strings = set([
        tree.get_type(attr)
        for attr in tree.children(recursive=True)
    ])

    for type_string in type_strings:
        print(type_string)
        types.parse_type(type_string)
