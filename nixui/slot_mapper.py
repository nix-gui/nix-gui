import collections


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
