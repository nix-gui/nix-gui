import re

from PyQt5 import QtWidgets, QtGui, QtCore

import api


class HTMLDelegate(QtWidgets.QStyledItemDelegate):
    def paint(self, painter, option, index):
        style = option.widget.style()
        doc = self._builddoc(option, index)
        option.text = ""
        style.drawControl(QtWidgets.QStyle.CE_ItemViewItem, option, painter)
        ctx = QtGui.QAbstractTextDocumentLayout.PaintContext()
        textRect = style.subElementRect(QtWidgets.QStyle.SE_ItemViewItemText, option)
        painter.save()
        painter.translate(textRect.topLeft())
        painter.setClipRect(textRect.translated(-textRect.topLeft()))
        doc.documentLayout().draw(painter, ctx)
        painter.restore()

    def sizeHint(self, option, index):
        doc = self._builddoc(option, index)
        return QtCore.QSize(
            doc.idealWidth() + 60,  # TODO: make width the size of the rendered html, right now its too small
            option.decorationSize.height() * 1.5  # hack
        )

    def _builddoc(self, option, index):
        option = QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(option, index)
        doc = QtGui.QTextDocument(defaultFont=option.font)
        doc.setHtml(option.text)
        return doc


def get_option_html(option_name):
    fancy_name = option_name.split('.')[-1]
    capitalized_fancy_name = re.sub(r"(\w)([A-Z])", r"\1 \2", fancy_name).title()
    child_count = api.get_option_count(option_name)
    return (f"""
    <p style="font-size:7pt">{capitalized_fancy_name}</p>
    <p style="font-style:italic; color:Gray; font-size:4pt; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px">{option_name} ({child_count})</p>
    """)
