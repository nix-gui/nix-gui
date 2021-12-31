import collections
import uuid

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

    def swap_options(self, option0, option1):
        # TODO: fix this hack, only using <name> because it isn't shown in OptionTree.children
        placeholder = Attribute(f'"<name>".{uuid.uuid4()}')
        self.option_tree.rename_attribute(option0, placeholder)
        self.option_tree.rename_attribute(option1, option0)
        self.option_tree.rename_attribute(placeholder, option1)
        update = state_update.SwapNamesUpdate(
            attribute0=option0,
            attribute1=option1,
        )
        self._record_update(update)

    def remove_option(self, option):
        old_in_memory_definitions, deleted_subtree = self.option_tree.remove_attribute(option)
        update = state_update.RemoveUpdate(
            attribute=option,
            deleted_subtree=deleted_subtree,
            old_in_memory_definitions=old_in_memory_definitions
        )
        self._record_update(update)

    def get_new_child_option_name(self, parent_option, parent_type=None):
        parent_type = parent_type or self.option_tree.get_type(parent_option)
        child_keys = set([c[-1] for c in self.option_tree.children(parent_option).keys()])
        if isinstance(parent_type, types.ListOfType):
            return Attribute.from_insertion(parent_option, f'[{len(child_keys)}]')
        elif isinstance(parent_type, types.AttrsOfType):
            suggested_child_key = 'newAttribute'
            for i in range(len(child_keys)):
                if suggested_child_key not in child_keys:
                    break
                suggested_child_key = f'newAttribute{i}'
            return Attribute.from_insertion(parent_option, suggested_child_key)
        else:
            raise TypeError

    def add_new_option(self, option):
        # add to option tree, append update, and return name
        self.option_tree.insert_attribute(option)
        update = state_update.CreateUpdate(attribute=option)
        self._record_update(update)

    def change_definition(self, option, new_definition):
        old_definition = self.option_tree.get_definition(option)
        if old_definition != new_definition:
            self.option_tree.set_definition(option, new_definition)
            update = state_update.ChangeDefinitionUpdate(
                attribute=option,
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

    def get_diffs(self):
        diffs = {}
        for attr, new_value in self.option_tree.get_changes().items():
            diffs[attr] = (
                self.option_tree.get_configured_definition(attr),
                new_value
            )
        return diffs

    def persist_changes(self):
        save_path = api.persist_changes(self.option_tree.get_changes())
        self.slotmapper('changes_saved')(save_path)
