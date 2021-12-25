from collections.abc import MutableMapping


# based on https://stackoverflow.com/a/3387975
class CachedHashDict(MutableMapping):
    """A dictionary that applies an arbitrary key-altering
       function before accessing the keys"""

    def __init__(self, *args, **kwargs):
        self.store = dict()
        self.update(dict(*args, **kwargs))

        self._hash = None
        self._recalculate_hash()
        self.has_changed = False

    def __hash__(self):
        if self.has_changed:
            self._recalculate_hash()
        self.has_changed = False
        return self._hash

    def __getitem__(self, key):
        return self.store[self._keytransform(key)]

    def __setitem__(self, key, value):
        self.store[self._keytransform(key)] = value
        self.has_changed = True

    def __delitem__(self, key):
        del self.store[self._keytransform(key)]
        self.has_changed = True

    def __iter__(self):
        return iter(self.store)

    def __len__(self):
        return len(self.store)

    def __repr__(self):
        return f'CachedHashDict({repr(self.store)})'

    def _keytransform(self, key):
        return key

    def _recalculate_hash(self):
        self._hash = hash(tuple(sorted(self.items())))
