import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ipyslides",
    version="0.0.1",
    author="Abdul Saboor",
    author_email="mass_qau@outlook.com",
    description="Live rich content slides in jupyter notebook",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/massgh/ipyslides",
    project_urls={
        "Bug Tracker": "https://github.com/massgh/ipyslides/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "ipyslides"},
    packages=setuptools.find_packages(where="ipyslides"),
    python_requires=">=3.6",
)