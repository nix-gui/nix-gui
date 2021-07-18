import csv
from dataclasses import dataclass, field
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

    def __iter__(self):
        return iter(self.loc)

    def __str__(self):
        return '.'.join([
            f'"{attribute}"' if '.' in attribute else attribute
            for attribute in self.loc
        ])

    def __bool__(self):
        return self.loc

    def __repr__(self):
        return f'{self.__class__}("{str(self)}")'

    def __hash__(self):
        return hash(tuple(self.loc))
