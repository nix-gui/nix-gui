import subprocess


def test_nix_info():
    out = subprocess.check_output([
        'nix', '--version'
    ])
    assert out.decode().startswith('nix (Nix) 2.4')
