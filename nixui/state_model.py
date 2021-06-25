import collections

from nixui import api, slot_mapper


Update = collections.namedtuple('Update', ['option', 'old_value', 'new_value'])


class StateModel:
    def __init__(self):
        self.update_history = []
        self.current_values = {
            opt: api.get_option_value(opt)
            for opt in api.get_options_dict().keys()
        }

        # TODO: is including the slotmapper overloading the StateModel? What are the alternatives?
        self.slotmapper = slot_mapper.SlotMapper()
        self.slotmapper.add_slot('value_changed', self.record_update)
        self.slotmapper.add_slot('undo', self.undo)

    def get_value(self, option):
        return self.current_values[option]

    def record_update(self, option, new_value):
        old_value = self.current_values[option]
        if old_value != new_value:
            self.update_history.append(
                Update(option, old_value, new_value)
            )
            self.current_values[option] = new_value

        self.slotmapper('update_recorded')(option, old_value, new_value)

    def undo(self, *args, **kwargs):
        last_update = self.update_history.pop()
        self.current_values[last_update.option] = last_update.old_value

        self.slotmapper('undo_performed')(last_update.option, last_update.old_value, last_update.new_value)
        self.slotmapper(('update_field', last_update.option))(last_update.old_value)
