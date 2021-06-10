from distutils.core import setup


setup(
    name='nixui',
    version='0.1.0',
    description='',
    author='Andrew Lapp',
    author_email='andrew@nixgui.rew.la',
    url='',
    packages=['nixui'],
    entry_points={
        'console_scripts': ['nix-gui=nixui.lang:get_language_server_client'],
    }
)
