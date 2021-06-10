import sys

from PyQt5 import QtWidgets

from nixui import widgets


def main():
    app = QtWidgets.QApplication(sys.argv)
    nix_gui = widgets.OptionChildViewer()
    nix_gui.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
