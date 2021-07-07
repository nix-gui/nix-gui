from PyQt5 import QtGui

import pkgutil


def get_icon(filename):
    pmap = QtGui.QPixmap()
    pmap.loadFromData(pkgutil.get_data('nixui', f'icons/{filename}'))
    return QtGui.QIcon(pmap)
