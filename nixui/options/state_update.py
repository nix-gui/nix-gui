import abc
import dataclasses

from treelib import Tree

from nixui.options import attribute, option_definition


class Update(abc.ABC):
    def revert(self, option_tree):
        raise NotImplementedError

    def merge_with_previous_update(self, previous_update):
        return None


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class ChangeDefinitionUpdate(Update):
    option: attribute.Attribute
    old_definition: option_definition.OptionDefinition
    new_definition: option_definition.OptionDefinition

    def revert(self, option_tree):
        option_tree.set_definition(self.option, self.old_definition)

    def merge_with_previous_update(self, previous_update):
        if previous_update.option != self.option:
            return None
        return ChangeDefinitionUpdate(
            option=self.option,
            old_definition=previous_update.old_definition,
            new_definition=self.new_definition
        )


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class CreateUpdate(Update):
    attribute: attribute.Attribute
    definition: option_definition.OptionDefinition = option_definition.OptionDefinition.undefined()

    def revert(self, option_tree):
        option_tree.remove_attribute(self.attribute)


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class RenameUpdate(Update):
    old_attribute: attribute.Attribute
    new_attribute: attribute.Attribute

    def revert(self, option_tree):
        option_tree.rename_attribute(self.new_attribute, self.old_attribute)


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class RemoveUpdate(Update):
    attribute: attribute.Attribute
    deleted_subtree: Tree

    def revert(self, option_tree):
        parent_nid = self.attribute[:-1]
        option_tree.tree.paste(parent_nid, self.deleted_subtree)
