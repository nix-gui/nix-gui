from nixui.main import get_nixos_config_path


def test_get_nixos_config():
    config_path = get_nixos_config_path('nixos-config=/etc/nixos/configuration.nix:nixpkgs=/home/example/nixpkgs/')
    assert config_path == '/etc/nixos/configuration.nix'

    config_path = get_nixos_config_path(
        '/home/example/.nix-defexpr/channels:/etc/nixos:nixos-config=/etc/nixos/configuration.nix:nixpkgs=/etc/nixos/nixpkgs'
    )
    assert config_path == '/etc/nixos/configuration.nix'
