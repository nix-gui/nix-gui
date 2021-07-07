import os


def get_store_path():
    if 'XDG_CONFIG_HOME' in os.environ:
        config_home = os.environ['XDG_CONFIG_HOME']
    else:
        config_home = os.path.join(
            os.getenv("HOME"),
            '.config'
        )
    return os.path.join(
        config_home,
        'nixgui'
    )
