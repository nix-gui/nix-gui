from nixui.options import types


def test_integration_load_specific_options(nix_gui_main_window):
    nix_type_str = '16 bit unsigned integer; between 0 and 65535 (both inclusive) or one of "auto" or submodule or list of 16 bit unsigned integer; between 0 and 65535 (both inclusive) or one of "auto" or submodules'
    option_type = types.from_nix_type_str(nix_type_str)
    assert option_type == types.Either(
        subtypes=[
            types.Int(minimum=0, maximum=65535),
            types.OneOf(choices=['auto']),
            types.Submodule(),
            types.ListOf(
                subtype=types.Either(
                    subtypes=[
                        types.Int(minimum=0, maximum=65535),
                        types.OneOf(choices=['auto']),
                        types.Submodule()
                    ]),
                )
        ])
