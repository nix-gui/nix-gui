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
        return ListOf()
    elif nix_type_str.startswith('list of') and nix_type_str.endswith('s'):
        return ListOf(
            from_nix_type_str(nix_type_str.removeprefix('list of ').removesuffix('s'))
        )
    elif nix_type_str.startswith('attribute set of'):
        return AttrsOf(
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
                if isinstance(left, Either):
                    if isinstance(right, Either):
                        return Either(left.subtypes + right.subtypes)
                    else:
                        return Either(left.subtypes + [right])
                elif isinstance(right, Either):
                    return Either([left] + right.subtypes)
                else:
                    return Either([left, right])
        else:
            return from_nix_type_str(nix_type_str, or_legal=False)
    elif nix_type_str.startswith('function that evaluates to a(n) '):
        return Function(
            from_nix_type_str(nix_type_str.removeprefix('function that evaluates to a(n) '))
        )

    # simple types with criteria
    elif nix_type_str.startswith('lazy attribute set of'):
        return AttrsOf(
            from_nix_type_str(nix_type_str.removeprefix('lazy attribute set of ')),
            lazy=True
        )
    elif nix_type_str.startswith('non-empty list of') and nix_type_str.endswith('s'):
        return ListOf(
            from_nix_type_str(nix_type_str.removeprefix('non-empty list of ').removesuffix('s')),
            minimum=1,
        )
    elif nix_type_str.startswith('pair of'):
        return ListOf(
            from_nix_type_str(nix_type_str.removeprefix('pair of ')),
            minimum=2,
            maximum=2,
        )
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
    elif nix_type_str == 'positive integer, meaning >0':
        return Int(minimum=1)
    elif nix_type_str.startswith('integer between') and nix_type_str.endswith('(both inclusive)'):
        s = nix_type_str.removeprefix('integer between ').removesuffix(' (both inclusive)')
        minimum, maximum = s.split(' and ')
        return Int(minimum=int(minimum), maximum=int(maximum))
    elif nix_type_str.startswith('one of'):
        s = nix_type_str.removeprefix('one of ')
        return OneOf([x.strip('"') for x in s.split(', ')])
    elif nix_type_str == '16 bit unsigned integer; between 0 and 65535 (both inclusive)':
        return Int(minimum=0, maximum=65535)
    elif nix_type_str in ('path, not containing newlines', 'path, not containing newlines or colons'):
        return Path()  # TODO: special handling
    elif nix_type_str.startswith('a floating point number in range'):
        s = nix_type_str.removeprefix('a floating point number in range ').lstrip('[').rstrip(']')
        minimum, maximum = s.split(', ')
        return Float(minimum=float(minimum), maximum=float(maximum))  # TODO: special handling


    # simple types
    elif nix_type_str == 'lambda':
        return Function()
    elif nix_type_str == 'attribute set':
        return Attrs()
    elif nix_type_str == 'boolean':
        return Bool()
    elif nix_type_str == 'unspecified':
        return Unspecified()
    elif nix_type_str == 'string':
        return Str()
    elif nix_type_str in ('int', 'signed integer', 'integer of at least 16 bits'):
        return Int()
    elif nix_type_str in ('float', 'floating point number'):
        return Float()
    elif nix_type_str == 'path':
        return Path()
    elif nix_type_str == 'package':
        return Package()
    elif nix_type_str == 'submodule':
        return Submodule()
    elif nix_type_str == 'null':
        return Null()
    elif nix_type_str == 'anything':
        return Anything()

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
        return Anything()

    else:
        raise ValueError(nix_type_str)


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


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class Float:
    minimum: float = None
    maximum: float = None


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
class Function:
    return_type: typing.Any = None


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class ListOf:
    subtype: typing.Any = None
    minimum: int = None
    maximum: int = None


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class AttrsOf:
    subtype: typing.Any
    lazy: bool = False


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
