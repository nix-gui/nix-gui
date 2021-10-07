from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import Qt, QRect


def get_default_font():
    return QtWidgets.QApplication.instance().font()


# modified from https://github.com/roman-popenov/demo-code/blob/23806afac12db2ddd85a1e0b0e1ff4860da08216/ui/switch.py
class ToggleSwitch(QtWidgets.QWidget):
    # TODO: reimplement this entirely so its comprised of a rectangle and square
    stateChanged = QtCore.pyqtSignal(bool)

    def __init__(self, on_text="Yes", off_text="No", starting_value=False, font=None):
        super().__init__()

        font = font or get_default_font()
        font_metrics = QtGui.QFontMetrics(font)

        font_height = font_metrics.height()
        off_text_width = font_metrics.width(off_text)
        font_width = max(
            font_metrics.width(on_text),
            off_text_width
        )

        self.widget_height = font_height + 4
        self.widget_width = font_width + font_height * 2 + 4  # account for circle

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.__labeloff = QtWidgets.QLabel(self)
        self.__labeloff.setText(off_text)
        self.__labeloff.setStyleSheet("""color: rgb(255, 255, 255); font-weight: bold;""")
        self.__background = Background(self.widget_height, self)
        self.__labelon = QtWidgets.QLabel(self)
        self.__labelon.setText(on_text)
        self.__labelon.setStyleSheet("""color: rgb(255, 255, 255); font-weight: bold;""")
        self.__labelon.hide()
        self.__circle = Circle(self.widget_height - 4, self)
        self.__circlemove = None
        self.__ellipsemove = None
        self.__enabled = True
        self.__duration = 100
        self.__value = None
        self.setFixedSize(self.widget_width, self.widget_height)

        self.__background.resize(self.widget_width - 4, self.widget_height - 4)
        self.__background.move(2, 2)
        self.__circle.move(2, 2)
        self.__labelon.move(self.widget_height / 2, 2)
        self.__labeloff.move(self.widget_width - off_text_width - self.widget_height / 2, 2)

        self.setChecked(starting_value)

    def setDuration(self, time):
        self.__duration = time

    def mousePressEvent(self, event):
        self.setChecked(not self.__value, animate=True)
        self.stateChanged.emit(self.__value)

    def isChecked(self):
        return self.__value

    def setChecked(self, value, animate=False):
        if not self.__enabled or self.__value == value:
            return

        old_value = not value
        self.__value = value

        xs = 2
        y = 2
        xf = self.width() - self.widget_height + 4
        hback = self.widget_height
        isize = QtCore.QSize(hback, hback)
        bsize = QtCore.QSize(self.width() - self.widget_height / 2, hback)
        if old_value:
            xf = 2
            xs = self.width() - 22
            bsize = QtCore.QSize(hback, hback)
            isize = QtCore.QSize(self.widget_width, hback)

        if animate:
            self.__circlemove = QtCore.QPropertyAnimation(self.__circle, b"pos")
            self.__circlemove.setDuration(self.__duration)

            self.__ellipsemove = QtCore.QPropertyAnimation(self.__background, b"size")
            self.__ellipsemove.setDuration(self.__duration)

            self.__circlemove.setStartValue(QtCore.QPoint(xs, y))
            self.__circlemove.setEndValue(QtCore.QPoint(xf, y))

            self.__ellipsemove.setStartValue(isize)
            self.__ellipsemove.setEndValue(bsize)

            if self.__value:
                self.__ellipsemove.finished.connect(self.__labelon.show)
            else:
                self.__ellipsemove.finished.connect(self.__labelon.hide)

            self.__circlemove.start()
            self.__ellipsemove.start()
        else:
            self.__circle.move(QtCore.QPoint(xf, y))
            self.__background.resize(bsize)

            if self.__value:
                self.__labelon.show()
            else:
                self.__labelon.hide()



    def paintEvent(self, event):
        s = self.size()
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.setRenderHint(QtGui.QPainter.Antialiasing, True)
        pen = QtGui.QPen(QtCore.Qt.NoPen)
        qp.setPen(pen)
        qp.setBrush(QtGui.QColor(120, 120, 120))
        qp.drawRoundedRect(0, 0, s.width(), s.height(), 12, 12)
        lg = QtGui.QLinearGradient(35, 30, 35, 0)
        lg.setColorAt(0, QtGui.QColor(210, 210, 210, 255))
        lg.setColorAt(0.25, QtGui.QColor(255, 255, 255, 255))
        lg.setColorAt(0.82, QtGui.QColor(255, 255, 255, 255))
        lg.setColorAt(1, QtGui.QColor(210, 210, 210, 255))
        qp.setBrush(lg)
        qp.drawRoundedRect(1, 1, s.width() - 2, s.height() - 2, 10, 10)

        qp.setBrush(QtGui.QColor(210, 210, 210))
        qp.drawRoundedRect(2, 2, s.width() - 4, s.height() - 4, 10, 10)

        lg = QtGui.QLinearGradient(50, 30, 35, 0)
        lg.setColorAt(0, QtGui.QColor(160, 40, 40, 255))
        lg.setColorAt(0.25, QtGui.QColor(140, 40, 40, 255))
        lg.setColorAt(0.82, QtGui.QColor(120, 40, 40, 255))
        lg.setColorAt(1, QtGui.QColor(100, 40, 40, 255))
        qp.setBrush(lg)
        qp.drawRoundedRect(3, 3, s.width() - 3, s.height() - 6, 7, 7)
        qp.end()


