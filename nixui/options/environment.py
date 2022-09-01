import os


def get_nixpath_element(nix_path, element, default_value = None):
    nixos_configs = [elem for elem in nix_path.split(':') if elem.startswith(f'{element}=')]
    assert len(nixos_configs) <= 1, f'more than one {element} defined in NIX_PATH'
    try:
        assert len(nixos_configs) > 0, f'no {element} defined in NIX_PATH'
    except AssertionError as error:
        if default_value:
            print(f"get_nixpath_element: element={element}: value is unset. using default value: {default_value}")
            return default_value
        raise error
    return nixos_configs[0].removeprefix(f'{element}=')


def get_nixos_config_path(nix_path=os.environ['NIX_PATH']):
    return get_nixpath_element(nix_path, 'nixos-config', '/etc/nixos/configuration.nix')


def get_nixpkgs_path(nix_path=os.environ['NIX_PATH']):
    return get_nixpath_element(nix_path, 'nixpkgs')
