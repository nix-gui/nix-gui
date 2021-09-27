from setuptools import setup


setup(
    name='nixui',
    version='0.1.0',
    description='',
    author='Andrew Lapp',
    author_email='andrew@nixgui.rew.la',
    url='',
    packages=[
        'nixui',
        'nixui.options',
        'nixui.graphics',
        'nixui.utils',
        'scrape_github',
    ],
    package_data={
        'nixui': [
            'icons/*',
            'tests/sample/*',
            'nix/*.nix',
        ],
    },
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'nix-gui=nixui.main:main',
            'scrape-github=scrape_github.main:main'
        ],
    }
)
