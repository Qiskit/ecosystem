# This code is part of Qiskit.
#
# (C) Copyright IBM 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at https://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Setup file for ecosystem."""

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt") as fp:
    install_requires = fp.read()

setuptools.setup(
    name="ecosystem",
    description="Ecosystem",
    entry_points={
        "console_scripts": ["ecosystem=ecosystem:main"],
    },
    long_description=long_description,
    packages=setuptools.find_packages(),
    package_data={"ecosystem": ["html_templates/*.jinja"]},
    install_requires=install_requires,
    python_requires=">=3.13",
)
