from nixui.options import api, types, option_definition
from nixui.graphics import color_indicator, richtext, generic_widgets, field_widgets, toggle_switch

from PyQt5 import QtWidgets, QtGui, QtCore


def get_field_widget_classes_from_type(option_type):
    if isinstance(option_type, types.ListOfType):
        return [field_widgets.ListOfRedirect]
    elif isinstance(option_type, types.AttrsOfType):
        return [field_widgets.AttrsOfRedirect]
    elif isinstance(option_type, types.AttrsType):
        return [field_widgets.AttrsRedirect]
    elif isinstance(option_type, types.SubmoduleType):
        return [field_widgets.SubmoduleRedirect]
    elif isinstance(option_type, types.EitherType):
        widgets = set()
        for subtype in option_type.subtypes:
            widgets |= set(get_field_widget_classes_from_type(subtype))
        return list(widgets)
    elif isinstance(option_type, types.UnspecifiedType):
        return [field_widgets.UndefinedField]
    elif isinstance(option_type, types.NullType):
        return [field_widgets.NullField]
    elif isinstance(option_type, types.BoolType):
        return [field_widgets.BooleanField]
    elif isinstance(option_type, types.StrType):
        return [field_widgets.TextField]
    elif isinstance(option_type, types.IntType):
        return [field_widgets.IntegerField]
    elif isinstance(option_type, types.FloatType):
        return [field_widgets.FloatField]
    elif isinstance(option_type, types.OneOfType):
        return [field_widgets.OneOfField]
    elif isinstance(option_type, types.PathType):
        return [field_widgets.NotImplementedField]
    elif isinstance(option_type, types.PackageType):
        return [field_widgets.NotImplementedField]
    elif isinstance(option_type, types.FunctionType):
        return [field_widgets.NotImplementedField]
    elif isinstance(option_type, types.AnythingType):
        return [field_widgets.NotImplementedField]
    else:
        raise NotImplementedError(option_type)


def get_field_widget_classes(option_type):
    return (
        get_field_widget_classes_from_type(option_type) +
        [field_widgets.ExpressionField, field_widgets.ReferenceField]
    )


def get_label_color_for_widget(field_widget):
    field_colors = {
        field_widgets.ExpressionField: QtGui.QColor(193, 236, 245),
        field_widgets.ReferenceField: QtGui.QColor(174, 250, 174),
    }
    return field_colors.get(
        type(field_widget),
        QtGui.QColor(255, 255, 240),  # default
    )


