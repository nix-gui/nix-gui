import sys

from PyQt5 import QtWidgets

import widgets


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    nix_gui = widgets.OptionChildViewer()
    nix_gui.show()
    sys.exit(app.exec_())
