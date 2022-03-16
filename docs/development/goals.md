# Intuition

Nix-Gui is UX focused. All counterintuitive elements should be
considered a bug. Bug reports can be filed at
<https://github.com/nix-gui/nix-gui/issues> There are no stupid
questions. This program is intended to make NixOS usable by someone with
basic competence in Ubuntu, Mint, Windows, or OS X.

# Comprehension

Nix-Gui strives to provide the ability to make any system changes that
are possible by editing a nix module..

# Sane Code

Nix-Gui is a graphical program written in python with recursively
defined elements to explore and define options. Additional functionality
should be designed cleanly with separation of concerns in mind.

# Speed

Once built, Nix-Gui targets a 100ms load time for all form changes. This
will be achieved through optimizing various data-structures and
algorithms, and implementing caching.