class GenericOptionDisplay(QtWidgets.QWidget):
    def __init__(self, statemodel, set_option_path_fn, option, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.statemodel = statemodel
        self.set_option_path_fn = set_option_path_fn
        self.option = option

        # vbox containing read-only option details and "is-defined" toggle switch
        description_layout = QtWidgets.QVBoxLayout()
        description_layout.addLayout(
            self._get_option_details_layout(option, set_option_path_fn)
        )
        self.is_defined_toggle = toggle_switch.ToggleSwitch("Defined", "Undefined")
        self.is_defined_toggle.stateChanged.connect(self.update_defined_field_visibility)
        description_layout.addWidget(self.is_defined_toggle)
        description_layout.addStretch()  # align widgets to top

        # field widget selector and stacked widget containing field widgets for display
        self.field_widgets = self._get_field_widgets(option)
        self.entry_stack = self._get_entry_stack(self.field_widgets)
        self.field_selector = self._get_field_selection_widget(self.field_widgets)

        # put together horizontally
        layout = QtWidgets.QHBoxLayout()
        layout.addLayout(description_layout)
        layout.addWidget(self.field_selector)
        layout.addStretch()
        layout.addWidget(self.entry_stack)
        self.setLayout(layout)

        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)

        self._load_definition()

    @staticmethod
    def _get_option_details_layout(option, set_option_path_fn):
        # title and description
        text = generic_widgets.ClickableLabel(str(option))
        text.clicked.connect(lambda: set_option_path_fn(option))
        description_text = api.get_option_tree().get_description(option)
        tooltip = generic_widgets.ToolTip(
            richtext.get_option_html(
                option,
                type_label=api.get_option_tree().get_type(option),
                description=description_text if description_text != option_definition.Undefined else None,
            )
        )
        option_details_layout = QtWidgets.QHBoxLayout()
        option_details_layout.addWidget(tooltip)
        option_details_layout.addWidget(text)
        option_details_layout.addStretch()
        return option_details_layout

    def _get_field_widgets(self, option):
        field_widget_classes = get_field_widget_classes(
            types.from_nix_type_str(
                api.get_option_tree().get_type(option)
            )
        )
        fields = []
        for field_widget_class in field_widget_classes:
            field = field_widget_class(option)
            # TODO: fix this hacky handling of `Redirect` (#109)
            if not isinstance(field, field_widgets.Redirect):
                field.stateChanged.connect(self.handle_state_change)
                self.statemodel.slotmapper.add_slot(('update_field', option), self._load_definition)
            fields.append(field)
        return fields

    def _get_entry_stack(self, field_widgets):
        entry_stack = QtWidgets.QStackedWidget()
        for w in field_widgets:
            entry_stack.addWidget(
                generic_widgets.CenteredContainer(w)
            )
        return entry_stack

    def _get_field_selection_widget(self, field_widgets):
        exclusive_btn_group = generic_widgets.ExclusiveButtonGroup(
            choices=[
                (
                    w.name,
                    self.load_selected_field_widget,
                    get_label_color_for_widget(w)
                )
                for w in field_widgets
            ]
        )
        # TODO: remove this when reference editor is done
        # disable reference editor button
        exclusive_btn_group.btn_group.buttons()[-1].setEnabled(False)
        return exclusive_btn_group

    def _load_definition(self):
        option_definition = self.statemodel.get_definition(self.option)

        self.is_defined_toggle.setChecked(not option_definition.is_undefined)
        self.update_defined_field_visibility()
        if option_definition.is_undefined:
            return

        for i, field in enumerate(self.field_widgets):
            if isinstance(field, field_widgets.Redirect):
                continue
            elif isinstance(field, field_widgets.ExpressionField):
                self.field_selector.select(i)
                field.load_value(option_definition.expression_string)
                break
            elif field.validate_field(option_definition.obj):
                self.field_selector.select(i)
                field.load_value(option_definition.obj)
                break

    def load_selected_field_widget(self, arg=None):
        stack_idx = self.field_selector.checked_index()
        current_widget = self.field_widgets[stack_idx]
        definition = self.statemodel.get_definition(self.option)
        # TODO: fix this hacky handling of `Redirect` (#109)
        if isinstance(current_widget, field_widgets.Redirect):
            self.set_option_path_fn(self.option, current_widget.option_type)
            return
        elif isinstance(current_widget, field_widgets.ExpressionField):
            current_widget.load_value(definition.expression_string)
        else:
            current_widget.load_value(definition.obj)
        self.entry_stack.setCurrentIndex(stack_idx)
        self.handle_state_change()

    def update_defined_field_visibility(self):
        if self.is_defined_toggle.isChecked():
            self.field_selector.setVisible(True)
            self.entry_stack.setVisible(True)
            self.field_selector.select(0)
        else:
            self.field_selector.setVisible(False)
            self.entry_stack.setVisible(False)
        self.handle_state_change()

    def handle_state_change(self):
        self.statemodel.slotmapper('form_definition_changed')(self.option, self.definition)

    @property
    def definition(self):
        if not self.is_defined_toggle.isChecked():
            return option_definition.OptionDefinition.undefined()
        current_widget = self.field_widgets[self.entry_stack.currentIndex()]
        if isinstance(current_widget, field_widgets.Redirect):
            #  TODO: implement getting definition based on value of descendents
            return option_definition.OptionDefinition.from_object('CHECK DESCENDENTS')
        form_value = current_widget.current_value
        if isinstance(current_widget, field_widgets.ExpressionField):
            return option_definition.OptionDefinition.from_expression_string(form_value)
        else:
            return option_definition.OptionDefinition.from_object(form_value)

    def contains_focus(self):
        return (
            self.hasFocus() or
            any(w.hasFocus() for w in self.field_widgets) or
            any(w.hasFocus() for w in self.field_selector.btn_group.buttons())
        )

    def paint_background_color(self, bg_color):
        qp = QtGui.QPainter(self)
        r = QtCore.QRect(0, 0, self.width(), self.height())
        qp.fillRect(r, bg_color)
        qp.end()

    def paintEvent(self, ev):
        super().paintEvent(ev)
        if self.contains_focus():
            self.paint_background_color(
                QtGui.QColor(233, 245, 248)
            )
        else:
            bg_color = color_indicator.get_edit_state_color_indicator(
                api.get_option_tree(),
                self.option
            )
            self.paint_background_color(bg_color)
        self.update()
