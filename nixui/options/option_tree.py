import dataclasses
import functools
import uuid

from treelib import Tree, Node
import treelib.exceptions

from nixui.options import types
from nixui.options.attribute import Attribute
from nixui.options.option_definition import OptionDefinition, Undefined


@dataclasses.dataclass
class OptionData:
    is_declared_option: bool = False  # the node is part of a declaraed option or part of Attrs/List defining one
    description: str = Undefined
    readOnly: bool = Undefined
    _type_string: str = Undefined
    _type: types.NixType = Undefined
    system_default_definition: OptionDefinition = OptionDefinition.undefined()
    configured_definition: OptionDefinition = OptionDefinition.undefined()
    in_memory_definition: OptionDefinition = OptionDefinition.undefined()

    def get_type(self):
        if self._type == Undefined:
            if self._type_string == Undefined:
                return types.AttrsType()
            else:
                return types.from_nix_type_str(self._type_string)
        else:
            return self._type

    # based on https://stackoverflow.com/a/61426351
    def update(self, new):
        for key, value in new.items():
            if hasattr(self, key):
                setattr(self, key, value)
            elif hasattr(self, f'_{key}'):
                setattr(self, f'_{key}', value)

    def copy(self):
        return dataclasses.replace(self)


class OptionTree:
    """
    Data structure managing option retrieval, option setting, and special handling for attribute sets of submodules

    system_option_data: mapping from Attribute to dict containing {'description', 'readOnly', 'type', 'default'}
    config_options: mapping from Attribute to configured definition

    in_memory_change_cache is a dictionary storing all changes made to the tree. This makes calculating the hash of
    the OptionTree trivial. Note that a value of `Undefined` indicates deletion of the definition.
    """
    def __init__(self, system_option_data, config_options):
        # load data into Tree with OptionData leaves
        self.tree = Tree()
        self.tree.create_node(identifier=Attribute([]), data=OptionData(_type=types.AttrsType()))

        # cache for faster lookup of changed nodes
        self.in_memory_change_cache = {}
        self.configured_change_cache = {}
        self.change_marker = None

        # insert option data with parent option data inserted first via `sorted`
        sort_key = lambda s: str(s[0]).replace('"<name>"', '')  # todo, clean up this hack
        for option_path, option_data_dict in sorted(system_option_data.items(), key=sort_key):
            self._upsert_node_data(
                option_path,
                {
                    'is_declared_option': True,
                    **option_data_dict,
                }
            )
        for option_path, option_definition in config_options.items():
            self._upsert_node_data(option_path, {'configured_definition': option_definition})
            self.configured_change_cache[option_path] = option_definition

    def __hash__(self):
        return hash(self.change_marker)

    def __eq__(self, other):
        # hack, only should be used to enable lru_cache for OptionTree methods
        return hash(self) == hash(other)

    def _upsert_node_data(self, option_path, option_data_dict):
        """
        update option_path leaf with option_data_dict
        insert branch if it doesn't exist
        clone attribute-set-of branch for new upsertions
        """
        if not self.tree.get_node(option_path):
            # Insert Attribute([]), then Attribute('foo'), then Attribute('foo.bar') into tree
            parent_option_path = Attribute([])
            for option_path_key in option_path:
                child_option_path = Attribute.from_insertion(parent_option_path, option_path_key)
                if child_option_path not in self.tree:
                    # copy attribute-set-of spec to new branch if branch doesn't yet exist
                    if self._is_attribute_set(parent_option_path) and child_option_path.get_end() != '<name>':
                        new_branch = self._get_attribute_set_template_branch(child_option_path)
                        self.tree.paste(parent_option_path, new_branch)
                    else:
                        self.tree.create_node(
                            child_option_path,
                            child_option_path,
                            parent=parent_option_path,
                            data=OptionData(
                                _type=self.get_type(parent_option_path).child_type or Undefined
                            )
                        )
                parent_option_path = child_option_path

        option_data = self.tree.get_node(option_path).data or OptionData()
        option_data.update(option_data_dict)
        self.tree.update_node(option_path, data=option_data)

    def _is_attribute_set(self, attribute):
        data = self.tree.get_node(attribute).data
        if data:
            return isinstance(data.get_type(), types.AttrsOfType)
        return False

    def _get_attribute_set_template_branch(self, attribute):
        """
        AttributeSetOf type attribute paths are parents of attribute paths which inherit their OptionData
        This method constructs a new branch for `attribute` labelled with the OptionData from its parent
        """
        parent_attribute = attribute.get_set()
        data = self.tree.get_node(parent_attribute).data  # get spec of parent attribute
        if data.get_type() == types.AttrsOfType(types.SubmoduleType()):
            submodule_spec_attribute = Attribute.from_insertion(parent_attribute, '<name>')
            tree = Tree(self.tree.subtree(submodule_spec_attribute), deep=True)
            # <name> -> actual attribute
            for node in tree.all_nodes():
                attr = node.identifier
                loc = list(attr.loc)
                loc[loc.index('<name>')] = attribute.loc[-1]
                new_attr = Attribute(loc)
                tree.update_node(attr, identifier=new_attr, tag=new_attr)
            return tree
        else:
            option_data_spec = data.copy()
            # TODO https://github.com/nix-gui/nix-gui/issues/65
            option_data_spec._type = data.get_type().child_type
            tree = Tree()
            node = Node(attribute, attribute, data=option_data_spec)
            tree.add_node(node)
            return tree

    def _get_data(self, attribute):
        result = self.tree.get_node(attribute).data
        if result == None:
            raise ValueError()
        return result

    def iter_changes(self, get_configured_changes=False):
        """
        Iterate over each attribute which has been changed, their old definition and new definition.
        If an options definition is distinct from the its old setting it is included.

        get_configured_changes:
            If true, iterate over differences between systems defaults and changes in memory / in `nixos-config`
            If false, iterate over differences between in memory changes and system defaults / `nixos-config
        """
        if get_configured_changes:
            change_cache = self.configured_change_cache
        else:
            change_cache = self.in_memory_change_cache
        for attr, new_definition in change_cache.items():
            old_definition = self.get_definition(
                attr,
                include_in_memory_definition=False,
                include_configured_change=not get_configured_changes
            )
            if new_definition != old_definition:
                yield (attr, old_definition, new_definition)

    @functools.lru_cache()
    def get_change_set_with_ancestors(self, get_configured_changes=False):
        attributes_with_mutated_descendents = set()
        for attr, old_d, new_d in self.iter_changes(get_configured_changes):
            for i in range(len(attr)):
                attributes_with_mutated_descendents.add(attr[:i])
        return attributes_with_mutated_descendents

    def iter_attribute_data(self):
        for node in self.tree.all_nodes():
            if '<name>' not in node.tag:
                yield (node.identifier, node.data)

    def iter_attributes(self):
        for attr, _ in self.iter_attribute_data():
            yield attr

    def insert_attribute(self, attribute):
        # update tree
        self._upsert_node_data(attribute, {})
        # update in_memory_change_cache
        self.in_memory_change_cache[attribute] = OptionDefinition.undefined()

    def rename_attribute(self, old_attribute, new_attribute):
        # update in_memory_change_cache
        if old_attribute in self.in_memory_change_cache:
            self.in_memory_change_cache[new_attribute] = self.in_memory_change_cache[old_attribute]
            del self.in_memory_change_cache[old_attribute]
        # update tree
        self.tree.update_node(old_attribute, identifier=new_attribute, tag=new_attribute)
        for node in self.tree.children(new_attribute):
            old_child_attribute = node.identifier
            new_child_attribute = Attribute.from_insertion(new_attribute, old_child_attribute.get_end())
            self.rename_attribute(old_child_attribute, new_child_attribute)

    def remove_attribute(self, attribute):
        # update in memory change cache
        old_in_memory_definitions = {}
        for node in self.tree.subtree(attribute).all_nodes():
            if node.identifier in self.in_memory_change_cache:
                old_in_memory_definitions[node.identifier] = self.in_memory_change_cache[node.identifier]
            self.in_memory_change_cache[node.identifier] = OptionDefinition.undefined()
        # update tree
        deleted_subtree = self.tree.remove_subtree(attribute)
        return old_in_memory_definitions, deleted_subtree

    def set_definition(self, option_path, option_definition):
        # update tree
        self._upsert_node_data(option_path, {'in_memory_definition': option_definition})
        # update in memory change cache
        in_memory_definition = self.tree.get_node(option_path).data.in_memory_definition
        if in_memory_definition == self.tree.get_node(option_path).data.configured_definition:
            if option_path in self.in_memory_change_cache:
                del self.in_memory_change_cache[option_path]
        else:
            self.in_memory_change_cache[option_path] = option_definition

    def get_definition(self, attribute, include_in_memory_definition=True, include_configured_change=True):
        if include_in_memory_definition:
            in_memory_definition = self.get_in_memory_definition(attribute)
            if in_memory_definition != OptionDefinition.undefined():
                return self.get_in_memory_definition(attribute)

        if include_configured_change:
            configured_definition = self.get_configured_definition(attribute)
            if configured_definition != OptionDefinition.undefined():
                return configured_definition

        system_default_definition = self.get_system_default_definition(attribute)
        return system_default_definition

    def get_in_memory_definition(self, attribute):
        return self._get_data(attribute).in_memory_definition

    def get_configured_definition(self, attribute):
        return self._get_data(attribute).configured_definition

    def get_system_default_definition(self, attribute):
        return self._get_data(attribute).system_default_definition

    def get_type(self, attribute):
        return self._get_data(attribute).get_type()

    def get_type_string(self, attribute):
        return self._get_data(attribute)._type_string

    def get_description(self, attribute):
        return self._get_data(attribute).description

    def is_readonly(self, attribute):
        return self._get_data(attribute).readOnly

    def is_declared_option(self, attribute):
        return self._get_data(attribute).is_declared_option

    def children(self, attribute, mode="direct"):
        """
        attribute: the key to explore children of
        mode:
        - "direct": get direct descendents
        - "full": get all descendents
        - "leaves": get only descendents which have no children
        """
        try:
            if mode == "direct":
                children = self.tree.children(attribute)
            elif mode == "leaves":
                children = self.tree.leaves(attribute)
            else:
                raise ValueError()
        except treelib.exceptions.NodeIDAbsentError:
            raise ValueError()
        return {
            node.tag: node.data
            for node in children
            if '"<name>"' not in node.tag
        }

    @functools.lru_cache(100000)  # this breaks when nixos has 100,000 attributes
    def count_leaves(self, attribute):
        child_ids = self.tree.is_branch(attribute)
        if child_ids:
            return sum(map(self.count_leaves, child_ids))
        return 1

    def get_next_branching_option(self, attribute):
        while len(self.children(attribute)) == 1:
            attribute = self.children(attribute)[0]
        return attribute
