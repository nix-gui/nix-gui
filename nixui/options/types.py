"""
based on https://github.com/NixOS/nixpkgs/blob/master/lib/types.nix
"""

import dataclasses
import typing
import os


def from_nix_type_str(nix_type_str, or_legal=True):
    """
    TODO: eval nested types, e.g.
    nix-instantiate --eval '<nixpkgs/nixos>' --arg configuration '{}' \
    -A "options.services.zrepl.settings.type.nestedTypes.freeformType.nestedTypes.elemType.nestedTypes.right.nestedTypes.elemType.nestedTypes.elemType.nestedTypes.left"
    we also need to extract validation data, e.g. "not containing newlines or colons"
      - does nix include a regexp or expression for us to validate with?
    """

    if nix_type_str == '':
        return None

    # types "containing" other types in their definitions
    elif nix_type_str == 'listOf':
        return ListOfType()
    elif nix_type_str.startswith('list of') and nix_type_str.endswith('s'):
        return ListOfType(
            from_nix_type_str(nix_type_str.removeprefix('list of ').removesuffix('s'))
        )
    elif nix_type_str.startswith('attribute set of'):
        return AttrsOfType(
            from_nix_type_str(nix_type_str.removeprefix('attribute set of ').removesuffix('s'))
        )

    elif ' or ' in nix_type_str and or_legal:
        chunks = nix_type_str.split(' or ')
        for i in range(1, len(chunks)):
            try:
                left = from_nix_type_str(' or '.join(chunks[:i]))
                right = from_nix_type_str(' or '.join(chunks[i:]))
            except ValueError:
                continue
            else:
                if isinstance(left, EitherType):
                    if isinstance(right, EitherType):
                        return EitherType(left.subtypes + right.subtypes)
                    else:
                        return EitherType(left.subtypes + [right])
                elif isinstance(right, EitherType):
                    return EitherType([left] + right.subtypes)
                else:
                    return EitherType([left, right])
        else:
            return from_nix_type_str(nix_type_str, or_legal=False)
    elif nix_type_str.startswith('function that evaluates to a(n) '):
        return FunctionType(
            from_nix_type_str(nix_type_str.removeprefix('function that evaluates to a(n) '))
        )

    # simple types with criteria
    elif nix_type_str.startswith('lazy attribute set of'):
        return AttrsOfType(
            from_nix_type_str(nix_type_str.removeprefix('lazy attribute set of ')),
            lazy=True
        )
    elif nix_type_str.startswith('non-empty list of') and nix_type_str.endswith('s'):
        return ListOfType(
            from_nix_type_str(nix_type_str.removeprefix('non-empty list of ').removesuffix('s')),
            minimum=1,
        )
    elif nix_type_str.startswith('pair of'):
        return ListOfType(
            from_nix_type_str(nix_type_str.removeprefix('pair of ')),
            minimum=2,
            maximum=2,
        )
    elif nix_type_str.startswith('string concatenated with') or nix_type_str.startswith('strings concatenated with'):
        # TODO: fix this hack, (((list of) strings) concatenated with "foo"), not # ((list of) string concatenated with "foo"s)
        s = nix_type_str.split('concatenated with')[1]
        s = s.strip('"')
        return StrType(concatenated_with=s)
    elif nix_type_str.startswith('string (with check: '):
        check = nix_type_str.split('(with check: ')[1].removesuffix(')')
        return StrType(check=check)
    elif nix_type_str.startswith('string matching the pattern'):
        return StrType(
            legal_pattern=nix_type_str.removeprefix('string matching the pattern ')
        )
    elif nix_type_str == 'unsigned integer, meaning >=0':
        return IntType(minimum=0)
    elif nix_type_str == 'positive integer, meaning >0':
        return IntType(minimum=1)
    elif nix_type_str.startswith('integer between') and nix_type_str.endswith('(both inclusive)'):
        s = nix_type_str.removeprefix('integer between ').removesuffix(' (both inclusive)')
        minimum, maximum = s.split(' and ')
        return IntType(minimum=int(minimum), maximum=int(maximum))
    elif nix_type_str.startswith('one of'):
        s = nix_type_str.removeprefix('one of ')
        return OneOfType([x.strip('"') for x in s.split(', ')])
    elif nix_type_str == '16 bit unsigned integer; between 0 and 65535 (both inclusive)':
        return IntType(minimum=0, maximum=65535)
    elif nix_type_str in ('path, not containing newlines', 'path, not containing newlines or colons'):
        return PathType()  # TODO: special handling
    elif nix_type_str.startswith('a floating point number in range'):
        s = nix_type_str.removeprefix('a floating point number in range ').lstrip('[').rstrip(']')
        minimum, maximum = s.split(', ')
        return FloatType(minimum=float(minimum), maximum=float(maximum))  # TODO: special handling

    # simple types
    elif nix_type_str == 'lambda':
        return FunctionType()
    elif nix_type_str == 'attribute set':
        return AttrsType()
    elif nix_type_str == 'boolean':
        return BoolType()
    elif nix_type_str == 'unspecified':
        return UnspecifiedType()
    elif nix_type_str == 'string':
        return StrType()
    elif nix_type_str in ('int', 'signed integer', 'integer of at least 16 bits'):
        return IntType()
    elif nix_type_str in ('float', 'floating point number'):
        return FloatType()
    elif nix_type_str == 'path':
        return PathType()
    elif nix_type_str == 'package':
        return PackageType()
    elif nix_type_str == 'submodule':
        return SubmoduleType()
    elif nix_type_str == 'null':
        return NullType()
    elif nix_type_str == 'anything':
        return AnythingType()

    # no good handling yet
    elif (
        nix_type_str.startswith('ncdns.conf configuration type') or
        nix_type_str.startswith('libconfig configuration') or
        nix_type_str.startswith('privoxy configuration type') or
        nix_type_str in (
            'systemd option',
            'JSON value',
            'Json value',
            'YAML value',
            'Yaml value',
            'TOML value',
            'session name',
            'settings option',
            'template name',
            'printable string without spaces, # and /',
            'string of the form number{b|k|M|G}',
            'Go duration (https://golang.org/pkg/time/#ParseDuration)',
            'sysctl option value',
            'Toplevel NixOS config',
            'INI atom (null, bool, int, float or string)',
            'path convertible to it',
            'string convertible to it',
            'nixpkgs config',
            'nixpkgs overlay',
            'An evaluation of Nixpkgs; the top level attribute set of packages',
            'submodule or signed integer convertible to it',
            'submodules or list of attribute sets convertible to it',
            'submodules or list of attribute sets convertible to it',
            'davmail config type (str, int, bool or attribute set thereof)',
            'submodules or list of unspecifieds convertible to it',
            'freeciv-server params',
            'list of string or signed integer convertible to it or boolean convertible to its or string or signed integer convertible to it or boolean convertible to it convertible to it',
            'limesurvey config type (str, int, bool or attribute set thereof)',
            'Minecraft UUID',
            'LDAP value',
            'tmpfiles.d(5) age format',
            'INI atom (null, bool, int, float or string) or a non-empty list of them',
            'dataset/template options',
            'signed integer or boolean convertible to it',
            'tuple of (unsigned integer, meaning >=0 or one of "level auto", "level full-speed", "level disengage") (unsigned integer, meaning >=0) (unsigned integer, meaning >=0)',
            'Traffic Server records value'
        )
        ):
        return AnythingType()

    else:
        raise ValueError(nix_type_str)


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class UnspecifiedType:
    pass


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class AnythingType:
    pass


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class BoolType:
    pass


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class IntType:
    minimum: int = None
    maximum: int = None


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class FloatType:
    minimum: float = None
    maximum: float = None


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class StrType:
    concatenated_with: str = None
    check: str = None
    legal_pattern: str = None


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class AttrsType:
    pass


# TODO: path is broken, it's divided between being a type class and a data class
@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class PathType:
    pass


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class PackageType:
    pass


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class FunctionType:
    return_type: typing.Any = None


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class ListOfType:
    subtype: typing.Any = None
    minimum: int = None
    maximum: int = None


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class AttrsOfType:
    subtype: typing.Any
    lazy: bool = False


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class NullType:
    pass


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class SubmoduleType:
    pass


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class EitherType:
    subtypes: tuple = tuple()


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class OneOfType:
    choices: tuple = tuple()
