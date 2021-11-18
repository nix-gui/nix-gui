import collections
import csv

from PyQt5 import QtWidgets, QtCore, QtGui

from nixui.graphics import icon, richtext, color_indicator
from nixui.options.attribute import Attribute
from nixui.options import api, option_definition, types
from nixui.utils.logger import logger


class GenericNavListDisplay:
    def __new__(cls, statemodel, set_option_path_fn, option_path, option_type=None, selected=None):
        option_type = option_type or api.get_option_tree().get_type(option_path)
        if isinstance(option_type, types.AttrsOfType):
            return DynamicAttrsOf(statemodel, option_path, set_option_path_fn, selected)
        elif isinstance(option_type, types.ListOfType):
            return DynamicListOf(statemodel, option_path, set_option_path_fn, selected)
        else:
            return StaticAttrsOf(option_path, set_option_path_fn, selected)


class OptionListItemDelegate(QtWidgets.QStyledItemDelegate):
    padding = 5

    def paint(self, painter, option, index):
        # ensure different background colors are applied for selected rows
        viewOption = QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(viewOption, index)
        QtWidgets.QStyledItemDelegate.paint(self, painter, viewOption, index)

        data = index.data(QtCore.Qt.DisplayRole)

        # draw left side icon if exists
        if data.get('icon_path'):
            icon_rect = QtCore.QRect(
                option.rect.left() + self.padding,
                option.rect.top() + self.padding,
                option.rect.height() - self.padding * 2,
                option.rect.height() - self.padding * 2,
            )
            icon_pixmap = icon.get_pixmap(data['icon_path'])
            painter.drawPixmap(icon_rect, icon_pixmap)

        if data.get('status_circle_color'):
            status_circle_rect = QtCore.QRectF(
                option.rect.right() - option.rect.height() * 0.5 - self.padding,
                option.rect.top() + option.rect.height() * 0.5 - self.padding,
                option.rect.height() * 0.25,
                option.rect.height() * 0.25,
            )
            circle_outline_width = 2
            painter.setPen(QtGui.QPen(QtCore.Qt.black, circle_outline_width, QtCore.Qt.SolidLine))
            painter.setBrush(QtGui.QBrush(data['status_circle_color'], QtCore.Qt.SolidPattern))
            painter.drawEllipse(status_circle_rect)

        # get text ready to draw
        text_left_offset = option.rect.height() + self.padding * 2 if data.get('icon_path') else self.padding * 2
        text_right_offset = option.rect.height() + self.padding * 2  # padding for space from status circle
        text_rect = QtCore.QRect(
            option.rect.left() + text_left_offset + self.padding,
            option.rect.top() + self.padding,
            option.rect.width() - text_left_offset - text_right_offset - self.padding * 2,
            option.rect.height() - self.padding * 2,
        )
        text = data['text'] + (f" ({data['child_count']})" if data.get('child_count') else "")

        # draw subtext
        if data.get('extra_text'):
            painter.save()
            extra_text_rect = QtCore.QRect(text_rect)
            extra_text_rect.setY(text_rect.y() + option.rect.height() / 3)
            text_rect.setY(text_rect.y() - option.rect.height() / 3)  # adjust the base text upwards
            extra_text_font = QtGui.QFont()
            extra_text_font.setItalic(True)
            extra_text_font.setPointSize(extra_text_font.pointSize() - 2)
            extra_text_font.setWeight(QtGui.QFont.Light)
            painter.setFont(extra_text_font)
            painter.drawText(extra_text_rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, '\t' + data['extra_text'])
            painter.restore()

        # draw text
        painter.drawText(text_rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, text)

    def sizeHint(self, option, index):
        """
        Double height of each item
        """
        size = super().sizeHint(option, index)
        data = index.data(QtCore.Qt.DisplayRole)
        if data.get('extra_text'):
            new_height = size.height() * 3
        else:
            new_height = size.height() * 2
        return QtCore.QSize(size.width(), new_height)


class OptionListItem(QtWidgets.QListWidgetItem):
    def __init__(self, option, use_full_option_path=False, use_child_count=True, extra_text=None, icon_path=None, editable=False):
        super().__init__()
        self.option_tree = api.get_option_tree()

        self.option = option
        self.previous_option = self.option  # stored to record edits

        self.use_full_option_path = use_full_option_path
        self.extra_text = extra_text
        self.icon_path = icon_path

        if use_child_count:
            num_direct_children = len(self.option_tree.children(self.option))
            num_descendants = len(self.option_tree.children(self.option, mode='leaves'))
            self.child_count = f'{num_direct_children}/{num_descendants}'
        else:
            self.child_count = None

        if editable:
            self.setFlags(self.flags() | QtCore.Qt.ItemIsEditable)

        self.setData(QtCore.Qt.DisplayRole, str(self.option))

    def setData(self, role, value_str):
        if role == QtCore.Qt.EditRole:
            self.previous_option = self.option
            self.option = Attribute.from_insertion(self.option.get_set(), value_str)

        # Delegate takes a dict, convert
        value = {
            'text': str(self.option) if self.use_full_option_path else str(self.option[-1]),
            'child_count': self.child_count,
            'extra_text': self.extra_text,
            'icon_path': self.icon_path,
            'status_circle_color': self.status_color
        }
        super().setData(role, value)

    @property
    def status_color(self):
        # get color based on whether it or a child has been edited
        color = color_indicator.get_edit_state_color_indicator(
            self.option_tree,
            self.option
        )
        return color


