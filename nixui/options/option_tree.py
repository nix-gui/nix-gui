import dataclasses
from treelib import Tree, Node
import typing

from nixui.options.attribute import Attribute


class UndefinedType:
    def __eq__(self, other):
        return isinstance(other, self.__class__)
Undefined = UndefinedType()


@dataclasses.dataclass
class OptionData:
    description: str = Undefined
    readOnly: bool = Undefined
    _type: str = Undefined
    system_default: typing.Any = Undefined
    configured_value: typing.Any = Undefined
    in_memory_value: typing.Any = Undefined

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

    system_options: mapping from Attribute to dict containing {'description', 'readOnly', 'type', 'default'}
    config_options: mapping from Attribute to configured value
    """
    def __init__(self, system_option_data, config_options):
        # load data into Tree with OptionData leaves
        self.tree = Tree()
        self.root = Attribute([])
        self.tree.create_node(identifier=self.root, data=OptionData(_type='PARENT'))

        # insert option data with parent option data inserted first via `sorted`
        for option_path, option_data_dict in sorted(system_option_data.items(), key=str):
            self._upsert_node_data(option_path, option_data_dict)
        for option_path, value in config_options.items():
            self._upsert_node_data(option_path, {'configured_value': value})

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
                    if self._is_attribute_set(parent_option_path) and str(child_option_path.get_end()) != '<name>':
                        new_branch = self._get_attribute_set_template_branch(child_option_path)
                        self.tree.paste(parent_option_path, new_branch)
                    else:
                        self.tree.create_node(
                            child_option_path,
                            child_option_path,
                            parent=parent_option_path,
                            data=OptionData(_type='PARENT')
                        )
                parent_option_path = child_option_path

        option_data = self.tree.get_node(option_path).data or OptionData()
        option_data.update(option_data_dict)
        self.tree.update_node(option_path, data=option_data)

    def _is_attribute_set(self, attribute):
        data = self.tree.get_node(attribute).data
        if data:
            return 'attribute set of' in data._type  # TODO https://github.com/nix-gui/nix-gui/issues/65
        return False

    def _get_attribute_set_template_branch(self, attribute):
        """
        AttributeSetOf type attribute paths are parents of attribute paths which inherit their OptionData
        This method constructs a new branch for `attribute` labelled with the OptionData from its parent
        """
        parent_attribute = attribute.get_set()
        data = self.tree.get_node(parent_attribute).data  # get spec of parent attribute
        if data._type == 'attribute set of submodules':
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
            option_data_spec._type = data._type.removeprefix('attribute set of ').removesuffix('s')
            tree = Tree()
            node = Node(attribute, attribute, data=option_data_spec)
            tree.add_node(node)
            return tree

    def _get_data(self, attribute):
        if self.tree.get_node(attribute).data is None:
            raise ValueError()
        return self.tree.get_node(attribute).data

    def iter_changes(self):
        for node in self.tree.all_nodes():
            attr = node.tag
            old_value = self.get_value(node.tag, include_in_memory_value=False)
            new_value = self.get_value(node.tag)
            if new_value != old_value:
                yield (attr, old_value, new_value)

    def insert_attribute(self, attribute):
        self._upsert_node_data(attribute, {})

    def rename_attribute(self, old_attribute, new_attribute):
        self.tree.update_node(old_attribute, identifier=new_attribute, tag=new_attribute)

    def set_value(self, option_path, value):
        self._upsert_node_data(option_path, {'in_memory_value': value})

    def get_value(self, attribute, include_in_memory_value=True):
        if include_in_memory_value and self.get_in_memory_value(attribute) != Undefined:
            return self.get_in_memory_value(attribute)
        elif self.get_configured_value(attribute) != Undefined:
            return self.get_configured_value(attribute)
        elif self.get_system_default(attribute) != Undefined:
            return self.get_system_default(attribute)
        else:
            return Undefined

    def get_in_memory_value(self, attribute):
        return self._get_data(attribute).in_memory_value

    def get_configured_value(self, attribute):
        return self._get_data(attribute).configured_value

    def get_system_default(self, attribute):
        return self._get_data(attribute).system_default

    def get_type(self, attribute):
        return self._get_data(attribute)._type

    def get_description(self, attribute):
        return self._get_data(attribute).description

    def is_readonly(self, attribute):
        return self._get_data(attribute).readOnly

    def children(self, attribute=None, recursive=False):
        attribute = attribute or self.root
        if recursive:
            children = self.tree.leaves(attribute)
        else:
            children = self.tree.children(attribute)
        return [
            node.tag for node in children
            if '<name>' not in node.tag
        ]

    def get_next_branching_option(self, attribute):
        while len(self.children(attribute)) == 1:
            attribute = self.children(attribute)[0]
        return attribute
