# This code is part of Qiskit.
#
# (C) Copyright IBM 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at https://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""License class for name normalization to SPDX ids."""


class License:
    """
    The License class to compute equivalencies
    """

    spdx_ids = {
        "Apache 2.0": "Apache-2.0",
        "Apache License 2.0": "Apache-2.0",
        "Apache-2.0": "Apache-2.0",
        "Apache Software License@pypi": "Apache-1.1",
        "MIT license": "MIT",
        "MIT License": "MIT",
        "MIT": "MIT",
        'BSD 3-Clause "New" or "Revised" License': "BSD-3-Clause",
        "BSD (3-clause)": "BSD-3-Clause",
        'BSD 2-Clause "Simplified" license': "BSD-2-Clause",
        'BSD 2-Clause "Simplified" License': "BSD-2-Clause",
        "GNU General Public License v3.0": "GPL-3.0",
        "GNU Lesser General Public License v2.1": "LGPL-2.1",
        "GNU Lesser General Public License v3.0": "LGPL-3.0",
    }

    def __init__(self, license_name: str, where: str = None):
        if "@" in license_name:
            license_name, where = license_name.split("@")
        self.license_name = license_name
        self.where = where

    @property
    def spdx_id(self):
        """if available, returns the SPDX id, otherwise, the given name at creation time"""
        if self.license_name in self.spdx_ids:
            return self.spdx_ids[self.license_name]
        if f"{self.license_name}@{self.where}" in self.spdx_ids:
            return self.spdx_ids[f"{self.license_name}@{self.where}"]
        if self.license_name in self.spdx_ids.values():
            return self.license_name
        return None

    def is_osi_approved(self):
        """Check if the license is OSI approved"""
        if self.license_name.lower() == "other":
            return None
        if self.license_name in self.spdx_ids.values():
            return True
        return False

    def __str__(self):
        if self.spdx_id:
            return self.spdx_id
        return self.license_name

    def __repr__(self):
        if self.spdx_id:
            return self.spdx_id
        return f"{self.license_name}@{self.where}"

    def __eq__(self, other):
        return repr(self) == repr(other)
