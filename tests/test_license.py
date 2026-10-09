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

"""Tests for ecosystem.request.License."""

# pylint: disable=redefined-builtin

from unittest import TestCase

from ecosystem.license import License


class TestLicense(TestCase):
    """Test class for ecosystem.license.License class."""

    def test_without_where(self):
        """A license string without a source should leave `where` unset."""
        license = License("AnyLicense")
        self.assertEqual(license.license_name, "AnyLicense")
        self.assertIsNone(license.where)

    def test_with_where(self):
        """A license string with an at should split name and `where`."""
        license = License("AnyLicense@anyplace")
        self.assertEqual(license.license_name, "AnyLicense")
        self.assertEqual(license.where, "anyplace")

    def test_spdx_id_without_where(self):
        """A known license name should resolve to its SPDX identifier."""
        license = License("Apache 2.0")
        self.assertEqual(license.spdx_id, "Apache-2.0")

    def test_spdx_id_with_where(self):
        """License normalization should consider the source when resolving SPDX."""
        license = License("Apache Software License@pypi")
        self.assertEqual(license.spdx_id, "Apache-2.0")

    def test_the_generic_apache_classifier_is_read_as_version_2(self):
        """`License :: OSI Approved :: Apache Software License` carries no version.

        It used to resolve to Apache-1.1, which is what OSI called version 1.1 in 2000, and
        it misreported 20 distributions including Qiskit's own addons.
        """
        self.assertEqual("Apache-2.0", str(License("Apache Software License", "pypi")))
        self.assertTrue(License("Apache Software License", "pypi").is_osi_approved())

    def test_a_spelled_out_apache_2_is_normalized(self):
        """It used to pass through unmapped, so it read as not OSI-approved"""
        license = License("Apache License, Version 2.0")
        self.assertEqual("Apache-2.0", str(license))
        self.assertTrue(license.is_osi_approved())

    def test_a_license_text_names_its_own_version(self):
        """What `license = { file = "LICENSE" }` publishes: the whole file"""
        self.assertEqual(
            "Apache-2.0",
            str(
                License.from_text(
                    "                                 Apache License\n"
                    "                           Version 2.0, January 2004\n"
                    "                        http://www.apache.org/licenses/\n"
                )
            ),
        )

    def test_a_text_that_names_no_version_resolves_to_nothing(self):
        """Better than a wrong version: the classifier is tried next"""
        self.assertIsNone(
            License.from_text("Permission is hereby granted, free of charge")
        )
        self.assertIsNone(License.from_text(""))
        self.assertIsNone(License.from_text(None))

    def test_spdx_id_with_spdxid(self):
        """An SPDX-formatted license name should be preserved."""
        license = License("Apache-2.0")
        self.assertEqual(license.spdx_id, "Apache-2.0")

    def test_is_osi_approved_other(self):
        """A generic placeholder license should yield an indeterminate OSI result."""
        license = License("Other")
        self.assertIsNone(license.is_osi_approved())

    def test_is_osi_approved_true(self):
        """A recognized OSI-approved license should return True."""
        license = License("Apache Software License@pypi")
        self.assertTrue(license.is_osi_approved())

    def test_is_osi_approved_false(self):
        """An unrecognized license should return False for OSI approval."""
        license = License("BananaLicense")
        self.assertFalse(license.is_osi_approved())

    def test_repr_apache2(self):
        """`repr` should use the normalized SPDX form when available."""
        license = License("Apache 2.0")
        self.assertEqual(repr(license), "Apache-2.0")

    def test_repr_spdxid(self):
        """`repr` should preserve an already-normalized SPDX identifier."""
        license = License("Apache-2.0")
        self.assertEqual(repr(license), "Apache-2.0")

    def test_repr_not_valid_license(self):
        """`repr` should fall back to the original license text when unknown."""
        license = License("Banana License")
        self.assertEqual(repr(license), "Banana License")

    def test_repr_anyother(self):
        """`repr` should include the source suffix when present."""
        license = License("Banana License", "bananaland")
        self.assertEqual(repr(license), "Banana License@bananaland")

    def test_eq(self):
        """Equivalent license spellings should compare equal."""
        license1 = License("BSD (3-clause)")
        license2 = License('BSD 3-Clause "New" or "Revised" License')
        self.assertEqual(license1, license2)

    def test_neq(self):
        """Different sources should prevent licenses from comparing equal."""
        license1 = License("Apache Software License", where="pypi")
        license2 = License('BSD 3-Clause "New" or "Revised" License')
        self.assertNotEqual(license1, license2)
