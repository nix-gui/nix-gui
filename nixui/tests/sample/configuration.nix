# Example configuration.nix modified to include various basic configurations and edge cases
# This file should NOT be considered as a useful example for a real system configuration

# https://github.com/lapp0/nix-gui/issues/14 utf-8 breaking character: ’

{ config, pkgs, ... }:
let
  vars = import ./vars.nix {};
in {
  imports = [
    ./hardware-configuration.nix
  ];


  security.sudo.extraConfig = ''
  sample ALL = NOPASSWD: echo hi
  '';

  users.extraGroups.vboxusers.members = [ "sample" ];
  users.extraUsers.sample = {
    isNormalUser = true;
    home = "/home/sample";
    description = "Sample";
    extraGroups = ["wheel" "networkmanager" "vboxsf" "dialout" "libvirtd"];
    uid = 1000;
    shell = "/run/current-system/sw/bin/zsh";
  };

  sound.enable = true;

  # multiple `services` definition locations
  services.dbus = {
    packages = [ pkgs.gnome3.gnome_terminal ];
    enable = true;
  };

  services = {

    # test list of submodules
    bookstack.nginx.listen = [
      {
        addr = "195.154.1.1";
        port = 443;
        ssl = true;
      }
      {
        addr = "192.154.1.1";
        port = 80;
      }
    ];

    unbound = {
      enable = true;  # local dns
      settings = {
        server = {
          cache-min-ttl = "1000";
          do-tcp = "yes";
          ssl-upstream = "yes";
        };
        forward-zone = [{
          forward-addr = [
            "dot-ch.blahdns.com@853"  # https://blahdns.com/
	          "dot-sg.blahdns.com@853"  # https://blahdns.com/
          ];
          name = ".";
          forward-tls-upstream = "yes";
        }];
      };
    };

    logind.lidSwitch = "ignore";

    printing = {
      enable = true;
      drivers = [ pkgs.gutenprint ];
    };

    xserver = {
      enable = true;
      xkbOptions = "ctrl:nocaps";

      synaptics.enable = false;

      windowManager.i3.enable = true;
      displayManager.lightdm.enable = true;

      displayManager.sessionCommands = ''
        ${pkgs.xlibs.xsetroot}/bin/xsetroot -cursor_name left_ptr

        ${pkgs.xorg.xmodmap}/bin/xmodmap ~/.Xmodmap

        ${pkgs.networkmanagerapplet}/bin/nm-applet &
      '';
    };

    redshift = {
      enable = false;
      temperature.day = 6500;
      temperature.night = 4500;
    };

  };

  environment.etc = {
    "resolv.conf".text = ''
      nameserver 127.0.0.1  # unbound dns
      options edns0
    '';
  };

  networking = {
    networkmanager.enable = true;

    hostName = "fakehost";
    hostId = "99999999";

    firewall.enable = true;
    firewall.allowedTCPPorts = [ 80 443 ];
    firewall.allowPing = true;
  };

  programs = {
    zsh.enable = true;
    vim.defaultEditor = true;  # don't actually use vim, this is just an example file
  };

  fonts = {
    fontDir.enable = true;
    fonts = with pkgs; [
      go-font
      sudo-font
    ];
  };

  time.timeZone = "	Atlantic/Madeira";

  hardware.opengl.driSupport32Bit = true;

  services.blueman.enable = true;
  hardware = {
    bluetooth = {
      enable = true;
      settings = {
        General = {
          Enable = "Source,Sink,Media,Socket";
        };
      };
    };
  };
  hardware.pulseaudio = {
    enable = true;
    package = pkgs.pulseaudioFull;
    extraModules = [ pkgs.pulseaudio-modules-bt ];
    support32Bit = true;
  };

  virtualisation.libvirtd.enable = true;

  fileSystems."/".options = [ "noatime" "nodiratime" "discard" ];

  # The NixOS release to be compatible with for stateful data such as databases.
  # This doesn't need to be changed in new versions, however some programs will need
  # this variable to change to be upgraded. Read the effects of the new state.
  system.stateVersion = "20.03";


  environment.systemPackages = with pkgs; [
    blueman
    file
    git
    gnupg
    irssi
    jupyter

    (python3.withPackages(ps: with ps; [
      flake8
	    virtualenv
    ]))

    zip
  ];
}
