from nixui.graphics.navbar import NavBar
from nixui.options.attribute import Attribute

import pytest
from PyQt5 import QtWidgets
import PyQt5

class Temp():
    def set_lookup_key(self, key):
        pass

def test_navbar_up_button(qapp, qtbot, mocker):
    temp = Temp()
    mocker.patch.object(temp, 'set_lookup_key')
    navbar = NavBar.as_option_tree(Attribute(["hardware"]), temp.set_lookup_key)
    qtbot.mouseClick(navbar.findChildren(QtWidgets.QPushButton)[1], PyQt5.QtCore.Qt.LeftButton)
    temp.set_lookup_key.assert_called_once()

def test_navbar_back_button(qapp, qtbot, mocker):
    temp = Temp()
    mocker.patch.object(temp, 'set_lookup_key')
    navbar = NavBar(temp.set_lookup_key, "", "")
    qtbot.mouseClick(navbar.findChildren(QtWidgets.QPushButton)[0], PyQt5.QtCore.Qt.LeftButton)
    temp.set_lookup_key.assert_called_once_with(None)

def test_navbar_enter_path(qapp, qtbot, mocker):
    temp = Temp()
    mocker.patch.object(temp, 'set_lookup_key')
    navbar = NavBar(temp.set_lookup_key, "", "")
    qtbot.keyClicks(navbar.findChildren(QtWidgets.QLineEdit)[0], "programs")
    qtbot.keyPress(navbar.findChildren(QtWidgets.QLineEdit)[0], PyQt5.QtCore.Qt.Key_Enter)
    temp.set_lookup_key.assert_called_once_with("programs")

def test_navbar_search(qapp, qtbot, mocker):
    temp = Temp()
    mocker.patch.object(temp, 'set_lookup_key')
    navbar = NavBar(temp.set_lookup_key, "", "")
    qtbot.keyClicks(navbar.findChildren(QtWidgets.QLineEdit)[1], "programs")
    qtbot.keyPress(navbar.findChildren(QtWidgets.QLineEdit)[1], PyQt5.QtCore.Qt.Key_Enter)
    temp.set_lookup_key.assert_called_once_with("search:programs")