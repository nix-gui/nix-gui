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


Update = collections.namedtuple('Update', ['option', 'old_value', 'new_value'])


class StateModel:
    def __init__(self):
        self.update_history = []
        self.current_values = api.get_option_values_map()

        # TODO: is including the slotmapper overloading the StateModel? What are the alternatives?
        self.slotmapper = SlotMapper()
        self.slotmapper.add_slot('value_changed', self.record_update)
        self.slotmapper.add_slot('undo', self.undo)

    def get_value(self, option):
        return self.current_values[option]

    def get_update_set(self):
        original_values_map = api.get_option_values_map()
        return [
            Update(option, original_values_map[option], current_value)
            for option, current_value in self.current_values.items()
            if original_values_map[option] != current_value
        ]

    def record_update(self, option, new_value):
        old_value = self.current_values[option]
        if old_value != new_value:
            # replace old update if we're still working on the same option
            if self.update_history and option == self.update_history[-1].option:
                update = Update(option, self.update_history[-1].old_value, new_value)
                self.update_history[-1] = update
                self.slotmapper('update_recorded')(option, self.update_history[-1].old_value, new_value)
                logger.debug(f'update: {update}')
            else:
                update = Update(option, old_value, new_value)
                self.update_history.append(update)
                self.slotmapper('update_recorded')(option, old_value, new_value)
                logger.info(f'update: {update}')

            self.current_values[option] = new_value

    def persist_updates(self):
        option_new_value_map = {
            u.option: u.new_value
            for u in self.get_update_set()
        }
        save_path = api.apply_updates(option_new_value_map)
        self.slotmapper('changes_saved')(save_path)

    def undo(self, *args, **kwargs):
        last_update = self.update_history.pop()
        self.current_values[last_update.option] = last_update.old_value

        if not self.update_history:
            self.slotmapper('no_updates_exist')()

        self.slotmapper('undo_performed')(last_update.option, last_update.old_value, last_update.new_value)
        self.slotmapper(('update_field', last_update.option))()
