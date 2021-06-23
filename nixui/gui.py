import sys

from PyQt5 import QtWidgets, QtGui, QtCore

from nixui import widgets, slot_mapper


class Window(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        slotmapper = slot_mapper.SlotMapper()

        self.setWindowTitle("Nix UI")
        self.setCentralWidget(widgets.GenericOptionSetDisplay(slotmapper=slotmapper))

        self.actions = {}

        self._create_actions()
        self._create_tool_bars()

        status_bar = NixuiStatusBar()
        self.setStatusBar(status_bar)
        slotmapper.add_slot('value_changed', status_bar.display_value_change)

    def _create_actions(self):
        self.actions['undo'] = QtWidgets.QAction(QtGui.QIcon('nixui/icons/undo.png'), "&Undo", self)
        self.actions['search'] = QtWidgets.QAction(QtGui.QIcon('nixui/icons/search.png'), "&Search", self)
        self.actions['view_diff'] = QtWidgets.QAction(QtGui.QIcon('nixui/icons/diff.png'), "&View Diff", self)
        self.actions['save'] = QtWidgets.QAction(QtGui.QIcon('nixui/icons/save.png'), "&Save", self)
        self.actions['build'] = QtWidgets.QAction(QtGui.QIcon('nixui/icons/build.png'), "&Build", self)
        self.actions['preferences'] = QtWidgets.QAction(QtGui.QIcon('nixui/icons/preferences.png'), "&Preferences", self)

    def _create_tool_bars(self):
        apply_bar = self.addToolBar("Apply")
        apply_bar.addAction(self.actions['save'])
        apply_bar.addAction(self.actions['build'])
        apply_bar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)

        edit_bar = self.addToolBar("Edit")
        edit_bar.addAction(self.actions['undo'])
        edit_bar.addAction(self.actions['search'])
        edit_bar.addAction(self.actions['view_diff'])
        edit_bar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)

        preferences_bar = self.addToolBar("Preferences")
        preferences_bar.addAction(self.actions['preferences'])
        preferences_bar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)


class NixuiStatusBar(QtWidgets.QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)

    def display_value_change(self, option, new_value):
        self.showMessage(f'{option}: set to `{new_value}`')


def main():
    app = QtWidgets.QApplication(sys.argv)
    nix_gui = Window()
    nix_gui.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
