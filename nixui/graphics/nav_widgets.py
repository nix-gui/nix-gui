import re

from PyQt5 import QtWidgets, QtGui, QtCore

from nixui.options import api, attribute
from nixui.graphics import richtext, field_widgets, generic_widgets, icon


class GenericOptionSetDisplay(QtWidgets.QWidget):
    def __init__(self, statemodel, option=attribute.Attribute(), is_base_viewer=None, *args, **kwargs):
        """
        recursively load option path navigation widget, or if leaf field widget
        field widgets are determined based on the type of the option
        path navigation widgets are determined based on multiple factors
        - if there is an "attribute set of" or "list of" type within the children, use the scroll list OptionChildViewer
        - if the option itself is an "attribute set of" or "list of" type, create their respective option navigation formn
        - if there aren't very many options left to edit, put them together in an OptionGroupBox

        each path navigation widget recurses and calls GenericOptionSetDisplay
        """
        super().__init__(*args, **kwargs)

        self.statemodel = statemodel
        self.is_base_viewer = is_base_viewer

        lay = QtWidgets.QHBoxLayout()
        lay.setAlignment(QtCore.Qt.AlignTop)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.get_view(option))
        self.setLayout(lay)

    def get_view(self, option):
        option_tree = api.get_option_tree()
        child_option_count = len(option_tree.children(option))

        # we must provide option sets with a dynamic set/list of children their appropriate widget
        option_type = option_tree.get_type(option)
        if option_type.startswith('attribute set of '):
            return AttributeSetOf(self.statemodel, option)
        if option_type.startswith('list of '):
            return ListOf(self.statemodel, option)

        # "attribute set of" and "list of" attributes require the full height of the window and
        # cannot be combined with other options in an OptionGroupBox, therefore if such an
        # attribute is a descendant an OptionChildViewer must be used
        # additionally, if there are too many child options, we don't render them in a single OptionGroupBox
        descendent_types = [
            option_tree.get_type(child_attr)
            for child_attr in option_tree.children(option, recursive=True)
        ]
        descendent_requires_full_display = any([
            _type.startswith('attribute set of ') or _type.startswith('list of ')
            for _type in descendent_types
        ])
        if descendent_requires_full_display or child_option_count > 15:
            return OptionChildViewer(self.statemodel, option)

        # compress descendents
        option = option_tree.get_next_branching_option(option)
        option_type = option_tree.get_type(option)
        # render either an OptionGroupBox or OptionChildViewer based on the type for options with multiple descendents
        if option_type == 'PARENT':
            # OptionGroupBox will recursively add child OptionGroupBoxes. Only the outermost OptionGroupBox should
            # be scrollable. is_base_viewer signals to add the scrollbar
            if self.is_base_viewer:
                return OptionGroupBox(self.statemodel, option)
            else:
                return OptionGroupBox(self.statemodel, option, is_base_viewer=True)

        # the only other possibility is that the option is a leaf, meaning we add the appropriate field widget
        return field_widgets.GenericOptionDisplay(self.statemodel, option)



class ChildCountOptionListItem(generic_widgets.OptionListItem):
    def set_text(self):
        child_count = len(api.get_option_tree().children(self.option))
        self.setText(richtext.get_option_html(self.option, child_count))


class OptionChildViewer(generic_widgets.ScrollListStackSelector):
    ItemCls = ChildCountOptionListItem
    ListCls = QtWidgets.QListWidget

    def __init__(self, statemodel, option=None, *args, **kwargs):
        self.option = option
        self.statemodel = statemodel

        super().__init__(*args, **kwargs)

        self.option_str = option

    def change_selected_item(self):
        new_option = self.item_list.currentItem().option
        if self.current_item != new_option:
            self.current_item = new_option
            self.change_option_view(new_option)

    def insert_items(self):
        # TODO: filter out <name> and * for submodules
        # TODO: add priority ordering
        for text in api.get_option_tree().children(self.option):
            icon_path = None
            it = self.ItemCls(text, icon_path)
            self.item_list.addItem(it)

    def change_option_view(self, option):
        view = GenericOptionSetDisplay(statemodel=self.statemodel, option=option)

        old_widget = self.current_widget
        self.stack.addWidget(view)
        self.stack.setCurrentWidget(view)
        self.stack.removeWidget(old_widget)
        self.current_widget = view


