Nix-Gui has two components: the backend and the frontend.

The backend (`nixui/options`{.verbatim}) reads information from two
sources:

-   NixOS (`<nixpkgs>`{.verbatim} and `<nixos>`{.verbatim})
-   and the configuration path being edited.

It then converts the read information to data-structures useful for
navigation, search, and editing. The backend maintains in-memory state
for all changes and commits those changes to disk by writing to the
configuration path.

The frontend (`nixui/graphics`{.verbatim}) constructs various widgets
comprising Nix-Gui and loads them with data from the backend. The
frontend doesn\'t manage any edit state. All \"edit\" actions performed
in the GUI send a request-for-update to the backend.

# Backend

The backend handles three major tasks: configuration retrieval to
initialize data-structures, in-memory configuration mutation, and
configuration committing. It provides APIs for frontend interaction, but
doesn\'t concern itself with how the frontend renders any of its data,
similar to most websites wherein the webpage defines the Javascript
determining how the backend will be queried, and the HTML / CSS
determining how it will be rendered to the user.

## Loading the Option Tree Data-Structure

Nix-Gui reads information from the configuration path and
`<nixos>`{.verbatim} in order to construct a data-structure
(`nixui.options.option_tree.OptionTree`{.verbatim}) mapping options and
attributes to metadata
(`nixui.options.option_tree.OptionData`{.verbatim}) including the
attributes type and definition:

-   `_type`{.verbatim}: A static python-object representation of the
    option type (`NixType`{.verbatim}). Informs the frontend of how
    `FieldWidget`{.verbatim} should be generated and input checking
    should be performed.
-   `system_default_definition`{.verbatim}: Provided by
    `<nixpkgs>`{.verbatim}, the default value if nothing is set in the
    configuration path.
-   `configured_definition`{.verbatim}: Provided by the configuration
    path, overrides `system_default_definition`{.verbatim}.
-   `in_memory_definition`{.verbatim}: Undefined when the data-structure
    is loaded, can be mutated by the user and later committed to disk.

`nixui/nix/lib.nix`{.verbatim} (invoked by
`nixui.options.nix_eval`{.verbatim}) contains the function
`get_all_nixos_options()`{.verbatim} which is used to retrieve
`OptionData`{.verbatim} including `system_default_definition`{.verbatim}
and `_type`{.verbatim} for all options from `<nixos>`{.verbatim}.

`nixui/options/parser.py`{.verbatim} contains the function
`get_all_option_values(module_path)`{.verbatim} which

