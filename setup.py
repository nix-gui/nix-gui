from setuptools import setup


setup(
    name='nixui',
    version='0.1.0',
    description='',
    author='Andrew Lapp',
    author_email='andrew@nixgui.rew.la',
    url='',
    packages=['nixui', 'nixui.parser'],
    entry_points={
        'console_scripts': ['nix-gui=nixui.gui:main'],
    }
)
