from PyQt5 import QtWidgets, QtGui

import api, richtext, option_widgets


class GenericOptionSetDisplay(QtWidgets.QWidget):
    def __init__(self, option=None, is_base_viewer=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        option = api.get_next_branching_option(option)
        self.option = option

        lay = QtWidgets.QHBoxLayout()

        # add appropriate widget to be displayed
        option_type = api.get_type(option)
        if option_type == 'PARENT':
            # if the option set contains fewer than 20 options, render a form for option setting
            if api.get_option_count(option) == 0:
                # if the option set contains fewer than 20 child options, render a form for option setting
                view = QtWidgets.QLabel(option + str(api.get_option_count(option)))
            elif api.get_option_count(option) < 20:
                if is_base_viewer != False:
                    view = OptionGroupBox(option, is_base_viewer=True)
                else:
                    view = OptionGroupBox(option)
            else:
                child_options = api.get_child_options(option)
                if len(child_options) < 10 and all([api.get_option_count(opt) < 20 for opt in child_options]):
                    # if there are fewer than 10 child options and each child  contains fewer than 20 options show a tab view
                    view = OptionTabs(option)
                else:
                    view = OptionChildViewer(option)
        else:
            view = option_widgets.GenericOptionDisplay(option)

        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)

        lay.addWidget(view)
        self.setLayout(lay)


class OptionListItem(QtWidgets.QListWidgetItem):
    def __init__(self, option_name, icon_path, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.option_name = option_name

        child_count = api.get_option_count(option_name)
        self.setText(richtext.get_option_html(option_name, child_count))
        if icon_path:
            self.setIcon(QtGui.QIcon(icon_path))


class OptionChildViewer(QtWidgets.QWidget):
    # TODO: filter
    # TODO: proper sizing
    # TODO: set option selection color to light green
    # TODO: don't automatically select first row
    def __init__(self, option=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.option_str = option

        self.child_options = QtWidgets.QLabel()
        self.child_options_container = QtWidgets.QStackedWidget()
        self.child_options_container.addWidget(self.child_options)

        self.option_list = QtWidgets.QListWidget()
        self.insert_child_options(option)
        self.option_list.currentItemChanged.connect(self.change_base_option_set)
        self.option_list.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.option_list.setItemDelegate(richtext.HTMLDelegate())
        self.option_list.currentItemChanged.connect(self.change_base_option_set)

        self.current_option = None

        self.hbox = QtWidgets.QHBoxLayout()
        self.hbox.setSpacing(0)
        self.hbox.setContentsMargins(0, 0, 0, 0)
        self.hbox.addWidget(self.option_list)
        self.hbox.addWidget(self.child_options_container)

        self.setLayout(self.hbox)

    def change_base_option_set(self):
        new_option = self.option_list.currentItem().option_name
        if self.current_option != new_option:
            self.current_option = new_option
            self.change_option_view(self.option_list.currentItem().option_name)

    def insert_child_options(self, option):
        for text in api.get_child_options(option):
            icon_path = None  # "/home/andrew/img/tim/long_leg.png"
            it = OptionListItem(text, icon_path)
            self.option_list.addItem(it)

    def change_option_view(self, full_option_name):
        view = GenericOptionSetDisplay(full_option_name)

        old_options = self.child_options
        self.child_options_container.addWidget(view)
        self.child_options_container.setCurrentWidget(view)
        self.child_options_container.removeWidget(old_options)
        self.child_options = view


class OptionTabs(QtWidgets.QTabWidget):
    def __init__(self, option, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.option_str = option

        for child_option in api.get_child_options(option):
            self.addTab(GenericOptionSetDisplay(child_option), child_option)


class OptionGroupBox(QtWidgets.QWidget):
    def __init__(self, option=None, is_base_viewer=False, *args, **kwargs):
        super().__init__(*args, **kwargs)

        group_box = QtWidgets.QGroupBox()
        group_box.setTitle(option)

        vbox = QtWidgets.QVBoxLayout()

        for child_option in api.get_child_options(option):
            vbox.addWidget(GenericOptionSetDisplay(child_option, is_base_viewer=False))

        group_box.setLayout(vbox)

        lay = QtWidgets.QHBoxLayout()
        if is_base_viewer:
            scroll_area = QtWidgets.QScrollArea()
            lay.addWidget(scroll_area)
            scroll_area.setWidget(group_box)
        else:
            lay.addWidget(group_box)

        self.setLayout(lay)
