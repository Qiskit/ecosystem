"""Setup file for demo-impl."""

import setuptools

with open("requirements.txt") as fp:
    install_requires = fp.read()

setuptools.setup(
    name="demo-impl",
    description="demo-impl",
    long_description="",
    packages=setuptools.find_packages(),
    install_requires=install_requires,
    python_requires=">=3.6",
)
