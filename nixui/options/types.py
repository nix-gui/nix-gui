"""
based on https://github.com/NixOS/nixpkgs/blob/master/lib/types.nix
"""

import dataclasses
import typing
import os


def from_nix_type_str(nix_type_str):
    # TODO: eval nested types, e.g.
    # nix-instantiate --eval '<nixpkgs/nixos>' --arg configuration '{}' -A "options.services.zrepl.settings.type.nestedTypes.freeformType.nestedTypes.elemType.nestedTypes.right.nestedTypes.elemType.nestedTypes.elemType.nestedTypes.left"
    # we also need to extract validation data, e.g. "not containing newlines or colons" - does this include a regexp for us to validate with?
    if nix_type_str.startswith('list of'):
        return ListOf(
            from_nix_type_str(nix_type_str.removeprefix('list of ').removesuffix('s'))
        )
    elif nix_type_str.startswith('attribute set of'):
        return AttrsOf(
            from_nix_type_str(nix_type_str.removeprefix('attribute set of ').removesuffix('s'))
        )

    elif ' or ' in nix_type_str:
        return Either([
            from_nix_type_str(s)
            for s in nix_type_str.split(' or ')
        ])

    # simple types with criteria
    elif nix_type_str.startswith('string concatenated with') or nix_type_str.startswith('strings concatenated with'):
        # TODO: fix this hack, (((list of) strings) concatenated with "foo"), not # ((list of) string concatenated with "foo"s)
        s = nix_type_str.split('concatenated with')[1]
        s = s.strip('"')
        return Str(concatenated_with=s)
    elif nix_type_str.startswith('string (with check: '):
        check = nix_type_str.split('(with check: ')[1].removesuffix(')')
        return Str(check=check)
    elif nix_type_str.startswith('string matching the pattern'):
        return Str(
            legal_pattern=nix_type_str.removeprefix('string matching the pattern ')
        )
    elif nix_type_str == 'unsigned integer, meaning >=0':
        return Int(minimum=0)
    elif nix_type_str.startswith('one of'):
        s = nix_type_str.removeprefix('one of ')
        return OneOf([x.strip('"') for x in s.split(', ')])
    elif nix_type_str == '16 bit unsigned integer; between 0 and 65535 (both inclusive)':
        return Int(minimum=0, maximum=65535)
    elif nix_type_str in ('path, not containing newlines', 'path, not containing newlines or colons'):
        return Path()  # TODO: special handling

    # simple types
    elif nix_type_str == 'anything':
        return Anything()
    elif nix_type_str == 'attribute set':
        return Attrs()
    elif nix_type_str == 'boolean':
        return Bool()
    elif nix_type_str == 'unspecified':
        return Unspecified()
    elif nix_type_str == 'string':
        return Str()
    elif nix_type_str in ('int', 'signed integer'):
        return Int()
    elif nix_type_str == 'float':
        return Float()
    elif nix_type_str == 'path':
        return Path()
    elif nix_type_str == 'package':
        return Package()
    elif nix_type_str == 'submodule':
        return Submodule()
    elif nix_type_str == 'null':
        return Null()
    else:
        raise Exception(nix_type_str)


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class Unspecified:
    pass


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class Anything:
    pass


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class Bool:
    pass


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class Int:
    minimum: int = None
    maximum: int = None


class Float:
    pass


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class Str:
    concatenated_with: str = None
    check: str = None
    legal_pattern: str = None


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class Attrs:
    pass


# TODO: path is broken, it's divided between being a type class and a data class
@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class Path:
    cwd: str = None
    path: str = None

    def eval_path(self):
        return os.path.join(self.cwd, self.path)


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class Package:
    pass


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class ListOf:
    subtype: typing.Any


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class AttrsOf:
    subtype: typing.Any


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class Null:
    pass


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class Submodule:
    pass


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class Either:
    subtypes: tuple = tuple()


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class OneOf:
    choices: tuple = tuple()
