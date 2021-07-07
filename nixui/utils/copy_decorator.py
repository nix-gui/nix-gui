import copy


def return_copy(wrapped):
    def fn(*args, **kwargs):
        return copy.copy(wrapped(*args, **kwargs))
    return fn
