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
        return Attribute(self.loc[-1:])

    def __bool__(self):
        return bool(self.loc)

    def __iter__(self):
        return iter(self.loc)

    def __len__(self):
        return len(self.loc)

    def __lt__(self, other):
        # defined such that iterating over sorted attributes is a bredth first search
        return (-len(self), str(self)) < (-len(other), str(other))

    def __str__(self):
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
