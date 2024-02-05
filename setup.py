"""Setup file for ecosystem."""

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as fp:
    install_requires = fp.read()

setuptools.setup(
    name="ecosystem",
    description="Ecosystem",
    entry_points = {
        'console_scripts': ['ecosystem=ecosystem:main'],
    },
    long_description=long_description,
    packages=setuptools.find_packages(),
    package_data={"ecosystem": ["html_templates/*.jinja"]},
    install_requires=install_requires,
    python_requires='>=3.6'
)
