import os, sys
from shutil import rmtree

from setuptools import setup, Command, find_packages

if sys.version_info[:2] < (3, 9):
    sys.exit("Sorry, Python < 3.9 is not supported for einteract")

# Package meta-data.
NAME = "einteract"
DESCRIPTION = (
    "An enhanced version of ipywidgets's interactive widgets."
)
URL = "https://github.com/asaboor-gh/einteract"
EMAIL = "asaboor.my@outlook.com"
AUTHOR = "Abdul Saboor"
REQUIRES_PYTHON = ">=3.9"


# What packages are required for this module to be executed?
REQUIRED = [
    "ipyslides",
]

# What packages are optional?
EXTRAS = {
    "extra": [],
}

KEYWORDS = ["Jupyter", "Widgets", "IPython", "interact", "interactive"]
PROJECT_URLS = {
    "Bug Tracker": "https://github.com/asaboor-gh/einteract/issues",
}

here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
try:
    with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
        long_description = "\n" + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

# Load the package's __version__.py module as a dictionary.
about = {}
with open(os.path.join(here, NAME, "__version__.py")) as f:
    exec(f.read(), about)


class UploadCommand(Command):
    """Support setup.py upload."""

    description = "Build and publish the package."
    user_options = []

    @staticmethod
    def status(s):
        print(f'\n\033[1;92m{s}\033[0m\n{"-" * 50}')

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            self.status("Removing previous dist …")
            rmtree(os.path.join(here, "dist"))
        except OSError:
            pass

        self.status("Building Source and Wheel (universal) distribution …")
        os.system("{0} setup.py sdist bdist_wheel --universal".format(sys.executable))

        self.status("Uploading the package to PyPI via Twine …")
        os.system("twine upload dist/*")

        yes_no = input("Upload this version to GitHub? [y/n]: ")
        if yes_no.lower() == "y":
            self.status("Pushing git tags…")
            os.system("git tag v{0}".format(about["__version__"]))
            os.system("git push --tags")

        sys.exit()


# Where the magic happens:
setup(
    name=NAME,
    version=about["__version__"],
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    # entry_points={
    #     'console_scripts': ['mycli=mymodule:cli'],
    # },
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license="MIT",
    classifiers=[
        # Trove classifiers
        # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    keywords=KEYWORDS,
    project_urls=PROJECT_URLS,
    # $ setup.py publish support.
    cmdclass={
        "upload": UploadCommand,
    },
    # for command line interface
    entry_points={
        "console_scripts": []
    },
)
