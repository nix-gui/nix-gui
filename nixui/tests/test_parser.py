import os
import tempfile
import pytest
from nixui.options import parser
from nixui.options.option_definition import OptionDefinition
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


SAMPLE_MODULE_STR = """
    { config, pkgs, ... }:
    {
        imports = [];
        users.extraGroups.vboxusers.members = [ "sample" "sampleB" ];
        users.extraUsers.sample = {
            isNormalUser = true;
            home = "/home/sample";
            description = "Sample";
            extraGroups = ["wheel" "networkmanager" "vboxsf" "dialout" "libvirtd"];
        };

        fileSystems."/".options = [ "noatime" "nodiratime" "discard" ];
        fileSystems."/".label = "sampledrive";
    }
"""
SAMPLE_CHANGES = {
    Attribute('fileSystems."/"'): None,  # delete
    #Attribute('users.extraGroups.vboxusers.members."[1]"'): None,  # delete list element
    Attribute('users.extraUsers.sample.home'): OptionDefinition.from_object("/home/sample_number_2"),  # change
    # TODO: change list element
    Attribute('users.extraGroups.foo'): OptionDefinition.from_object(111),  # create
    Attribute('users.extraUsers.renamedsample.extraGroups."[5]"'): OptionDefinition.from_object("othergroup"),  # create
}


def test_persist_multiple_changes():
    tf = tempfile.NamedTemporaryFile(mode='w')
    tf.write(SAMPLE_MODULE_STR)
    tf.flush()
    module_path = tf.name

    old_option_def_map = parser.get_all_option_values(module_path)
    changed_module_str = parser.calculate_changed_module(module_path, SAMPLE_CHANGES)

    tf = tempfile.NamedTemporaryFile(mode='w')
    tf.write(changed_module_str)
    tf.flush()
    module_path = tf.name

    new_option_def_map = parser.get_all_option_values(module_path)

    # assert changes were made
    assert Attribute('fileSystems."/".options') in old_option_def_map
    assert Attribute('fileSystems."/".options') not in new_option_def_map

    assert Attribute('fileSystems."/".label') in old_option_def_map
    assert Attribute('fileSystems."/".label') not in new_option_def_map

    # TODO: fix
    #assert Attribute('users.extraGroups.vboxusers.members."[1]"') in old_option_def_map
    #assert Attribute('users.extraGroups.vboxusers.members."[1]"') not in new_option_def_map

    assert old_option_def_map[Attribute('users.extraUsers.sample.home')].obj == '/home/sample'
    assert new_option_def_map[Attribute('users.extraUsers.sample.home')].obj == '/home/sample_number_2'

    assert Attribute('users.extraGroups.foo') not in old_option_def_map
    assert new_option_def_map[Attribute('users.extraGroups.foo')].obj == 111

    assert Attribute('users.extraUsers.renamedsample.extraGroups."[5]"') not in old_option_def_map
    assert new_option_def_map[Attribute('users.extraUsers.renamedsample.extraGroups."[5]"')].obj == 'othergroup'

    # delete all changes from both option_def_map's and assert they're equivalent otherwise
    del old_option_def_map[Attribute('fileSystems."/".options')]
    del old_option_def_map[Attribute('fileSystems."/".options."[0]"')]
    del old_option_def_map[Attribute('fileSystems."/".options."[1]"')]
    del old_option_def_map[Attribute('fileSystems."/".options."[2]"')]
    del old_option_def_map[Attribute('fileSystems."/".label')]
    #del old_option_def_map[Attribute('users.extraGroups.vboxusers.members."[1]"')]
    del old_option_def_map[Attribute('users.extraUsers.sample.home')]
    del old_option_def_map[Attribute('users.extraUsers.sample')]
    del new_option_def_map[Attribute('users.extraUsers.sample')]
    del new_option_def_map[Attribute('users.extraUsers.sample.home')]
    del new_option_def_map[Attribute('users.extraGroups.foo')]
    del new_option_def_map[Attribute('users.extraUsers.renamedsample.extraGroups."[5]"')]
    Attribute('users.extraGroups.vboxusers.members."[1]"')
    assert {k: v.expression_string for k, v in new_option_def_map.items()} == {k: v.expression_string for k, v in old_option_def_map.items()}


def test_sane_placement():
    tf = tempfile.NamedTemporaryFile(mode='w')
    tf.write(SAMPLE_MODULE_STR)
    tf.flush()
    module_path = tf.name
    changed_module_str = parser.calculate_changed_module(module_path, SAMPLE_CHANGES)

    expected_module_str = """
    { config, pkgs, ... }:
    {
        imports = [];
        users.extraGroups.vboxusers.members = [ "sample" "sampleB" ];
        users.extraGroups.foo = 111;
        users.extraUsers.sample = {
            isNormalUser = true;
            home = "/home/sample_number_2";
            description = "Sample";
            extraGroups = ["wheel" "networkmanager" "vboxsf" "dialout" "libvirtd" "othergroup"];
        };
    }
    """
    assert changed_module_str == expected_module_str, changed_module_str
