import re

from PyQt5 import QtWidgets, QtGui, QtCore

from nixui import api, richtext, option_widgets, generic_widgets, icon


class GenericOptionSetDisplay(QtWidgets.QWidget):
    def __init__(self, statemodel, option=None, is_base_viewer=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        option = api.get_next_branching_option(option)
        self.option = option

        lay = QtWidgets.QHBoxLayout()

        # add appropriate widget to be displayed
        option_type = api.get_option_type(option)
        if option_type == 'PARENT':
            # if the option set contains fewer than 20 options, render a form for option setting
            if api.get_option_count(option) == 0:
                # if the option set contains fewer than 20 child options, render a form for option setting
                view = QtWidgets.QLabel(option + str(api.get_option_count(option)))
            elif api.get_option_count(option) < 20:
                if is_base_viewer:
                    view = OptionGroupBox(statemodel, option)
                else:
                    view = OptionGroupBox(statemodel, option, is_base_viewer=True)
            else:
                child_options = api.get_child_options(option)
                if len(child_options) < 10 and all([api.get_option_count(opt) < 20 for opt in child_options]):
                    # if there are fewer than 10 child options and each child  contains fewer than 20 options show a tab view
                    view = OptionTabs(statemodel, option)
                else:
                    view = OptionChildViewer(statemodel, option)
        elif option_type.startswith('attribute set of '):
            view = AttributeSetOf(statemodel, option)
        elif option_type.startswith('list of '):
            view = ListOf(statemodel, option)
        else:
            view = option_widgets.GenericOptionDisplay(statemodel, option)

        lay.setAlignment(QtCore.Qt.AlignTop)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)

        lay.addWidget(view)
        self.setLayout(lay)


