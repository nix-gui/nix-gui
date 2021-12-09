import os
import pytest
from nixui.options import parser, option_definition, state_update
from nixui.options.attribute import Attribute


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
    expected_attrs = {
        'boot.extraModulePackages',
        'boot.initrd.availableKernelModules',
        'boot.initrd.availableKernelModules."[0]"',
        'boot.initrd.availableKernelModules."[1]"',
        'boot.initrd.availableKernelModules."[2]"',
        'boot.initrd.availableKernelModules."[3]"',
        'boot.initrd.availableKernelModules."[4]"',
        'boot.initrd.availableKernelModules."[5]"',
        'boot.initrd.kernelModules',
        'boot.kernelModules',
        'boot.kernelModules."[0]"',
        'boot.kernelModules."[1]"',
        'environment.etc',
        'environment.etc."resolv.conf".text',
        'environment.systemPackages',
        'fileSystems."/"',
        'fileSystems."/".device',
        'fileSystems."/".fsType',
        'fileSystems."/".label',
        'fileSystems."/".options',
        'fileSystems."/".options."[0]"',
        'fileSystems."/".options."[1]"',
        'fileSystems."/".options."[2]"',
        'fileSystems."/boot"',
        'fileSystems."/boot".device',
        'fileSystems."/boot".fsType',
        'fileSystems."/home"',
        'fileSystems."/home".device',
        'fileSystems."/home".fsType',
        'fileSystems."/home/sample/media"',
        'fileSystems."/home/sample/media".device',
        'fileSystems."/home/sample/media".fsType',
        'fonts',
        'fonts.fontDir.enable',
        'fonts.fonts',
        'hardware.bluetooth',
        'hardware.bluetooth.enable',
        'hardware.bluetooth.settings',
        'hardware.bluetooth.settings.General',
        'hardware.bluetooth.settings.General.Enable',
        'hardware.enableRedistributableFirmware',
        'hardware.opengl.driSupport32Bit',
        'hardware.pulseaudio',
        'hardware.pulseaudio.enable',
        'hardware.pulseaudio.extraModules',
        'hardware.pulseaudio.extraModules."[0]"',
        'hardware.pulseaudio.package',
        'hardware.pulseaudio.support32Bit',
        'networking',
        'networking.firewall.allowPing',
        'networking.firewall.allowedTCPPorts',
        'networking.firewall.allowedTCPPorts."[0]"',
        'networking.firewall.allowedTCPPorts."[1]"',
        'networking.firewall.enable',
        'networking.hostId',
        'networking.hostName',
        'networking.networkmanager.enable',
        'programs',
        'programs.vim.defaultEditor',
        'programs.zsh.enable',
        'security.sudo.extraConfig',
        'services.blueman.enable',
        'services.bookstack.nginx.listen',
        'services.bookstack.nginx.listen."[0]"',
        'services.bookstack.nginx.listen."[0]".addr',
        'services.bookstack.nginx.listen."[0]".port',
        'services.bookstack.nginx.listen."[0]".ssl',
        'services.bookstack.nginx.listen."[1]"',
        'services.bookstack.nginx.listen."[1]".addr',
        'services.bookstack.nginx.listen."[1]".port',
        'services.dbus',
        'services.dbus.enable',
        'services.dbus.packages',
        'services.dbus.packages."[0]"',
        'services.logind.lidSwitch',
        'services.printing',
        'services.printing.drivers',
        'services.printing.drivers."[0]"',
        'services.printing.enable',
        'services.redshift.enable',
        'services.redshift.temperature.day',
        'services.redshift.temperature.night',
        'services.unbound',
        'services.unbound.enable',
        'services.unbound.settings',
        'services.unbound.settings.forward-zone',
        'services.unbound.settings.forward-zone."[0]"',
        'services.unbound.settings.forward-zone."[0]".forward-addr',
        'services.unbound.settings.forward-zone."[0]".forward-addr."[0]"',
        'services.unbound.settings.forward-zone."[0]".forward-addr."[1]"',
        'services.unbound.settings.forward-zone."[0]".forward-tls-upstream',
        'services.unbound.settings.forward-zone."[0]".name',
        'services.unbound.settings.server',
        'services.unbound.settings.server.cache-min-ttl',
        'services.unbound.settings.server.do-tcp',
        'services.unbound.settings.server.ssl-upstream',
        'services.xserver',
        'services.xserver.displayManager.lightdm.enable',
        'services.xserver.displayManager.sessionCommands',
        'services.xserver.enable',
        'services.xserver.synaptics.enable',
        'services.xserver.windowManager.i3.enable',
        'services.xserver.xkbOptions',
        'sound.enable',
        'swapDevices',
        'swapDevices."[0]"',
        'swapDevices."[0]".device',
        'system.stateVersion',
        'time.timeZone',
        'users.extraGroups.vboxusers.members',
        'users.extraGroups.vboxusers.members."[0]"',
        'users.extraUsers.sample',
        'users.extraUsers.sample.description',
        'users.extraUsers.sample.extraGroups',
        'users.extraUsers.sample.extraGroups."[0]"',
        'users.extraUsers.sample.extraGroups."[1]"',
        'users.extraUsers.sample.extraGroups."[2]"',
        'users.extraUsers.sample.extraGroups."[3]"',
        'users.extraUsers.sample.extraGroups."[4]"',
        'users.extraUsers.sample.home',
        'users.extraUsers.sample.isNormalUser',
        'users.extraUsers.sample.shell',
        'users.extraUsers.sample.uid',
        'virtualisation.libvirtd.enable'
    }
    assert found_attrs == expected_attrs


@pytest.mark.datafiles(SAMPLES_PATH)
def test_persist_multiple_updates():
    module_path = os.path.abspath(os.path.join(SAMPLES_PATH, 'configuration.nix'))
    option_def_map = parser.get_all_option_values(module_path)

    # assert sample configuration.nix is as expected prior to updates
    assert Attribute('users.extraUsers.sample.extraGroups') in option_def_map
    assert Attribute('users.extraUsers.renamedsample.extraGroups') not in option_def_map
    assert Attribute('filesystems."/mockpath"') not in option_def_map
    assert option_def_map[Attribute('services.unbound.enable')].obj is True
    assert Attribute('environment.etc."resolv.conf".text') in option_def_map

    # apply updates
    updates = [
        state_update.RenameUpdate(
            Attribute('users.extraUsers.sample'),
            Attribute('users.extraUsers.renamedsample')
        ),
        state_update.CreateUpdate(
            Attribute('filesystems."/mockpath"')
        ),
        state_update.ChangeDefinitionUpdate(
            Attribute('services.unbound.enable'),
            option_def_map[Attribute('services.unbound.enable')],
            option_definition.OptionDefinition.from_object(False)
        ),
        state_update.RemoveUpdate(
            Attribute('environment.etc."resolv.conf"')
        ),
    ]
    parser.persist_updates(module_path, updates)

    option_def_map = parser.get_all_option_values(module_path)

    # assert updates are sane
    assert Attribute('users.extraUsers.sample.extraGroups') not in option_def_map
    assert Attribute('users.extraUsers.renamedsample.extraGroups') in option_def_map
    assert Attribute('filesystems."/mockpath"') in option_def_map
    assert option_def_map[Attribute('services.unbound.enable')].obj is False
    assert Attribute('environment.etc."resolv.conf".text') not in option_def_map
