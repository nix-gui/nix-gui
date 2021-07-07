import collections


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

    @staticmethod
    def get_child_node(node, key):
        if key in node:
            return node[key]
        elif '<name>' in node:
            return node['<name>']
        elif '*' in node:
            return node['*']
        else:
            raise ValueError()

    def get_children(self, branch=[]):
        node = self.tree
        for key in branch:
            node = self.get_child_node(node, key)
        return sorted([k for k in node.keys() if k not in SPECIAL_LABELS], key=lambda x: x.lower())

    def get_node(self, branch=[]):
        node = self.tree
        for key in branch:
            node = self.get_child_node(node, key)
        return Tree(node)

    def get_count(self, branch=[]):
        node = self.tree
        for key in branch:
            node = self.get_child_node(node, key)
        return node[COUNT] if COUNT in node else 0

    def get_leaf(self):
        return self.tree[LEAF] if LEAF in self.tree else {}
