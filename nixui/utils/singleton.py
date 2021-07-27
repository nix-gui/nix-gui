class Singleton:
    def __eq__(self, other):
        return isinstance(other, self.__class__)
