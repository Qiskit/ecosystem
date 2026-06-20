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

"""Tests for ecosystem.request.URL."""

from unittest import TestCase

from ecosystem.error_handling import EcosystemError
from ecosystem.request import URL


class TestURL(TestCase):
    """Test class for ecosystem.request.URL."""

    def test_normal_url(self):
        """Tests parsing a normal url."""
        url = URL("https://github.com/banana?key=value")
        self.assertEqual(url.hostname, "github.com")
        self.assertEqual(url.path, "/banana")
        self.assertEqual(url.query, "key=value")

    def test_no_response(self):
        """Tests parsing _No response_."""
        with self.assertRaises(EcosystemError):
            _ = URL("_No response_")

    def test_contains_url(self):
        """Tests parsing a string that contains a url"""
        url = URL(" - https://github.com/banana?key=value and somehting else")
        self.assertEqual(url.hostname, "github.com")
        self.assertEqual(url.path, "/banana")
        self.assertEqual(url.query, "key=value")

    def test_no_schema(self):
        """Tests parsing a url without a schema"""
        url = URL("github.com/banana?key=value")
        self.assertEqual(url.hostname, "github.com")
        self.assertEqual(url.path, "/banana")
        self.assertEqual(url.query, "key=value")

    def test_trailing_bar(self):
        """Tests parsing a url with a trailing bar"""
        url = URL("github.com/banana/")
        self.assertEqual(url.hostname, "github.com")
        self.assertEqual(url.path, "/banana")

    def test_hostname_case(self):
        """Tests parsing a url with casing in the hostname"""
        url = URL("GitHub.com/banana?key=value")
        self.assertEqual(url.hostname, "github.com")
        self.assertEqual(url.path, "/banana")
        self.assertEqual(url.query, "key=value")