-   retrieves all
    `attributePath = string representation of nix expression;`{.verbatim}
    pairs in the file by parsing the
    `nixui.options.syntax_tree.SyntaxTree`{.verbatim} constructed using
    `nix_dump_syntax_tree_json`{.verbatim} (a wrapper for
    [rnix-parser](https://github.com/nix-community/rnix-parser/))
-   resolves the path of all `imports`{.verbatim} and recurses

The result of `get_all_option_values(module_path)`{.verbatim} is used to
set `OptionData.configured_definition`{.verbatim} where applicable.

### Caveat

Attributes in the `OptionTree`{.verbatim} can either be
**schema-defined** or **user-defined**.

1.  Schema-Defined Attribute

    These attributes are defined in the NixOS config schema, so we call
    them \"schema-defined\" attributes. In the `<nixos>`{.verbatim}
    source code, schema-defined attributes are specified by
    `mkOption`{.verbatim}, for example:

    ``` nix
    hardware.bluetooth.powerOnBoot = mkOption {
      type = types.bool;
      default = true;
      description = "Whether to power up the default Bluetooth controller on boot.";
    };
    ```

2.  User-Defined Attribute

    For `types.attrsOf`{.verbatim} options, users can specify the name
    of the attribute being defined, such as the names of users, the
    paths to files, and systemd service names. For example in
    `<nixos>`{.verbatim} source code, the schema-defined attribute
    `environment.etc`{.verbatim} provides the ability to set the
    User-Defined Attribute `environment.etc."resolv.conf"`{.verbatim} in
    `configuration.nix`{.verbatim}.

    `nixos/modules/system/etc/etc.nix`{.verbatim}:

    ``` nix
    environment.etc = mkOption {
      default = {};
      type = with types; attrsOf (submodule (
        { name, config, options, ... }:
        { options = {
            text = mkOption {
              default = null;
              type = types.nullOr types.lines;
            };
            ...
    ```

    `configuration.nix`{.verbatim}:

    ``` nix
    environment.etc."resolv.conf".text = "text here";
    ```

    1.  User-Defined List Elements

        `types.listOf`{.verbatim} options are also part of the
        `OptionTree`{.verbatim} despite not having a proper attribute
        path, e.g. a list of allowed TCP ports in the firewall will have
        the element

        ``` nix
        networking.firewall.allowedTCPPorts[0]
        ```

        This is **not** the same as

        ``` nix
        networking.firewall.allowedTCPPorts[0] = <expression>;  # illegal syntax in nix
        ```

        rather, it is equivalent to

        ``` nix
        networking.firewall.allowedTCPPorts = [<expression> ...];
        ```

### `OptionDefinition`{.verbatim}

Nix expression strings are immediately converted to
`nixui.options.option_definition.OptionDefinition`{.verbatim} Python
objects. The `OptionDefinition`{.verbatim} class provides methods to get
the python representation of an expression string. E.g. an attribute set
is converted to a dict, `"true"`{.verbatim} is converted to
`True`{.verbatim}, `"5.424"`{.verbatim} is converted to
`float(5.424)`{.verbatim}).

`OptionDefinition`{.verbatim}\'s also have the `_type`{.verbatim}
property, which returns the `NixType`{.verbatim} the current definition
is compatible with.

Additionally `OptionDefinition`{.verbatim}\'s can be used to convert
Python objects to nix expressions, which is useful for the \"Commit
Changes to Disk\" section below.

## State Management

Once constructed, the backend can perform four mutation operations:

-   replacing an old `in_memory_definition`{.verbatim}
    (`OptionDefinition`{.verbatim}) with a new one
-   adding a new attribute with a new `OptionDefinition`{.verbatim}
-   renaming an attribute
-   removing an attribute

`OptionTree.in_memory_diff`{.verbatim} contains a cache of all state
changes represented simply as a mapping between attributes and their new
`OptionDefinition`{.verbatim} (or `None`{.verbatim} if deleted).

All updates to the `OptionTree`{.verbatim} coming from the frontend pass
through `nixui.state_model.StateModel`{.verbatim}, which is a layer on
top of the `OptionTree`{.verbatim} with `Update`{.verbatim}\'s
integrated. Each mutating method results in an `Update`{.verbatim} (an
object containing information necessary to revert a change) being
appended to `StateModel.update_history`{.verbatim}.

The `StateModel`{.verbatim}\'s mutating methods include

-   `record_update`{.verbatim}: Update the
    `in_memory_definition`{.verbatim} of an attribute in the
    `OptionTree`{.verbatim}
-   `rename_option`{.verbatim}: Generally used to rename a submodule,
    e.g. `filesystems."/".foo`{.verbatim} -\>
    `"filesystems."/boot".foo`{.verbatim}
-   `add_new_option`{.verbatim}: Generally used to add an attribute or
    element to a `submodule`{.verbatim} or `list of`{.verbatim}.
-   `undo`{.verbatim}: Revert the latest `Update`{.verbatim} in
    `update_history`{.verbatim}

## Commit Changes to Disk

The `StateModel`{.verbatim} also provides the method
`persist_changes`{.verbatim}, a pass-through function which

-   Calls `OptionTree.get_changes()`{.verbatim}, which retrieves a
    mapping of attributes to **new** definitions for which the
    `in_memory_diff`{.verbatim} and `configured_definition`{.verbatim}
    differ.
-   calls `parser.calculate_changed_module`{.verbatim}, which extracts
    the `expression_string`{.verbatim} from each changed
    `OptionDefinition`{.verbatim} and calls one of three
    `SyntaxTree`{.verbatim}-modifying functions
    (`parser.add_definition()`{.verbatim},
    `parser.apply_replace_definition()`{.verbatim}, or
    `parser.apply_remove_definition()`{.verbatim} if `None`{.verbatim}).
    Each of these three functions call `add_comment`{.verbatim} with
    distinct parameters to note changes by Nix-Gui. Each of these three
    functions apply modifications to the syntax tree using methods
    provided by `SyntaxTree`{.verbatim}.

We are left with a new module string which will be written to
`module_path`{.verbatim}.

# Frontend

The frontend renders a graphical tool for changing configurations. A
primer on frontend functionality can be found in
[Usage#Interface](../usage.org#Interface).

The Nav Interface
(`nixui.graphics.nav_interface.OptionNavigationInterface`{.verbatim}) is
the main widget. It contains a layout with place-holders for three
widgets:

-   Navbar: View and update the URI.
-   Navlist: A list of attribute paths which, if clicked, updates the
    URI.
-   Options Editor: A container for a list of `FieldWidgets`{.verbatim}
    which contains option/attribute metadata and editing widgets.

## URI Resolution

Each time the URI changes, the Nav Interface creates a new instance of
each widget, replacing the old instance.

When loading a new URI,

-   A Navbar is instantiated which displays the new URIs
-   A Navlist is instantiated which displays the children of the
    attribute path, or search results. Selects the navlist item if the
    URI instructs to.
-   An Options Editor is instantiated which either is blank or shows a
    list of Option Displays an item in the navlist is selected.

### URI Format

There are currently two types of URIs,
`config:option.path.here`{.verbatim} and
`search:search text here`{.verbatim}.

## Navbar

The Navbar displays the URI and has four widgets, each of which results
in a callback telling the Nav Interface to change the URI:

-   Up Arrow: Change the URI from `config:foo.bar.baz`{.verbatim} to
    `config:foo.bar`{.verbatim}. (disabled for
    `search:anything`{.verbatim} and top level `config:`{.verbatim})
-   Back Arrow: Change the URI to the previous URI.
-   URI Box: Shows a pretty format of the URI, allow for direct editing
    of the URI when clicked.
-   Search Box: Change URI to `search:<entered text>`{.verbatim}.

## Navlist

The Navlist displays navigable options based on the URI. If the URI is
`config:parent.option.path`{.verbatim}, the navlist will display each
option which is a member of the set `parent.option.path`{.verbatim}. If
the URI is `search:<search string>`{.verbatim}, the navlist will display
each option matching the search.

If a Navlist item is clicked, the Nav Interface will load the clicked
items URI.

There are a variety of Navlist types defined in
`nixui.graphics.navlist`{.verbatim}:

-   `StaticAttrsOf`{.verbatim}: immutable listing of attributes of the
    URIs config path.
-   `DynamicAttrsOf`{.verbatim}: mutable list of attributes. Useful for
    `attribute set of <t>`{.verbatim} type attributes.
-   `DynamicListOf`{.verbatim}: mutable list elements, shown for a
    `list of <t>`{.verbatim} type attributes.
-   `SearchResultListDisplay`{.verbatim}: immutable list of search
    results including details about why it matched the search. Searches
    are matched based on `Attribute Path`{.verbatim}, `Type`{.verbatim},
    and `Description`{.verbatim}.

## Options Editor

The Options Editor is comprised of an Option Display Group
(`nixui.graphics.option_display_group.OptionDisplayGroupBox`{.verbatim}),
a `QGroupBox`{.verbatim} containing one or many Option Displays
(`nixui.graphics.option_display.GenericOptionDisplay`{.verbatim}).

An Option Display is a tool for editing the value of a single option or
attribute. The current value and option/attribute type impact how it is
rendered.

A Field Widget (`nixui.graphics.field_widgets`{.verbatim}) is the
component of an Option Display which allows the user to edit the value
of an option/attribute.

There are a variety of Field Widgets, and types of functionality for
Field Widgets:

-   Standard Field Widget: allows changes to
    `OptionDefinition.obj`{.verbatim} which will be converted to a nix
    expression
-   Expression Field Widget: allows changes to the nix expression itself
    (`OptionDefinition.expression_string`{.verbatim})
-   Reference Field Widget: (NOT IMPLEMENTED) allows users to refer to a
    package, option, or other variable in scope. This is a more
    constrained form of the Expression Field Widget and allows users to
    reference variables more easily.
-   Redirect Field Widget: For `ListOf`{.verbatim} and
    `AttrsOf`{.verbatim}, changes the URI so the navlist is the editor
    for the elements / set members for the list / set.
