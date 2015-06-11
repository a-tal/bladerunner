"""Bladerunner's setup.py."""


import io
import re

from setuptools import setup
from setuptools.command.test import test as TestCommand


def find_version(filename):
    """Uses re to pull out the assigned value to __version__ in filename."""

    with io.open(filename, encoding="utf-8") as version_file:
        version_match = re.search(r'^__version__ = [\'"]([^\'"]*)[\'"]',
                                  version_file.read(), re.M)
    if version_match:
        return version_match.group(1)
    return "0.0-version-unknown"


def read_description(filename):
    """Reads filename and returns its contents."""

    with io.open(filename, encoding="utf-8") as opendescription:
        return opendescription.read()


class PyTest(TestCommand):
    """Shim in pytest to be able to use it with setup.py test."""

    def finalize_options(self):
        """Stolen from http://pytest.org/latest/goodpractises.html."""

        TestCommand.finalize_options(self)
        self.test_args = ["-v", "-rf", "--cov-report", "term-missing", "--cov",
                          "bladerunner", "test"]
        self.test_suite = True

    def run_tests(self):
        """Also shamelessly stolen."""

        # have to import here, outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        raise SystemExit(errno)


setup(
    name="bladerunner",
    version=find_version("bladerunner/__init__.py"),
    author="Adam Talsma",
    author_email="adam@talsma.ca",
    packages=["bladerunner"],
    install_requires=["pexpect >= 3.3", "futures"],
    entry_points={
        'console_scripts': [
            'bladerunner = bladerunner.cmdline:main',
        ]
    },
    url="https://github.com/a-tal/bladerunner",
    description="Execution of commands on hosts",
    long_description=read_description("README.rst"),
    download_url="https://github.com/a-tal/bladerunner",
    tests_require=["pytest", "pytest-cov", "mock", "tornado"],
    cmdclass={"test": PyTest},
    license="GPLv2",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Operating System :: POSIX :: Linux",
        "Topic :: System :: Clustering",
        "Topic :: System :: Systems Administration",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
    ],
)
