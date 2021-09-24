from nixui.options import types


def test_integration_load_specific_options(nix_gui_main_window):
    nix_type_str = '16 bit unsigned integer; between 0 and 65535 (both inclusive) or one of "auto" or submodule or list of 16 bit unsigned integer; between 0 and 65535 (both inclusive) or one of "auto" or submodules'
    option_type = types.from_nix_type_str(nix_type_str)
    expected = types.EitherType(
        subtypes=[
            types.IntType(minimum=0, maximum=65535),
            types.OneOfType(choices=['auto']),
            types.SubmoduleType(),
            types.ListOfType(
                subtype=types.EitherType(
                    subtypes=[
                        types.IntType(minimum=0, maximum=65535),
                        types.OneOfType(choices=['auto']),
                        types.SubmoduleType()
                    ]),
                )
        ])
    assert option_type == expected
