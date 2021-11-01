import csv
from dataclasses import dataclass, field
import re
from typing import List


@dataclass(frozen=True)
class Attribute:
    loc: List[str] = field(default_factory=list)

    @classmethod
    def from_string(cls, attribute_string):
        loc = next(csv.reader([attribute_string], delimiter='.', quotechar='"'))
        return cls(loc)

    @classmethod
    def from_insertion(cls, attribute_set, attribute):
        return cls(attribute_set.loc + [attribute])

    def get_set(self):
        return Attribute(self.loc[:-1])

    def get_end(self):
        return self.loc[-1]

    def startswith(self, attribute_set):
        if len(attribute_set) > len(self):
            return False
        for i, key in enumerate(attribute_set):
            if self[i] != key:
                return False
        return True

    def __bool__(self):
        return bool(self.loc)

    def __getitem__(self, subscript):
        if isinstance(subscript, slice):
            return Attribute(self.loc[subscript])
        else:
            return self.loc[subscript]

    def __iter__(self):
        return iter(self.loc)

    def __len__(self):
        return len(self.loc)

    def __lt__(self, other):
        # defined such that iterating over sorted attributes is a bredth first search
        return (-len(self), str(self)) < (-len(other), str(other))

    def __str__(self):
        """
        regexp based on
        https://github.com/NixOS/nix/blob/99f8fc995b2f080cc0a6fe934c8d9c777edc3751/src/libexpr/lexer.l#L97
        https://github.com/NixOS/nixpkgs/blob/8da27ef161e8bd0403c8f9ae030ef1e91cb6c475/pkgs/tools/nix/nixos-option/libnix-copy-paste.cc#L52
        """
        return '.'.join([
            attribute
            if re.match(r'^[a-zA-Z\_][a-zA-Z0-9\_\'\-]*$', attribute)
            else f'"{attribute}"'
            for attribute in self.loc
        ])

    def __repr__(self):
        return f"Attribute('{str(self)}')"

    def __hash__(self):
        return hash(tuple(self.loc))
