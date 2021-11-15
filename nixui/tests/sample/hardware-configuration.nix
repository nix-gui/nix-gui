# example borrowed from https://github.com/geokkjer/nixosdotfiles/
{ config, lib, pkgs, modulesPath, ... }:

{
  imports =
    [ (modulesPath + "/installer/scan/not-detected.nix")
    ];

  boot.initrd.availableKernelModules = [ "xhci_pci" "ahci" "nvme" "usbhid" "usb_storage" "sd_mod" ];
  boot.initrd.kernelModules = [ ];
  boot.kernelModules = [ "kvm-amd" "ipvs" ];
  boot.extraModulePackages = [ ];

  fileSystems."/" =
    { device = "/dev/disk/by-label/nixos";
      fsType = "xfs";
    };

  fileSystems."/boot" =
    { device = "/dev/disk/by-label/boot";
      fsType = "vfat";
    };

  fileSystems."/home" =
    { device = "/dev/disk/by-label/home";
      fsType = "xfs";
    };

  fileSystems."/home/sample/media" =
    { device = "/dev/disk/by-uuid/7416be6f-2c6d-1fc9-852c-cf6c8227d38f";
      fsType = "xfs";
    };

  swapDevices =
    [ { device = "/dev/disk/by-uuid/c7c1dcc0-c828-3a36-d44e-efeb602044a8"; }
    ];

}
