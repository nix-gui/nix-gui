from PyQt5 import QtGui

import pkgutil


def get_pixmap(filename):
    pmap = QtGui.QPixmap()
    pmap.loadFromData(pkgutil.get_data('nixui', f'icons/{filename}'))
    return pmap


def get_icon(filename):
    return QtGui.QIcon(
        get_pixmap(filename)
    )
