import abc
import dataclasses
import uuid

from treelib import Tree

from nixui.options import option_definition
from nixui.options.attribute import Attribute


class Update(abc.ABC):
    def revert(self, option_tree):
        """
        Function applied to option_tree to revert the update
        """
        raise NotImplementedError

    def merge_with_previous_update(self, previous_update):
        """
        In some cases updates can merged with the previous update.
        If merging is possible, return an Update reflecting the merging of the two updates
        If merging is not possible, return None
        """
        return None

    def details_string(self):
        """
        String description of update for logging and status bar
        """
        raise NotImplementedError

    def reversion_impacted_attribute(self):
        """
        Used to determine which attribute to display when Undo is performed.

        """
        raise NotImplementedError


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class ChangeDefinitionUpdate(Update):
    attribute: Attribute  # TODO: https://github.com/nix-gui/nix-gui/issues/75
    old_definition: option_definition.OptionDefinition
    new_definition: option_definition.OptionDefinition

    def revert(self, option_tree):
        option_tree.set_definition(self.attribute, self.old_definition)

    def merge_with_previous_update(self, previous_update):
        if isinstance(previous_update, (CreateUpdate, ChangeDefinitionUpdate)):
            return None
        elif previous_update.attribute != self.attribute:
            return None
        return ChangeDefinitionUpdate(
            attribute=self.attribute,
            old_definition=previous_update.old_definition,
            new_definition=self.new_definition
        )

    def details_string(self):
        return f'Changed {self.attribute} from {self.old_definition} -> {self.new_definition}'

    def reversion_impacted_attribute(self):
        return self.attribute


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class CreateUpdate(Update):
    attribute: Attribute
    definition: option_definition.OptionDefinition = option_definition.OptionDefinition.undefined()

    def revert(self, option_tree):
        option_tree.remove_attribute(self.attribute)

    def details_string(self):
        return f'Created {self.attribute}'

    def reversion_impacted_attribute(self):
        return self.attribute[:-1]


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class RenameUpdate(Update):
    old_attribute: Attribute
    new_attribute: Attribute

    def revert(self, option_tree):
        option_tree.rename_attribute(self.new_attribute, self.old_attribute)

    def merge_with_previous_update(self, previous_update):
        if isinstance(previous_update, CreateUpdate) and previous_update.attribute == self.old_attribute:
            return CreateUpdate(
                attribute=self.new_attribute,
                definition=previous_update.definition
            )

    def details_string(self):
        return f'Renamed attribute {self.old_attribute} to {self.new_attribute}'

    def reversion_impacted_attribute(self):
        return self.old_attribute


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class SwapNamesUpdate(Update):
    attribute0: Attribute
    attribute1: Attribute

    def revert(self, option_tree):
        placeholder = str(uuid.uuid4())
        option_tree.rename_attribute(self.attribute0, placeholder)
        option_tree.rename_attribute(self.attribute1, self.attribute0)
        option_tree.rename_attribute(placeholder, self.attribute1)

    def details_string(self):
        return f'Swapped attributes {self.attribute0} and {self.attribute0}'

    def reversion_impacted_attribute(self):
        return self.attribute0


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class RemoveUpdate(Update):
    attribute: Attribute
    deleted_subtree: Tree
    old_in_memory_definitions: dict

    def revert(self, option_tree):
        parent_nid = self.attribute[:-1]
        option_tree.tree.paste(parent_nid, self.deleted_subtree)
        option_tree.in_memory_diff.update(self.old_in_memory_definitions)

    def details_string(self):
        return f'Removed attribute {self.attribute}'

    def reversion_impacted_attribute(self):
        return self.attribute