class Circle(QtWidgets.QWidget):
    def __init__(self, diameter, parent=None):
        super(Circle, self).__init__(parent)
        self.diameter = diameter
        self.setFixedSize(diameter, diameter)

    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.setRenderHint(QtGui.QPainter.Antialiasing, True)
        qp.setPen(QtCore.Qt.NoPen)
        qp.setBrush(QtGui.QColor(120, 120, 120))
        qp.drawEllipse(0, 0, self.diameter, self.diameter)
        rg = QtGui.QRadialGradient(int(self.width() / 2), int(self.height() / 2), 12)
        rg.setColorAt(0, QtGui.QColor(255, 255, 255))
        rg.setColorAt(0.6, QtGui.QColor(255, 255, 255))
        rg.setColorAt(1, QtGui.QColor(205, 205, 205))
        qp.setBrush(QtGui.QBrush(rg))
        qp.drawEllipse(1, 1, self.diameter - 2, self.diameter - 2)

        qp.setBrush(QtGui.QColor(210, 210, 210))
        qp.drawEllipse(2, 2, self.diameter - 4, self.diameter - 4)

        lg = QtGui.QLinearGradient(3, 18, 20, 4)
        lg.setColorAt(0, QtGui.QColor(255, 255, 255, 255))
        lg.setColorAt(0.55, QtGui.QColor(230, 230, 230, 255))
        lg.setColorAt(0.72, QtGui.QColor(255, 255, 255, 255))
        lg.setColorAt(1, QtGui.QColor(255, 255, 255, 255))
        qp.setBrush(lg)
        qp.drawEllipse(3, 3, self.diameter - 6, self.diameter - 6)
        qp.end()


class Background(QtWidgets.QWidget):
    def __init__(self, height, parent=None):
        super(Background, self).__init__(parent)
        self.height = height
        self.setFixedHeight(height)

    def paintEvent(self, event):
        s = self.size()
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.setRenderHint(QtGui.QPainter.Antialiasing, True)
        pen = QtGui.QPen(QtCore.Qt.NoPen)
        qp.setPen(pen)
        qp.setBrush(QtGui.QColor(154, 205, 50))

        qp.setBrush(QtGui.QColor(154, 190, 50))
        qp.drawRoundedRect(0, 0, s.width(), s.height(), 10, 10)

        lg = QtGui.QLinearGradient(0, 25, 70, 0)
        lg.setColorAt(0, QtGui.QColor(154, 184, 50))
        lg.setColorAt(0.35, QtGui.QColor(154, 210, 50))
        lg.setColorAt(0.85, QtGui.QColor(154, 184, 50))
        qp.setBrush(lg)
        qp.drawRoundedRect(1, 1, s.width() - 2, s.height() - 2, 8, 8)
        qp.end()
