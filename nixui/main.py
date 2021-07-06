import sys

from PyQt5 import QtWidgets

from nixui.graphics import main_window
from nixui import state_model


def main():
    statemodel = state_model.StateModel()

    app = QtWidgets.QApplication(sys.argv)
    nix_gui = main_window.NixGuiMainWindow(statemodel)
    nix_gui.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
