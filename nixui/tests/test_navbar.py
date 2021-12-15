from nixui.graphics import navbar
from nixui.graphics.navbar import NavBar

import pytest

def test_navbar_up_button(qapp, mocker):
    def set_lookup_key(key):
        pass
    navbar = NavBar.as_option_tree('hardware', set_lookup_key)
    mocker.patch(navbar, 'set_lookup_key')
    set_lookup_key.assert_called_once()