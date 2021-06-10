import collections
from dataclasses import dataclass, is_dataclass


class InfiniteDict(collections.defaultdict):
    def __init__(self):
        collections.defaultdict.__init__(self, self.__class__)

    def __setitem__(self, key, value):
        self.__setitem__(key, value)


LEAF = 0
COUNT = 1
SPECIAL_LABELS = (LEAF, COUNT)


class Tree:
    def __init__(self, tree=None):
        self.tree = tree or dict()

    def add_leaf(self, branch, value):
        node = self.tree
        for key in branch:
            if COUNT not in node:
                node[COUNT] = 0
            node[COUNT] += 1
            if key not in node:
                node[key] = {}
            node = node[key]

        node[LEAF] = value

    def get_children(self, branch=[]):
        node = self.tree
        for key in branch:
            node = node[key]
        return sorted([k for k in node.keys() if k not in SPECIAL_LABELS], key=lambda x: x.lower())

    def get_node(self, branch=[]):
        node = self.tree
        for key in branch:
            node = node[key]
        return Tree(node)

    def get_count(self, branch=[]):
        node = self.tree
        for key in branch:
            node = node[key]
        return node[COUNT] if COUNT in node else 0

    def get_leaf(self):
        return self.tree[LEAF] if LEAF in self.tree else {}





# decorator to wrap original __init__
def nested_dataclass(*args, **kwargs):

    def wrapper(check_class):

        # passing class to investigate
        check_class = dataclass(check_class, **kwargs)
        o_init = check_class.__init__

        def __init__(self, *args, **kwargs):

            for name, value in kwargs.items():

                # getting field type
                ft = check_class.__annotations__.get(name, None)

                if is_dataclass(ft) and isinstance(value, dict):
                    obj = ft(**value)
                    kwargs[name]= obj
                o_init(self, *args, **kwargs)
        check_class.__init__=__init__

        return check_class

    return wrapper(args[0]) if args else wrapper
