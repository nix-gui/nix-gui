import sys

from PyQt5 import QtWidgets, QtCore

from nixui import widgets, state_model, icon, diff_widget


class NixGuiMainWindow(QtWidgets.QMainWindow):
    def __init__(self, statemodel, parent=None):
        super().__init__(parent)

        self.statemodel = statemodel

        self.setWindowTitle("Nix UI")
        self.setCentralWidget(widgets.GenericOptionSetDisplay(statemodel=statemodel))

        self.actions = {}

        self._create_actions()
        self._create_tool_bars()

        status_bar = NixuiStatusBar()
        self.setStatusBar(status_bar)
        self.statemodel.slotmapper.add_slot('update_recorded', status_bar.display_value_change)
        self.statemodel.slotmapper.add_slot('undo_performed', status_bar.display_undo_performed)

    def _create_actions(self):
        self.actions['undo'] = QtWidgets.QAction(icon.get_icon('undo.png'), "&Undo", self)
        self.actions['undo'].triggered.connect(self.statemodel.slotmapper('undo'))

        self.actions['search'] = QtWidgets.QAction(icon.get_icon('search.png'), "&Search", self)

        self.actions['view_diff'] = QtWidgets.QAction(icon.get_icon('diff.png'), "&View Diff", self)
        self.actions['view_diff'].triggered.connect(lambda: diff_widget.DiffDialog(self.statemodel).exec())

        self.actions['save'] = QtWidgets.QAction(icon.get_icon('save.png'), "&Save", self)

        self.actions['build'] = QtWidgets.QAction(icon.get_icon('build.png'), "&Build", self)
        self.actions['preferences'] = QtWidgets.QAction(icon.get_icon('preferences.png'), "&Preferences", self)

        # TODO: enable the below
        self.actions['search'].setEnabled(False)
        self.actions['build'].setEnabled(False)
        self.actions['preferences'].setEnabled(False)

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

    def display_value_change(self, option, old_value, new_value):
        self.showMessage(f'UPDATE {option}: changed from `{old_value}` to `{new_value}`')

    def display_undo_performed(self, option, reverted_to, reverted_from):
        self.showMessage(f'UNDO {option}: reverted from `{reverted_from}` to `{reverted_to}`')


def main():
    statemodel = state_model.StateModel()

    app = QtWidgets.QApplication(sys.argv)
    nix_gui = NixGuiMainWindow(statemodel)
    nix_gui.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