class OptionListItem(QtWidgets.QListWidgetItem):
    def __init__(self, option_name, icon_path=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.option_name = option_name

        self.set_text()
        if icon_path:
            self.setIcon(QtGui.QIcon(icon_path))

    def set_text(self):
        child_count = api.get_option_count(self.option_name)
        self.setText(richtext.get_option_html(self.option_name, child_count))


class OptionChildViewer(generic_widgets.ScrollListStackSelector):
    # TODO: filter
    # TODO: proper sizing
    # TODO: set option selection color to light green
    # TODO: don't automatically select first row

    ItemCls = OptionListItem
    ListCls = QtWidgets.QListWidget

    def __init__(self, statemodel, option=None, *args, **kwargs):
        self.option = option
        self.statemodel = statemodel

        super().__init__(*args, **kwargs)

        self.option_str = option

    def change_item(self):
        new_option = self.item_list.currentItem().option_name
        if self.current_item != new_option:
            self.current_item = new_option
            self.change_option_view(new_option)

    def insert_items(self):
        for text in api.get_child_options(self.option):
            icon_path = None
            it = self.ItemCls(text, icon_path)
            self.item_list.addItem(it)

    def change_option_view(self, full_option_name):
        view = GenericOptionSetDisplay(statemodel=self.statemodel, option=full_option_name)

        old_widget = self.current_widget
        self.stack.addWidget(view)
        self.stack.setCurrentWidget(view)
        self.stack.removeWidget(old_widget)
        self.current_widget = view


class OptionTabs(QtWidgets.QTabWidget):
    def __init__(self, statemodel, option, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.option_str = option

        for child_option in api.get_child_options(option):
            self.addTab(GenericOptionSetDisplay(statemodel, child_option), child_option)


class OptionGroupBox(QtWidgets.QWidget):
    def __init__(self, statemodel, option=None, is_base_viewer=False, *args, **kwargs):
        super().__init__(*args, **kwargs)

        group_box = QtWidgets.QGroupBox()
        group_box.setTitle(option)

        vbox = QtWidgets.QVBoxLayout()

        for child_option in api.get_child_options(option):
            vbox.addWidget(GenericOptionSetDisplay(statemodel, child_option, is_base_viewer=False))
            vbox.addWidget(generic_widgets.SeparatorLine())

        group_box.setLayout(vbox)

        lay = QtWidgets.QHBoxLayout()
        if is_base_viewer:
            scroll_area = QtWidgets.QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            lay.addWidget(scroll_area)
            scroll_area.setWidget(group_box)
        else:
            lay.addWidget(group_box)

        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        self.setLayout(lay)

        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)


#############################
# editable navigation widgets
#############################
class EditableListItem(QtWidgets.QListWidgetItem):
    def __init__(self, option_name, icon_path=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.option_name = option_name
        self.setFlags(self.flags() | QtCore.Qt.ItemIsEditable)
        self.set_text()

    def set_text(self):
        self.setText(self.option_name.split('.')[-1])

    def setData(self, index, value):
        # is valid option name?
        if re.match(r'^[a-zA-Z\_][a-zA-Z0-9\_\'\-]*$', value):
            super().setData(index, value)


class AttributeSetOf(generic_widgets.ScrollListStackSelector):
    ItemCls = EditableListItem

    def __init__(self, statemodel, option, *args, **kwargs):
        self.option = option
        self.statemodel = statemodel
        self.layout = QtWidgets.QVBoxLayout()

        super().__init__(*args, **kwargs)

        self.item_list.itemDoubleClicked.connect(self.item_list.editItem)

        self.add_btn = QtWidgets.QPushButton("", self)
        self.add_btn.setIcon(icon.get_icon('plus.png'))
        self.add_btn.clicked.connect(self.add_clicked)

        self.remove_btn = QtWidgets.QPushButton("", self)
        self.remove_btn.setIcon(icon.get_icon('trash.png'))
        self.remove_btn.clicked.connect(self.remove_clicked)

        btn_hbox = QtWidgets.QHBoxLayout()
        btn_hbox.addWidget(self.add_btn)
        btn_hbox.addWidget(self.remove_btn)

        self.nav_layout.insertLayout(0, btn_hbox)

    def add_clicked(self):
        it = self.ItemCls(self.option)
        self.item_list.addItem(it)
        self.item_list.editItem(it)

    def remove_clicked(self):
        self.item_list.takeItem(self.item_list.currentItem())

    def change_item(self):
        item = self.item_list.currentItem()
        new_option = f'{item.option_name}.{item.text()}'
        if self.current_item != new_option:
            self.current_item = new_option
            self.change_option_view(new_option)

    def insert_items(self):
        pass
        # TODO: get from parser
        #for text in api.get_child_options(self.option):
        #    icon_path = None
        #    it = self.ItemCls(text, icon_path)
        #    self.item_list.addItem(it)

    def change_option_view(self, full_option_name):
        view = GenericOptionSetDisplay(statemodel=self.statemodel, option=full_option_name)

        old_widget = self.current_widget
        self.stack.addWidget(view)
        self.stack.setCurrentWidget(view)
        self.stack.removeWidget(old_widget)
        self.current_widget = view


class ListOf(generic_widgets.ScrollListStackSelector):
    ItemCls = EditableListItem

    def __init__(self, statemodel, option, *args, **kwargs):
        self.option = option
        self.statemodel = statemodel
        self.layout = QtWidgets.QVBoxLayout()

        super().__init__(*args, **kwargs)

        self.item_list.itemDoubleClicked.connect(self.item_list.editItem)

        self.add_btn = QtWidgets.QPushButton("", self)
        self.add_btn.setIcon(icon.get_icon('plus.png'))
        self.add_btn.clicked.connect(self.add_clicked)

        self.remove_btn = QtWidgets.QPushButton("", self)
        self.remove_btn.setIcon(icon.get_icon('trash.png'))
        self.remove_btn.clicked.connect(self.remove_clicked)

        btn_hbox = QtWidgets.QHBoxLayout()
        btn_hbox.addWidget(self.add_btn)
        btn_hbox.addWidget(self.remove_btn)

        self.nav_layout.insertLayout(0, btn_hbox)

    def add_clicked(self):
        it = self.ItemCls(self.option)
        self.item_list.addItem(it)
        self.item_list.editItem(it)

    def remove_clicked(self):
        self.item_list.takeItem(self.item_list.currentItem())

    def change_item(self):
        item = self.item_list.currentItem()
        new_option = f'{item.option_name}.{item.text()}'
        if self.current_item != new_option:
            self.current_item = new_option
            self.change_option_view(new_option)

    def insert_items(self):
        pass
        # TODO: get from parser
        #for text in api.get_child_options(self.option):
        #    icon_path = None
        #    it = self.ItemCls(text, icon_path)
        #    self.item_list.addItem(it)

    def change_option_view(self, full_option_name):
        view = GenericOptionSetDisplay(statemodel=self.statemodel, option=full_option_name)

        old_widget = self.current_widget
        self.stack.addWidget(view)
        self.stack.setCurrentWidget(view)
        self.stack.removeWidget(old_widget)
        self.current_widget = view
