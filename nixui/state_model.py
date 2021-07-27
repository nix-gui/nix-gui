import collections

from nixui.options import api
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


Update = collections.namedtuple('Update', ['option', 'old_definition', 'new_definition'])


class StateModel:
    def __init__(self):
        self.update_history = []
        self.option_tree = api.get_option_tree()

        # TODO: is including the slotmapper overloading the StateModel? What are the alternatives?
        self.slotmapper = SlotMapper()
        self.slotmapper.add_slot('value_changed', self.record_update)
        self.slotmapper.add_slot('undo', self.undo)

    def get_definition(self, option):
        return self.option_tree.get_definition(option)

    def get_update_set(self):
        return [
            Update(option, configured_value, current_value)
            for option, configured_value, current_value in self.option_tree.iter_changes()
        ]

    def rename_option(self, old_option, option):
        self.option_tree.rename_attribute(old_option, option)

    def add_new_option(self, option):
        self.option_tree.insert_attribute(option)

    def record_update(self, option, new_definition):
        old_definition = self.option_tree.get_definition(option)
        if old_definition != new_definition:
            # replace old update if we're still working on the same option
            if self.update_history and option == self.update_history[-1].option:
                update = Update(option, self.update_history[-1].old_definition, new_definition)
                self.update_history[-1] = update
                self.slotmapper('update_recorded')(option, self.update_history[-1].old_definition, new_definition)
                logger.debug(f'update: {update}')
            else:
                update = Update(option, old_definition, new_definition)
                self.update_history.append(update)
                self.slotmapper('update_recorded')(option, old_definition, new_definition)
                logger.info(f'update: {update}')

            self.option_tree.set_definition(option, new_definition)

    def persist_updates(self):
        option_new_definition_map = {
            u.option: u.new_definition
            for u in self.get_update_set()
        }
        save_path = api.apply_updates(option_new_definition_map)
        self.slotmapper('changes_saved')(save_path)

    def undo(self, *args, **kwargs):
        last_update = self.update_history.pop()
        self.option_tree.set_value(last_update.option, last_update.old_definition)

        if not self.update_history:
            self.slotmapper('no_updates_exist')()

        self.slotmapper('undo_performed')(last_update.option, last_update.old_definition, last_update.new_definition)
        self.slotmapper(('update_field', last_update.option))()
