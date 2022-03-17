import setuptools
from ipyslides.shared_vars import __version__

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ipyslides",
    version = __version__,
    author = "Abdul Saboor",
    author_email = "mass_qau@outlook.com",
    description = "Live rich content slides in jupyter notebook",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/massgh/ipyslides",
    project_urls = {
        "Bug Tracker": "https://github.com/massgh/ipyslides/issues",
    },
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    requires = ['markdown'],
    install_requires = [
          'markdown',
      ],
    packages = setuptools.find_packages(),
    keywords        = ['Jupyter', 'Widgets', 'IPython'],
    include_package_data = True,
    python_requires =">=3.6",
)