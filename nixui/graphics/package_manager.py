from PyQt5 import QtWidgets, QtCore


class Package:
    pass


class PackageManagerWidget(QtWidgets.QWidget):
    stateChanged = QtCore.pyqtSignal(str)

    def __init__(self, statemodel, only_one_package=False):
        super().__init__()
        self.statemodel = statemodel
        self.only_one_package = only_one_package
        self.init_ui()

    def init_ui(self):
        # current list of packages included
        self.included_packages_listbox = QtWidgets.QListWidget()

        # all packages filtered by search box
        self.search_box = QtWidgets.QLineEdit()
        self.all_packages_listbox = QtWidgets.QListWidget()

        # details on the selected item
        self.details_textbox = QtWidgets.QTextEdit()
        self.all_packages_listbox = QtWidgets.QListWidget()

        # setup layout
        right_vbox = QtWidgets.QVBoxLayout()
        right_vbox.addWidget(self.search_box)
        right_vbox.addWidget(self.all_packages_listbox)
        right_vbox.addWidget(self.details_textbox)

        main_hbox = QtWidgets.QHBoxLayout()
        main_hbox.addWidget(self.included_packages_listbox)
        main_hbox.addLayout(right_vbox)

        self.setLayout(main_hbox)
