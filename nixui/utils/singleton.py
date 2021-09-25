import dataclasses


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class Singleton:
    name: str

    def __eq__(self, other):
        return (
            type(other) == type(self) and
            self.name == other.name
        )

    def __repr__(self):
        return f'Singleton("{self.name}")'
