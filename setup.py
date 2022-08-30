from setuptools import setup
from distutils.util import convert_path


# get __version__ before building https://stackoverflow.com/a/24517154
main_ns = {}
ver_path = convert_path('nixui/version.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)


setup(
    name='nixui',
    version=main_ns['__version__'],
    description='',
    author='Andrew Lapp',
    author_email='andrew@nixgui.rew.la',
    url='',
    packages=[
        'nixui',
        'nixui.options',
        'nixui.graphics',
        'nixui.icons',
        'nixui.utils',
        'nixui.nix',
        'nixui.tests.sample',
        'scrape_github',
    ],
    package_data={
        'nixui': [
            'icons/*',
            'tests/sample/*'
        ],
        'nixui.nix': [
            '*.nix'
        ]
    },
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'nix-gui=nixui.main:main',
            'scrape-github=scrape_github.main:main'
        ],
    }
)
