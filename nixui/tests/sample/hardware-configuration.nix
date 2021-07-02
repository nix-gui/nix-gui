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

  fileSystems."/home/geir/media" =
    { device = "/dev/disk/by-uuid/03dbdfd1-9f2e-4755-8d29-32e9352ce043";
      fsType = "xfs";
    };

  swapDevices =
    [ { device = "/dev/disk/by-uuid/4f824f11-cd8e-46af-a5d8-47c6806d76ac"; }
    ];

}
