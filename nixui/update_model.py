import collections

from nixui import api


Update = collections.namedtuple('Update', ['option', 'old_value', 'new_value'])


class UpdateModel:
    def __init__(self, slotmapper):
        # TODO: is including the slotmapper failing to encapsulate the UpdateModel? What are the alternatives?
        self.slotmapper = slotmapper

        self.update_history = []
        self.current_values = {
            opt: api.get_option_value(opt)
            for opt in api.get_options_dict().keys()
        }

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
