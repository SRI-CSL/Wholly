from setuptools import setup, find_packages
import os
import glob

from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
# with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
#     long_description = f.read()

# use the in house version number so we stay in synch with ourselves.
from wholly.version import wholly_version

setup(
    name='wholly',
    version=wholly_version,
    description='Wholly',
    long_description='Wholly provides a Python tool that can build clean packages in a traceable way from open-source code. We make use of Docker containers to provide a minimal and controlled build environment, clear and meaningful build "recipes" to describe precisely the dependencies and the build invocations, and fine-grained sub-packaging to release lightweight and usable images.',
    url='https://github.com/SRI-CSL/Wholly',
    author='Loic Gelle, Hassen Saidi, Ian A. Mason.',
    author_email='iam@csl.sri.com',


    include_package_data=True,

    packages=find_packages(),

    entry_points = {
        'console_scripts': [
            'wholly = wholly.wholly:main',
        ],
    },

    license='MIT',

    install_requires=[
        "pyyaml >= 3.12"
    ],

    classifiers=[
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Compilers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Operating System :: MacOS',
        'Operating System :: POSIX :: Linux',
        'Operating System :: POSIX :: BSD',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],
)
