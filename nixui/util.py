from functools import wraps

class Default(object):
    def __init__(self, name):
        super(Default, self).__init__()

        self.name = name


my_defaults = dict(USER_INPUT=0)


def set_defaults(defaults):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Backup original function defaults.
            original_defaults = f.func_defaults

            # Replace every `Default("...")` argument with its current value.
            function_defaults = []
            for default_value in f.func_defaults:
                if isinstance(default_value, Default):
                    function_defaults.append(defaults[default_value.name])
                else:
                    function_defaults.append(default_value)

            # Set the new function defaults.
            f.func_defaults = tuple(function_defaults)

            return_value = f(*args, **kwargs)

            # Restore original defaults (required to keep this trick working.)
            f.func_defaults = original_defaults

            return return_value

        return wrapper

    return decorator



@set_defaults(my_defaults)
def DoSomething(var_of_data, user_input=Default("USER_INPUT")):
    return var_of_data, user_input


def main():
    print DoSomething("This")

    my_defaults["USER_INPUT"] = 1

    print DoSomething("Thing")

    my_defaults["USER_INPUT"] = 2

    print DoSomething("Actually")
    print DoSomething("Works", 3)


if __name__ == "__main__":
    main()
