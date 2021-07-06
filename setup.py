from setuptools import setup


setup(
    name='nixui',
    version='0.1.0',
    description='',
    author='Andrew Lapp',
    author_email='andrew@nixgui.rew.la',
    url='',
    packages=['nixui', 'nixui.parser'],
    package_data={'nixui': [
        'icons/*',
        'tests/sample/*'
    ]},
    include_package_data=True,
    entry_points={
        'console_scripts': ['nix-gui=nixui.gui:main'],
    }
)
