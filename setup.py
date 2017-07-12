"""The setup and build script for the neagent library."""
import codecs
import os
from setuptools import setup, find_packages

__author__ = 'Igor Nemilentsev'
__author_email__ = 'trezorg@gmail.com'
__version__ = '0.0.1'
tests_require = ['py.test']
setup_requires = ['pytest-runner']


def _read(*names, **kwargs):
    return codecs.open(
        os.path.join(os.path.dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ).read()

setup(
    name="neagent",
    version=__version__,
    author=__author__,
    author_email=__author_email__,
    description='Tracks neagent announcements by search link',
    long_description=_read('README.md'),
    license='MIT',
    url='https://github.com/trezorg/neagent.git',
    keywords='neagent',
    packages=find_packages(),
    include_package_data=True,
    install_requires=_read('requirements.txt').splitlines(),
    setup_requires=setup_requires,
    tests_require=tests_require,
    entry_points={
        'console_scripts': ['neagent=neagent.neagent:main'],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Communications',
        'Topic :: Internet',
    ],
)
