import collections

from nixui.options import api, types, state_update
from nixui.options.attribute import Attribute
from nixui.utils.logger import logger


class SlotMapper:
    def __init__(self):
        self.slot_fns = collections.defaultdict(list)

    def add_slot(self, key, slot):
        self.slot_fns[key].append(slot)

    def __call__(self, key):
        def fn(*args, **kwargs):
            for slot in self.slot_fns[key]:
                slot(*args, **kwargs)
        return fn


class StateModel:
    def __init__(self):
        self.update_history = []

        # TODO: is including the slotmapper overloading the StateModel? What are the alternatives?
        self.slotmapper = SlotMapper()
        self.slotmapper.add_slot('form_definition_changed', self.change_definition)
        self.slotmapper.add_slot('undo', self.undo)

    @property
    def option_tree(self):
        return api.get_option_tree()

    def get_definition(self, option):
        return self.option_tree.get_definition(option)

    def rename_option(self, old_option, option):
        self.option_tree.rename_attribute(old_option, option)
        update = state_update.RenameUpdate(
            old_attribute=old_option,
            new_attribute=option
        )
        self._record_update(update)

    def remove_option(self, option):
        subtree = self.option_tree.remove_attribute(option)
        update = state_update.RemoveUpdate(
            attribute=option,
            deleted_subtree=subtree
        )
        self._record_update(update)

    def add_new_option(self, parent_option):
        parent_type = self.option_tree.get_type(parent_option)

        # get best default name
        # TODO: logic for getting name should be moved to option_tree.py?
        child_keys = set([c[-1] for c in self.option_tree.children(parent_option).keys()])
        if isinstance(parent_type, types.ListOfType):
            new_child_attribute_path = Attribute.from_insertion(parent_option, f'[{len(child_keys)}]')
        elif isinstance(parent_type, types.AttrsOfType):
            suggested_child_key = 'newAttribute'
            for i in range(len(child_keys)):
                if suggested_child_key not in child_keys:
                    break
                suggested_child_key = f'newAttribute{i}'
            new_child_attribute_path = Attribute.from_insertion(parent_option, suggested_child_key)
        else:
            raise TypeError

        # add to option tree, append update, and return name
        self.option_tree.insert_attribute(new_child_attribute_path)
        update = state_update.CreateUpdate(attribute=new_child_attribute_path)
        self._record_update(update)
        return new_child_attribute_path

    def change_definition(self, option, new_definition):
        old_definition = self.option_tree.get_definition(option)
        if old_definition != new_definition:
            self.option_tree.set_definition(option, new_definition)
            update = state_update.ChangeDefinitionUpdate(
                option=option,
                old_definition=old_definition,
                new_definition=new_definition
            )
            self._record_update(update)

    def _record_update(self, update):
        merged_update = update.merge_with_previous_update(self.update_history[-1]) if self.update_history else None
        if merged_update:
            self.update_history[-1] = merged_update
            logger.debug(f'updates merged: {update} -> {merged_update}')
            self.slotmapper('update_recorded')(merged_update.details_string())
        else:
            self.update_history.append(update)
            logger.info(f'update recorded: {update}')
            self.slotmapper('update_recorded')(update.details_string)

    def undo(self, *args, **kwargs):
        last_update = self.update_history.pop()
        last_update.revert(self.option_tree)

        if not self.update_history:
            self.slotmapper('no_updates_exist')()

        self.slotmapper('undo_performed')(last_update.details_string())
        self.slotmapper('reload_attribute')(
            last_update.reversion_impacted_attribute()
        )