class OptionScrollListSelector(QtWidgets.QListWidget):
    def __init__(self, base_option_path, set_option_path_fn=None):
        super().__init__()

        # change selected callback
        self.base_option_path = base_option_path
        self.set_option_path_fn = set_option_path_fn
        self.itemClicked.connect(self.set_option_path_callback)

        # load options
        options = api.get_option_tree().children(base_option_path)
        self.option_item_map = {}
        for option in options:
            item = OptionListItem(option)
            self.addItem(item)
            self.option_item_map[option.get_end()] = item

        self._setup_scroll_list_selector_theme()  # form look and feel

    def _setup_scroll_list_selector_theme(self):
        self.setAlternatingRowColors(True)
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.MinimumExpanding)
        self.setItemDelegate(OptionListItemDelegate())
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setMinimumWidth(self.sizeHintForColumn(0))

    def set_current_option(self, option_path):
        self.setCurrentItem(
            self.option_item_map[option_path]
        )

    def set_option_path_callback(self, *args, **kwargs):
        if self.set_option_path_fn:
            attr = Attribute.from_insertion(
                self.base_option_path,
                self.currentItem().option.get_end()
            )
            self.set_option_path_fn(attr)


class StaticAttrsOf(OptionScrollListSelector):
    def __init__(self, option_path, set_option_path_fn, selected=None, *args, **kwargs):
        super().__init__(option_path, set_option_path_fn)
        if selected:
            self.set_current_option(selected)


class DynamicAttrsOf(QtWidgets.QWidget):
    def __init__(self, statemodel, option_path, set_option_path_fn, selected=None, *args, **kwargs):
        super().__init__()

        self.statemodel = statemodel
        self.option_path = option_path

        self.list_widget = OptionScrollListSelector(option_path, set_option_path_fn)
        if selected:
            self.list_widget.set_current_option(selected)

        self.add_btn = QtWidgets.QPushButton("", self)
        self.add_btn.setIcon(icon.get_icon('plus.png'))
        self.add_btn.clicked.connect(self.add_clicked)

        self.remove_btn = QtWidgets.QPushButton("", self)
        self.remove_btn.setIcon(icon.get_icon('trash.png'))
        self.remove_btn.clicked.connect(self.remove_clicked)

        btn_hbox = QtWidgets.QHBoxLayout()
        btn_hbox.addWidget(ChangeTypeButton(option_path, "AttrsOf", set_option_path_fn))
        btn_hbox.addWidget(QtWidgets.QLabel(option_path.get_end()))
        btn_hbox.addWidget(self.add_btn)
        btn_hbox.addWidget(self.remove_btn)

        self.list_widget.itemDoubleClicked.connect(self.list_widget.editItem)
        self.list_widget.itemChanged.connect(self.rename_item)
        self.list_widget.model().rowsRemoved.connect(lambda: self.remove_item)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(btn_hbox)
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

    def remove_item(self, item):
        print('not implemented')

    def rename_item(self, item):
        self.statemodel.rename_option(item.previous_option, item.option)

    def add_clicked(self):
        item = OptionListItem(
            Attribute.from_insertion(self.option_path, 'newAttribute'),
            editable=True
        )
        self.list_widget.addItem(item)
        self.statemodel.add_new_option(item.option)
        self.list_widget.editItem(item)

    def remove_clicked(self):
        self.list_widget.takeItem(self.list_widget.currentItem())

    def insert_items(self):
        for option in api.get_option_tree().children(self.option_path):
            it = self.ItemCls(option)
            self.list_widget.addItem(it)


