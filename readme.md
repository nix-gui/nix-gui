# Nix-Gui

Make NixOS usable for non-technical users through a settings / package
management GUI.

(Work in progress: more features and refinement necessary to meet the
above goal)

[*screenshots/historical_2021_10_06.png*]{.spurious-link
target="screenshots/historical_2021_10_06.png"}

[*screenshots/historical_search_2021_10_10.png*]{.spurious-link
target="screenshots/historical_search_2021_10_10.png"}

## Using

Prerequisites:

-   Ensure NixOS is installed

Run

-   `nix run github:nix-gui/nix-gui`{.verbatim}

Print help string

-   `nix run github:nix-gui/nix-gui -- --help`{.verbatim}

If you don\'t have [Nix Flakes](https://nixos.wiki/wiki/Flakes) enabled,
either

-   Run
    `nix --experimental-features 'nix-command flakes' run github:nix-gui/nix-gui`{.verbatim},
    or
-   Set
    `nix.extraOptions = ''experimental-features = nix-command flakes'';`{.verbatim}
    in `configuration.nix`{.verbatim} and rebuild to enable.

For details on how to use Nix-Gui, see the [*Usage*]{.spurious-link
target="docs/usage.md"} page.

## Motives

The declarative nature of NixOS provides it the capability of being
**the most user friendly GNU/Linux distribution.** No more [editing
dotfiles](https://github.com/nix-community/home-manager),
`/etc`{.verbatim} files, manually writing timers, services, running
commands to manage and create users and groups, etc. NixOS integrates
all of that into a declarative system, and this project integrates
NixOS\' declarative system into a GUI.

### Serve Users Unfamiliar with or Learning Nix

Nix-Gui is a configuration management tool designed for those who
haven\'t mastered the (arguably difficult) nix language. It is also an
attempt to replicate the ease of use of popular configuration systems
including

-   [Unity Control Center
    (Ubuntu)](https://packages.ubuntu.com/search?keywords=unity-control-center),
    not used anymore
-   [Cinnamon Settings (Linux
    Mint)](https://github.com/linuxmint/cinnamon/tree/master/files/usr/share/cinnamon/cinnamon-settings)
-   [Synaptic Package Manager](https://www.nongnu.org/synaptic/)

Nix-Gui is designed to gradually and comfortably teach users about the
mechanics of the nix language and nixpkgs.

### Serve as an Effective System Management Tool for Experienced Users

At the most advanced level, and once feature parity has been achieved.
Power users should be capable of changing system configuration, creating
system ISOs, [deploying systems to the
cloud](https://github.com/NixOS/nixops), etc in Nix-Gui more
intelligibly and faster than through their traditional means of writing
a nix module.

### Serve Mobile Users

An additional motive for this project is to enable system configuration
for [mobile devices](https://mobile.nixos.org/) without having to type
code on your phone.

## Functionality

Nix-Gui is a tool which loads data including option paths, option types,
default values, configured values, descriptions, etc. The option
hierarchy is made explorable and the value of individual options are
editable. Changes are committed by writing to modules within the
configuration path.

This data is retrieved from `<nixos/nixpkgs>`{.verbatim} and from the
configuration path via `NIX_PATH`{.verbatim}
`nixos-configuration`{.verbatim}.

### Features

-   View and edit the state of options using type-specific widgets (e.g.
    textbox for strings)
    -   View and edit the actual nix expression defining an option
    -   View metadata of an option including type and definition
-   Save changes to a relevant module in the configuration path
    -   \"Diff\" to show option changes not yet committed to disk
-   Explore the hierarchy of options
    -   Utilize color indicators of which options have been set
-   Search options based on options path, type, and description
-   Undo changes to options

## Major Shortcomings to be Fixed

Currently there are a few major limitations to Nix-Gui, including

-   Documentation is can be improved.
-   Nix-Gui has yet to be thoroughly vetted, therefore the configuration
    path is copied to `~/.config/nixgui/configurations/`{.verbatim}, in
    which all changes made by Nix-Gui are saved.
-   Some option types aren\'t handled yet (e.g. `package`{.verbatim},
    `lambda`{.verbatim}, and specific types like
    `ncdns.conf configuration type`{.verbatim},
    `systemd option`{.verbatim}). These options can only be edited as a
    nix expression, as they do not have a matching widget.

## Documentation

-   [*Usage*]{.spurious-link target="docs/usage.md"}
-   Development
    -   [*Development Goals*]{.spurious-link
        target="docs/development/goals.md"}
    -   [*Nix-Gui Architecture*]{.spurious-link
        target="docs/development/architecture.md"}
    -   [*Development Commands*]{.spurious-link
        target="docs/development/commands.md"}
-   [*References*]{.spurious-link target="docs/references.md"}

## Contributing

Developers and users, if you want to help please

-   Run the application and submit bug report and feature request issues
    on GitHub.
-   Contribute to the [UX
    Survey](https://github.com/nix-gui/nix-gui/issues/129).
-   Read the Development documentation in the section above.
-   Review existing [pull
    requests](https://github.com/nix-gui/nix-gui/pulls).
-   See [good first
    issues](https://github.com/nix-gui/nix-gui/labels/good%20first%20issue).
-   Create issues to ask questions about code, documentation, etc (there
    are no dumb questions).
-   Contribute to important dependencies including
    [rnix-parser](https://github.com/nix-community/rnix-parser/) and
    [rnix-lsp](https://github.com/nix-community/rnix-lsp).
-   Join the matrix below to discuss.

## Matrix

Development, support, discussion on Matrix
`#nix-gui:nixos.org`{.verbatim}
[https://matrix.to/#/#nix-gui:nixos.org](https://matrix.to/#/#nix-gui:nixos.org)
