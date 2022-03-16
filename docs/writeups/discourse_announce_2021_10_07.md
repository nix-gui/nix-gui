<https://discourse.nixos.org/t/announcing-nix-gui/15409>

Announcing Nix-Gui\[link to repo\] (v0.1 beta)

A project with the ambitious goal of making NixOS the most user friendly
GNU/Linux distro.

\[screenshot\]

(Please see the Github readme\[link to readme.org\] for a broader
overview, the Motive, Functionality, Features, and Shortcomings sections
below are quoted from there)

\[bold\]Motive

\[quoted\]The declarative nature of NixOS provides it the capability of
being the most user friendly linux distro. No more editing dotfiles,
/etc files, manually writing timers, services, running commands to
manage and create users and groups, etc. NixOS integrates all of that
into a declarative system, and this project integrates NixOS'
declarative system into a GUI.

\[bold\]Functionality

\[quoted\]Nix-Gui is a tool which loads data including option paths,
valid option types, default values, configured values, descriptions,
etc. The option hierarchy is made explorable and the value of individual
options are editable. Changes are committed by writing to modules within
the configuration path.

This data is retrieved from `<nixos/nixpkgs>`{.verbatim} and from the
configuration path via `NIX_PATH`{.verbatim}
`nixos-configuration`{.verbatim}.

Features:

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

\[bold\]Shortcomings

\[quoted\]Currently there are a few major limitations to Nix-Gui,
including

-   Nix-Gui requires that `configuration.nix`{.verbatim} be a function
    module. It cannot handle set modules.
    (<https://github.com/nix-gui/nix-gui/issues/54>)
-   The interface for `ListOf`{.verbatim} and `AttrsOf`{.verbatim} is
    incomplete.
-   Nix-Gui has yet to be thoroughly vetted, therefore the configuration
    path is copied to `~./config/nixgui/configurations/`{.verbatim}, in
    which all changes made by Nix-Gui are saved.
-   Not all data structures used in this application are optimal,
    resulting in some configuration paths taking longer than I\'d like
    to load (<https://github.com/nix-gui/nix-gui/issues/128>).
-   Some option types aren\'t handled yet (e.g. `float`{.verbatim},
    `package`{.verbatim}, `lambda`{.verbatim}, and specific types like
    `ncdns.conf configuration type`{.verbatim},
    `systemd option`{.verbatim}). These options can only be edited as a
    nix expression, as they do not have a matching widget.
-   The UX hasn\'t yet received any comments from the community .

\[bold\]Running

Quoted from usage.org\[link to
<https://github.com/nix-gui/nix-gui/blob/master/docs/usage.org>\]

\[quote of Running section\]

\[bold\]Roadmap

Short term goals (v0.2)

-   Fix the problems in the \"Shortcomings\" section.
-   Solicit UX feedback

Medium term goals (v1.0)

-   Guided configuration
    (<https://github.com/nix-gui/nix-gui/issues/77>), allow developers
    to define a \"collection\" of options related to completing a task
    (e.g. select a window manager, display manager, desktop environment,
    settings such as dpi, etc)
-   Recommended options <https://github.com/nix-gui/nix-gui/issues/21>

Long Term Goals (v2.0+)

-   In addition to the system Nix-Gui is running on, Nix-Gui should also
    be able to edit, build, and deploy for ISOs, machines via NixOps,
    and flakes.
-   Integrate home-manager
    (<https://github.com/nix-gui/nix-gui/issues/44>)
-   Trace side-effects of options
    (<https://github.com/nix-gui/nix-gui/issues/58>)
-   Modularize Nix-Gui so its various tools can be utilized by other
    programs.

\[bold\]Please Help with Testing UX Feedback

Run Nix-Gui and create issues for bugs you encounter
here\[<https://github.com/nix-gui/nix-gui/issues>\].

Please fill out the UX
Survey\[<https://github.com/nix-gui/nix-gui/issues/129>\]
