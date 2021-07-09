import os
import pytest
from nixui.options import nix_eval

def test_nix_instantiate_eval():
    assert nix_eval.nix_instantiate_eval("true")

def test_nixpkgs_nixos_instantiate_eval():
    assert nix_eval.nix_instantiate_eval("<nixpkgs/nixos>")
