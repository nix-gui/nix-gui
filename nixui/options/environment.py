import os


def get_nixpath_element(nix_path, element):
    nixos_configs = [elem for elem in nix_path.split(':') if elem.startswith(f'{element}=')]
    assert len(nixos_configs) <= 1, f'more than one {element} defined in NIX_PATH'
    assert len(nixos_configs) > 0, f'no {element} defined in NIX_PATH'
    return nixos_configs[0].removeprefix(f'{element}=')


def get_nixos_config_path(nix_path=os.environ['NIX_PATH']):
    return get_nixpath_element(nix_path, 'nixos-config')


def get_nixpkgs_path(nix_path=os.environ['NIX_PATH']):
    return get_nixpath_element(nix_path, 'nixpkgs')
