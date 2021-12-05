import collections

from nixui.options import api, attribute, types
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

        # TODO: is including the slotmapper overloading the StateModel? What are the alternatives?
        self.slotmapper = SlotMapper()
        self.slotmapper.add_slot('form_definition_changed', self.record_update)
        self.slotmapper.add_slot('undo', self.undo)

    @property
    def option_tree(self):
        return api.get_option_tree()

    def get_definition(self, option):
        return self.option_tree.get_definition(option)

    def get_update_set(self):
        return [
            Update(option, configured_value, current_value)
            for option, configured_value, current_value in self.option_tree.iter_changes()
        ]

    def rename_option(self, old_option, option):
        self.option_tree.rename_attribute(old_option, option)

    def add_new_option(self, parent_option):
        parent_type = self.option_tree.get_type(parent_option)

        # get best default name
        child_keys = set([c[-1] for c in self.option_tree.children(parent_option).keys()])
        if isinstance(parent_type, types.ListOfType):
            new_child_attribute_path = attribute.Attribute.from_insertion(parent_option, f'[{len(child_keys)}]')
        elif isinstance(parent_type, types.AttrsOfType):
            suggested_child_key = 'newAttribute'
            for i in range(len(child_keys)):
                if suggested_child_key not in child_keys:
                    break
                suggested_child_key = f'newAttribute{i}'
            new_child_attribute_path = attribute.Attribute.from_insertion(parent_option, suggested_child_key)
        else:
            raise TypeError

        # add to option tree and return name
        self.option_tree.insert_attribute(new_child_attribute_path)
        return new_child_attribute_path

    def record_update(self, option, new_definition):
        old_definition = self.option_tree.get_definition(option)
        if old_definition != new_definition:
            if self.update_history and option == self.update_history[-1].option:
                # replace old update if we're still working on the same option
                update = Update(option, self.update_history[-1].old_definition, new_definition)
                self.update_history[-1] = update
                logger.debug(f'update: {update}')
            else:
                update = Update(option, old_definition, new_definition)
                self.update_history.append(update)
                logger.info(f'update: {update}')

            self.slotmapper('update_recorded')(
                option,
                update.old_definition.expression_string,
                update.new_definition.expression_string,
            )
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
        self.option_tree.set_definition(last_update.option, last_update.old_definition)

        if not self.update_history:
            self.slotmapper('no_updates_exist')()

        self.slotmapper('undo_performed')(last_update.option, last_update.old_definition, last_update.new_definition)
        self.slotmapper(('update_field', last_update.option))()
