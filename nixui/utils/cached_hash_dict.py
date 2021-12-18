# from https://stackoverflow.com/a/39375731
class CachedHashDict(dict):
    __slots__ = ()  # no __dict__ - that would be redundant

    def __init__(self, *args, **kwargs):
        dict.__init__(*args, **kwargs)
        self._recalculate_hash()

    def __hash__(self):
        return self._hash

    def __setitem__(self, *args, **kwargs):
        res = super().__setitem__(*args, **kwargs)
        self._recalculate_hash()
        return res

    def __delitem__(self, *args, **kwargs):
        res = super().__delitem__(*args, **kwargs)
        self._recalculate_hash()
        return res

    def pop(self, *args, **kwargs):
        res = super().pop(*args, **kwargs)
        self._recalculate_hash()
        return res

    def update(self, *args, **kwargs):
        res = dict.update(*args, **kwargs)
        self._recalculate_hash()
        return res

    def _recalculate_hash(self):
        self._hash = hash(tuple(sorted(self.items())))