class OptionTabs(QtWidgets.QTabWidget):
    def __init__(self, statemodel, option, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.option_str = option

        for child_option in api.get_option_tree().children(option):
            self.addTab(GenericOptionSetDisplay(statemodel, child_option), str(child_option))


class OptionGroupBox(QtWidgets.QWidget):
    def __init__(self, statemodel, option=None, is_base_viewer=False, *args, **kwargs):
        super().__init__(*args, **kwargs)

        group_box = QtWidgets.QGroupBox()
        group_box.setTitle(str(option))

        vbox = QtWidgets.QVBoxLayout()

        for child_option in api.get_option_tree().children(option):
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
    def __init__(self, option, icon_path=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.option = option
        self.previous_option = option
        self.setFlags(self.flags() | QtCore.Qt.ItemIsEditable)
        self.set_text()

    def set_text(self):
        self.setText(str(self.option.get_end()))

    def setData(self, index, value):
        # is valid option name?
        if re.match(r'^[a-zA-Z\_][a-zA-Z0-9\_\'\-]*$', value):
            self.previous_option = self.option
            self.option = attribute.Attribute.from_insertion(self.option.get_set(), value)
            super().setData(index, value)


class AttributeSetOf(generic_widgets.ScrollListStackSelector):
    ItemCls = EditableListItem

    def __init__(self, statemodel, option, *args, **kwargs):
        self.option = option
        self.statemodel = statemodel
        self.layout = QtWidgets.QVBoxLayout()

        super().__init__(*args, **kwargs)

        self.item_list.itemDoubleClicked.connect(self.item_list.editItem)
        self.item_list.itemChanged.connect(self.rename_item)
        self.item_list.model().rowsRemoved.connect(lambda: self.remove_item)

        self.add_btn = QtWidgets.QPushButton("", self)
        self.add_btn.setIcon(icon.get_icon('plus.png'))
        self.add_btn.clicked.connect(self.add_clicked)

        self.remove_btn = QtWidgets.QPushButton("", self)
        self.remove_btn.setIcon(icon.get_icon('trash.png'))
        self.remove_btn.clicked.connect(self.remove_clicked)

        btn_hbox = QtWidgets.QHBoxLayout()
        btn_hbox.addWidget(self.add_btn, 1)
        btn_hbox.addWidget(self.remove_btn, 1)

        self.nav_layout.insertLayout(1, btn_hbox)

    def remove_item(self, item):
        print('not implemented')

    def rename_item(self, item):
        self.statemodel.rename_option(item.previous_option, item.option)

    def get_title(self):
        return f'Attribute Set\n{self.option}'

    def add_clicked(self):
        item = self.ItemCls(
            attribute.Attribute.from_insertion(self.option, 'newAttribute')
        )
        self.item_list.addItem(item)
        self.statemodel.add_new_option(item.option)
        self.item_list.editItem(item)

    def remove_clicked(self):
        self.item_list.takeItem(self.item_list.currentItem())

    def change_selected_item(self):
        item = self.item_list.currentItem()
        new_option = item.option
        if self.current_item != new_option:
            self.current_item = new_option
            self.change_option_view(new_option)

    def insert_items(self):
        for option in api.get_option_tree().children(self.option):
            it = self.ItemCls(option)
            self.item_list.addItem(it)

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

        self.up_btn = QtWidgets.QPushButton("△", self)
        self.up_btn.clicked.connect(self.up_clicked)

        self.down_btn = QtWidgets.QPushButton("▽", self)
        self.down_btn.clicked.connect(self.down_clicked)

        btn_hbox = QtWidgets.QHBoxLayout()
        btn_hbox.addWidget(self.add_btn)
        btn_hbox.addWidget(self.remove_btn)

        btn_hbox.addWidget(self.up_btn)
        btn_hbox.addWidget(self.down_btn)

        self.nav_layout.insertLayout(0, btn_hbox)

    def add_clicked(self):
        it = self.ItemCls(self.option)
        self.item_list.addItem(it)
        self.item_list.editItem(it)

    def remove_clicked(self):
        self.item_list.takeItem(self.item_list.currentItem())

    def up_clicked(self):
        print('up')

    def down_clicked(self):
        print('down')

    def change_selected_item(self):
        item = self.item_list.currentItem()
        new_option = f'{item.option}.{item.text()}'
        if self.current_item != new_option:
            self.current_item = new_option
            self.change_option_view(new_option)

    def insert_items(self):
        pass
        #for text in api.get_option_tree.children(option):
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
