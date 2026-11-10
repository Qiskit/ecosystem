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

"""Tests for BadgeData, in ecosystem/badge.py"""

from unittest import TestCase
from unittest.mock import patch

from ecosystem.badge import BadgeData
from ecosystem.error_handling import EcosystemError

SVG = '<svg xmlns="http://www.w3.org/2000/svg"></svg>'
UUID = "deadbeef"


class UpdateUrlTestCase(TestCase):
    """`update_url` records the short link, or creates one when there is none"""

    def update(self, badge, link=SVG):
        """Runs `update_url` with both network calls stood in for.

        `link` is what `qisk.it/e-<uuid>` answers: an SVG for a link that is there, an
        `EcosystemError` for one that is not.
        """
        side_effect = link if isinstance(link, Exception) else None
        with patch("ecosystem.badge.request_json") as request_json, patch.object(
            BadgeData, "create_link", return_value="https://qisk.it/created"
        ) as create_link:
            if side_effect:
                request_json.side_effect = side_effect
            else:
                request_json.side_effect = lambda url, parser=None, **kw: parser(link)
            badge.update_url(name="Banana", short_uuid=UUID)
        return request_json, create_link

    def test_a_stored_url_is_not_rechecked(self):
        """The daily run calls this once per member, so the request has to be skipped"""
        badge = BadgeData(url="https://qisk.it/e-stored")
        request_json, create_link = self.update(badge)
        request_json.assert_not_called()
        create_link.assert_not_called()
        self.assertEqual("https://qisk.it/e-stored", str(badge.url))

    def test_an_existing_link_is_recorded(self):
        """The 11 members backfilled in 2026-11 were all this case: link there, key not"""
        badge = BadgeData(style="flat")
        _, create_link = self.update(badge)
        self.assertEqual(f"https://qisk.it/e-{UUID}", str(badge.url))
        create_link.assert_not_called()

    def test_a_link_that_is_not_there_yet_is_created(self):
        """Which is a member just accepted, whose Bitly link no run has made"""
        badge = BadgeData(style="flat")
        _, create_link = self.update(badge, link=EcosystemError("404"))
        create_link.assert_called_once_with("Banana", UUID)
        self.assertEqual("https://qisk.it/created", str(badge.url))

    def test_something_that_is_not_a_badge_is_not_recorded(self):
        """A 200 that is not the SVG means the keyword is taken by something else"""
        badge = BadgeData(style="flat")
        _, create_link = self.update(badge, link="<html>not a badge</html>")
        create_link.assert_called_once_with("Banana", UUID)