class DynamicListOf(QtWidgets.QWidget):
    def __init__(self, statemodel, option_path, set_option_path_fn, selected=None, *args, **kwargs):
        super().__init__()

        self.statemodel = statemodel
        self.option_path = option_path

        self.list_widget = OptionScrollListSelector(option_path, set_option_path_fn)
        if selected:
            self.list_widget.set_current_option(selected)

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
        btn_hbox.addWidget(ChangeTypeButton(option_path, "ListOf", set_option_path_fn))
        btn_hbox.addWidget(QtWidgets.QLabel(option_path.get_end()))
        btn_hbox.addWidget(self.add_btn)
        btn_hbox.addWidget(self.remove_btn)
        btn_hbox.addWidget(self.up_btn)
        btn_hbox.addWidget(self.down_btn)

        self.list_widget.itemDoubleClicked.connect(self.list_widget.editItem)
        self.list_widget.itemChanged.connect(self.rename_item)
        self.list_widget.model().rowsRemoved.connect(lambda: self.remove_item)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(btn_hbox)
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

    def remove_item(self, item):
        print('not implemented')

    def rename_item(self, item):
        self.statemodel.rename_option(item.previous_option, item.option)

    def add_clicked(self):
        item = OptionListItem(
            Attribute.from_insertion(self.option_path, 'newAttribute'),  # TODO: fix this
            editable=True
        )
        self.list_widget.addItem(item)
        self.statemodel.add_new_option(item.option)
        self.list_widget.editItem(item)

    def remove_clicked(self):
        self.list_widget.takeItem(self.list_widget.currentItem())

    def up_clicked(self):
        current_row = self.list_widget.currentRow()
        if current_row == 0:
            logger.info('Cannot move item up, current index is 0')
        current_item = self.list_widget.takeItem(current_row)
        self.list_widget.insertItem(current_row - 1, current_item)

    def down_clicked(self):
        last_item_idx = self.list_widget.count() - 1
        current_row = self.list_widget.currentRow()
        if current_row == last_item_idx:
            logger.info('Cannot move item up, current index is end of list')
        current_item = self.list_widget.takeItem(current_row)
        self.list_widget.addItem(current_item)

    def insert_items(self):
        for option in api.get_option_tree().children(self.option_path):
            it = self.ItemCls(option)
            self.list_widget.addItem(it)


class SearchResultListDisplay(QtWidgets.QListWidget):
    _setup_scroll_list_selector_theme = OptionScrollListSelector._setup_scroll_list_selector_theme

    def __init__(self, search_str, set_option_path_fn=None):
        super().__init__()

        self.set_option_path_fn = set_option_path_fn
        self.itemClicked.connect(self.set_option_path_callback)

        # load options
        tree = api.get_option_tree()
        for option_path, matched_operations in self.search_tree_for_options(tree, search_str):
            item = OptionListItem(
                option_path,
                use_full_option_path=True,
                use_child_count=False,
                extra_text='Matched ' + ', '.join(matched_operations)
            )
            self.addItem(item)

        self._setup_scroll_list_selector_theme()  # same look and feel as basic nav displays

    def search_tree_for_options(self, tree, search_str):
        # TODO: consider offloading this to nixui/options/search.py
        """
        1) search_str is tokenized
        Example: A search string of
            "foo bar" baz bif
        results in three search tokens

        2) The data of all optionis iterated over, with each token being checked for matches.
        For a given options inclusion, each tokens must match at least one search function.

        Match operations are prioritized in the following order:
        - token is a substring of the attribute path
        - token exactly matches the option type
        - token is in the option description
        - prioritizing in memory definition, then configured definition, then system default definition
          (TODO, awaiting https://github.com/nix-gui/nix-gui/issues/9)
          - token partially matches the unevaluated definition
          - token exactly matches the string form of the evaluated definition
        """
        tokens = set([
            t.lower() for t in
            next(csv.reader([search_str], delimiter=' ', quotechar='"'))
        ])
        attribute_path_score_map = {}
        for attribute_path, data in tree.iter_attribute_data():
            matched_tokens = set()
            matched_operations = collections.OrderedDict([
                ('Attribute Path', 0), ('Type', 0), ('Description', 0),
                ('In Memory Value', 0), ('Configured Value', 0),
                ('System Default Value', 0)
            ])
            for token in tokens:
                if token in str(attribute_path).lower():
                    matched_tokens.add(token)
                    matched_operations['Attribute Path'] += 1
                if data is not None:
                    if data._type_string != option_definition.Undefined and token in data._type_string.lower():
                        matched_tokens.add(token)
                        matched_operations['Type'] += 1
                    if data.description != option_definition.Undefined and token in data.description.lower():
                        matched_tokens.add(token)
                        matched_operations['Description'] += 1

            if matched_tokens == tokens:
                attribute_path_score_map[attribute_path] = (
                    tuple(matched_operations.values()),
                    tuple(k for k, v in matched_operations.items() if v > 0)
                )

        return [
            (attribute_path, matched_operations) for
            attribute_path, (score, matched_operations) in
            sorted(
                attribute_path_score_map.items(),
                key=lambda item: item[1][0],
                reverse=True
            )
        ]

    def set_option_path_callback(self, *args, **kwargs):
        if self.set_option_path_fn:
            self.set_option_path_fn(
                self.currentItem().option
            )


class ChangeTypeButton(QtWidgets.QPushButton):
    def __init__(self, base_option_path, option_type, set_option_path_fn):
        super().__init__()
        self.setText(option_type)
        self.clicked.connect(
            lambda:
            set_option_path_fn(
                base_option_path,
                display_as_single_field=True
            )
        )
