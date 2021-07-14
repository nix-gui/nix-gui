{
  imports = [
    ./hardware_configuration.nix # Include the results of the hardware scan
  ];

  sound.enable = true;

  system.stateVersion = "20.09";
}
