import os
import pytest

from nixui.options import nix_eval, attribute


SAMPLES_PATH = 'tests/sample'


def test_nix_instantiate_eval():
    assert nix_eval.nix_instantiate_eval("true")


def test_nixpkgs_nixos_instantiate_eval():
    assert nix_eval.nix_instantiate_eval("<nixpkgs/nixos>")


@pytest.mark.datafiles(SAMPLES_PATH)
def test_get_modules_defined_attrs_set_configuration():
    module_path = os.path.abspath(os.path.join(SAMPLES_PATH, 'set_configuration.nix'))
    result = nix_eval.get_modules_defined_attrs(module_path)
    assert result[attribute.Attribute.from_string('system.stateVersion')]['position']['column'] == 5
    assert result[attribute.Attribute.from_string('system.stateVersion')]['position']['line'] == 5


@pytest.mark.datafiles(SAMPLES_PATH)
def test_get_modules_evaluated_imports():
    module_path = os.path.abspath(os.path.join(SAMPLES_PATH, 'hardware-configuration.nix'))
    result = nix_eval.get_modules_evaluated_import_paths(module_path)
    base_modules_path = nix_eval.resolve_nix_search_path('<nixpkgs/nixos/modules>')
    assert result == [base_modules_path.strip() + "/installer/scan/not-detected.nix"]
