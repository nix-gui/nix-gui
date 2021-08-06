from PyQt5 import QtWidgets, QtCore


from nixui.graphics import nav_interface, icon, diff_widget


class NixGuiMainWindow(QtWidgets.QMainWindow):
    def __init__(self, statemodel, parent=None):
        super().__init__(parent)

        self.statemodel = statemodel

        self.setWindowTitle("Nix UI")
        self.setCentralWidget(
            nav_interface.OptionNavigationInterface(statemodel=statemodel)
        )

        self.actions = {}

        self._create_actions()
        self._create_tool_bars()
        self._create_menu()

        status_bar = NixuiStatusBar(self.statemodel)
        self.setStatusBar(status_bar)

    def _create_actions(self):
        self.actions['undo'] = QtWidgets.QAction(icon.get_icon('undo.png'), "&Undo", self)
        self.actions['undo'].setShortcut(QtGui.QKeySequence("Ctrl+z"))
        self.actions['undo'].triggered.connect(self.statemodel.slotmapper('undo'))
        self.actions['undo'].setEnabled(False)
        self.statemodel.slotmapper.add_slot('no_updates_exist', lambda: self.actions['undo'].setEnabled(False))
        self.statemodel.slotmapper.add_slot('update_recorded', lambda *args, **kwargs: self.actions['undo'].setEnabled(True))

        self.actions['view_diff'] = QtWidgets.QAction(icon.get_icon('diff.png'), "&View Diff", self)
        self.actions['view_diff'].setShortcut(QtGui.QKeySequence("Ctrl+d"))
        self.actions['view_diff'].triggered.connect(lambda: diff_widget.DiffDialog(self.statemodel).exec())

        self.actions['save'] = QtWidgets.QAction(icon.get_icon('save.png'), "&Save", self)
        self.actions['save'].setShortcut(QtGui.QKeySequence("Ctrl+s"))
        self.actions['save'].triggered.connect(lambda: diff_widget.SaveDialog(self.statemodel).exec())

        self.actions['build'] = QtWidgets.QAction(icon.get_icon('build.png'), "&Build", self)
        self.actions['preferences'] = QtWidgets.QAction(icon.get_icon('preferences.png'), "&Preferences", self)

        self.actions['quit'] = QtWidgets.QAction("&Quit", self)
        self.actions['quit'].setShortcut(QtGui.QKeySequence("Ctrl+q"))
        self.actions['quit'].triggered.connect(lambda: self.close())

        # TODO: enable the below
        self.actions['build'].setEnabled(False)
        self.actions['preferences'].setEnabled(False)

    def _create_tool_bars(self):
        apply_bar = self.addToolBar("Apply")
        apply_bar.addAction(self.actions['save'])
        apply_bar.addAction(self.actions['build'])
        apply_bar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)

        edit_bar = self.addToolBar("Edit")
        edit_bar.addAction(self.actions['undo'])
        edit_bar.addAction(self.actions['view_diff'])
        edit_bar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)

        preferences_bar = self.addToolBar("Preferences")
        preferences_bar.addAction(self.actions['preferences'])
        preferences_bar.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)

    def _create_menu(self):
        file_menu = self.menuBar().addMenu("File")
        file_menu.addAction(self.actions['save'])
        file_menu.addAction(self.actions['quit'])

        edit_menu = self.menuBar().addMenu("Edit")
        edit_menu.addAction(self.actions['undo'])
        edit_menu.addAction(self.actions['view_diff'])


class NixuiStatusBar(QtWidgets.QStatusBar):
    def __init__(self, statemodel):
        super().__init__()
        statemodel.slotmapper.add_slot('update_recorded', self.display_value_change)
        statemodel.slotmapper.add_slot('undo_performed', self.display_undo_performed)
        statemodel.slotmapper.add_slot('changes_saved', self.display_changes_saved)

    def display_value_change(self, option, old_value, new_value):
        self.showMessage(f'UPDATE {option}: changed from `{old_value}` to `{new_value}`')

    def display_undo_performed(self, option, reverted_to, reverted_from):
        self.showMessage(f'UNDO {option}: reverted from `{reverted_from}` to `{reverted_to}`')

    def display_changes_saved(self, save_path):
        self.showMessage(f'SAVED changes to {save_path}')
