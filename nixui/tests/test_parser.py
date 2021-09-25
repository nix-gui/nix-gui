import os
import pytest
from nixui.options import parser


SAMPLES_PATH = 'tests/sample'


@pytest.mark.datafiles(SAMPLES_PATH)
def test_get_all_option_values():
    assert parser.get_all_option_values(
        os.path.abspath(os.path.join(SAMPLES_PATH, 'configuration.nix'))
    )


@pytest.mark.datafiles(SAMPLES_PATH)
def test_get_all_option_values_correct_attributes():
    module_path = os.path.abspath(os.path.join(SAMPLES_PATH, 'configuration.nix'))
    found_attrs = set([str(x) for x in parser.get_all_option_values(module_path)])

    # exclude `imports`
    configuration_nix_attrs = {
        'environment.etc',
        'environment.systemPackages',
        'fileSystems',
        'fonts.fontDir.enable',
        'fonts.fonts',
        'hardware.bluetooth.enable',
        'hardware.bluetooth.settings',
        'hardware.opengl.driSupport32Bit',
        'hardware.pulseaudio.enable',
        'hardware.pulseaudio.extraModules',
        'hardware.pulseaudio.package',
        'hardware.pulseaudio.support32Bit',
        'networking.firewall.allowPing',
        'networking.firewall.allowedTCPPorts',
        'networking.firewall.enable',
        'networking.hostId',
        'networking.hostName',
        'networking.networkmanager.enable',
        'programs.vim.defaultEditor',
        'programs.zsh.enable',
        'security.sudo.extraConfig',
        'services.blueman.enable',
        'services.bookstack.nginx',
        'services.dbus.enable',
        'services.dbus.packages',
        'services.logind.lidSwitch',
        'services.printing.drivers',
        'services.printing.enable',
        'services.redshift.enable',
        'services.redshift.temperature.day',
        'services.redshift.temperature.night',
        'services.unbound.enable',
        'services.unbound.settings',
        'services.xserver.displayManager.lightdm.enable',
        'services.xserver.displayManager.sessionCommands',
        'services.xserver.enable',
        'services.xserver.synaptics.enable',
        'services.xserver.windowManager.i3.enable',
        'services.xserver.xkbOptions',
        'sound.enable',
        'system.stateVersion',
        'time.timeZone',
        'users.extraGroups',
        'users.extraUsers',
        'virtualisation.libvirtd.enable'
    }
    hardware_configuration_nix_attrs = {
        'boot.extraModulePackages',
        'boot.initrd.availableKernelModules',
        'boot.initrd.kernelModules',
        'boot.kernelModules',
        'swapDevices'
    }

    # TODO: add these to the expected set when `lib.nix` recurses into submodules
    configuration_nix_submodule_attrs = {
        'users.extraUsers.isNormalUser',
        'users.extraUsers.home',
        'users.extraUsers.description',
        'users.extraUsers.extraGroups',
        'users.extraUsers.uid',
        'users.extraUsers.shell',
        'users.extraGroups.vboxusers.members',
        'services.bookstack.nginx.listen',
        'services.unbound.settings.server.cache-min-ttl',
        'services.unbound.settings.server.do-tcp',
        'services.unbound.settings.server.ssl-upstream',
        'services.unbound.settings.forwrad-zone',
        'environment.etc."resolv.conf".text',
        'hardware.bluetooth.settings.General.Enable',
        'fileSystems."/".options',
    }
    hardware_configuration_nix_submodule_attrs = {
        'fileSystems."/".device',
        'fileSystems."/".fsType',
        'fileSystems."/boot".device',
        'fileSystems."/boot".fsType',
        'fileSystems."/home".fsType',
        'fileSystems."/home".device',
        'fileSystems."/home/geir/media".device',
        'fileSystems."/home/geir/media".fsType',
    }

    # TODO: add cases when `lib.nix` recurses into lists, e.g.
    # 'swapDevices.[0].device', 'users.extraUsers.sample'.extraGroups.[3]'

    expected_attrs = configuration_nix_attrs | hardware_configuration_nix_attrs
    assert found_attrs == expected_attrs
