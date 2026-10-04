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

"""Tests for ecosystem/crates.py"""

from datetime import date
from unittest import TestCase
from unittest.mock import patch

from tests.common import named, names
from ecosystem.crates import CratesData, HEADERS
from ecosystem.error_handling import EcosystemError
from ecosystem.license import License
from ecosystem.member import Member
from ecosystem.request import URL

# the shape of https://crates.io/api/v1/crates/<name>, cut down to the keys that are read
CRATES_JSON = {
    "crate": {
        "name": "banana_parser",
        "description": "Parses bananas",
        "max_version": "0.8.0-rc1",
        "max_stable_version": "0.7.0",
        "newest_version": "0.8.0-rc1",
        "downloads": 939802,
        "recent_downloads": 166899,
        "repository": "https://github.com/banana-org/banana-repo",
    },
    "versions": [
        {
            "num": "0.8.0-rc1",
            "created_at": "2026-02-02T04:23:53.715054Z",
            "license": "MIT",
            "rust_version": "1.80",
            "edition": "2024",
        },
        {
            "num": "0.7.0",
            "created_at": "2024-10-30T04:23:53.715054Z",
            "license": "Apache-2.0",
            "rust_version": "1.70",
            "edition": "2021",
        },
    ],
}

OWNERS_JSON = {
    "users": [
        {"login": "banana", "kind": "user", "url": "https://github.com/banana"},
        {"login": "github:banana-org:crates", "kind": "team", "url": None},
    ]
}


class CratesTestCase(TestCase):
    """Base with the two crates.io responses stubbed out"""

    @staticmethod
    def fetched(crates_json=None, owners_json=None):
        """A CratesData as if `update_json` had read those responses"""
        crates_data = CratesData(package_name="banana_parser")
        with patch(
            "ecosystem.crates.request_json",
            side_effect=[
                crates_json if crates_json is not None else CRATES_JSON,
                owners_json if owners_json is not None else OWNERS_JSON,
            ],
        ):
            crates_data.update_json()
        return crates_data


class TestCratesDataFromUrl(CratesTestCase):
    """Which URLs name a crate, which is what a submission is read with"""

    def test_a_crate_page_is_a_section(self):
        """The only crates.io URL a submission is expected to carry"""
        crates_data = CratesData.from_url(URL("https://crates.io/crates/banana_parser"))
        self.assertEqual("banana_parser", crates_data.package_name)

    def test_a_trailing_slash_is_not_a_second_path_part(self):
        """Both spellings of the same page"""
        self.assertEqual(
            "banana_parser",
            CratesData.from_url(
                URL("https://crates.io/crates/banana_parser/")
            ).package_name,
        )

    def test_another_registry_is_not_ours_to_read(self):
        """`upsert_sections` tries every section on every URL, so None means "not mine" """
        self.assertIsNone(CratesData.from_url(URL("https://pypi.org/project/banana/")))

    def test_a_crates_io_url_that_is_not_a_crate_is_an_error(self):
        """Silently dropping it would lose whatever the submission meant by it"""
        with self.assertRaises(EcosystemError):
            CratesData.from_url(URL("https://crates.io/categories/science"))


class TestCratesDataFetched(CratesTestCase):
    """What the section says after reading crates.io"""

    def test_the_section_is_what_the_registry_says(self):
        """Every stored key, from the two responses"""
        self.assertEqual(
            {
                "package_name": "banana_parser",
                "version": "0.7.0",
                "last_release_date": date(2024, 10, 30),
                "license": "Apache-2.0",
                "description": "Parses bananas",
                "url": "https://crates.io/crates/banana_parser",
                "maintainers": ["https://github.com/banana"],
                "rust_version": "1.70",
                "edition": "2021",
                "total_downloads": 939802,
                "last_90_days_downloads": 166899,
            },
            self.fetched().to_dict(),
        )

    def test_the_release_read_is_the_newest_stable_one(self):
        """A release candidate is published but is not what a user installs"""
        crates_data = self.fetched()
        self.assertEqual("0.7.0", crates_data.version)
        self.assertEqual("1.70", crates_data.rust_version)
        self.assertEqual(date(2024, 10, 30), crates_data.last_release_date)

    def test_a_crate_with_no_stable_release_reports_no_release(self):
        """`max_stable_version` is null until the first non-prerelease"""
        payload = {
            "crate": dict(CRATES_JSON["crate"], max_stable_version=None),
            "versions": CRATES_JSON["versions"],
        }
        crates_data = self.fetched(crates_json=payload)
        self.assertIsNone(crates_data.version)
        self.assertIsNone(crates_data.last_release_date)
        self.assertIsNone(crates_data.rust_version)

    def test_an_owner_with_no_url_is_left_out(self):
        """A team is as much an owner as a person, but only if it can be linked"""
        self.assertEqual(["https://github.com/banana"], self.fetched().maintainers)

    def test_a_field_the_payload_does_not_carry_falls_back(self):
        """A fetch that answers less than it used to does not empty the section"""
        crates_data = CratesData(package_name="banana_parser", rust_version="1.70")
        payload = {"crate": dict(CRATES_JSON["crate"]), "versions": [{"num": "0.7.0"}]}
        with patch("ecosystem.crates.request_json", side_effect=[payload, OWNERS_JSON]):
            crates_data.update_json()
        self.assertEqual("1.70", crates_data.rust_version)

    def test_an_unknown_attribute_of_a_fetched_section_is_an_error(self):
        """The payload is not a free-form namespace to read fields off"""
        with self.assertRaises(AttributeError):
            _ = self.fetched().bananas

    def test_the_section_prints_as_what_it_stores(self):
        """`repr` is what the update log shows for it"""
        self.assertIn("banana_parser", repr(self.fetched()))

    def test_an_unreachable_crate_keeps_the_stored_values(self):
        """A yanked crate, or a bad name: the section is still what it was"""
        crates_data = CratesData(package_name="banana_parser", version="0.7.0")
        with patch("ecosystem.crates.request_json", side_effect=EcosystemError("404")):
            crates_data.update_json()
        self.assertEqual("0.7.0", crates_data.version)

    def test_both_requests_carry_a_user_agent(self):
        """crates.io answers 403 without one, and `request_json` sends it to GitHub only"""
        crates_data = CratesData(package_name="banana_parser")
        with patch(
            "ecosystem.crates.request_json",
            side_effect=[CRATES_JSON, OWNERS_JSON],
        ) as request:
            crates_data.update_json()
        self.assertEqual(
            [
                "https://crates.io/api/v1/crates/banana_parser",
                "https://crates.io/api/v1/crates/banana_parser/owners",
            ],
            [call.args[0] for call in request.call_args_list],
        )
        for call in request.call_args_list:
            self.assertEqual(HEADERS, call.kwargs["headers"])
        self.assertIn("User-Agent", HEADERS)


class TestCratesDataStored(CratesTestCase):
    """What a member file carries, read back without the network"""

    @staticmethod
    def stored(**section):
        """A CratesData as `from_dict` builds one out of a member file"""
        return CratesData.from_dict({"package_name": "banana_parser"} | section)

    def test_the_license_comes_back_as_the_license_class(self):
        """Which is what knows `Apache-2.0` and `Apache 2.0` are the same thing"""
        self.assertIsInstance(self.stored(license="Apache-2.0").license, License)

    def test_stored_values_are_returned_unfetched(self):
        """Reading a member file must not reach crates.io"""
        crates_data = self.stored(
            version="0.7.0",
            last_release_date="2024-10-30",
            license="Apache-2.0",
            total_downloads=939802,
        )
        self.assertEqual("0.7.0", crates_data.version)
        self.assertEqual("Apache-2.0", str(crates_data.license))
        self.assertEqual(939802, crates_data.total_downloads)

    def test_the_url_is_a_function_of_the_name(self):
        """So a section does not have to store it to be able to link the crate"""
        self.assertEqual("https://crates.io/crates/banana_parser", self.stored().url)

    def test_a_key_that_is_not_stored_reads_as_nothing(self):
        """Most sections are missing an MSRV, which is not an error"""
        self.assertIsNone(self.stored().rust_version)
        self.assertIsNone(self.stored().description)
        self.assertIsNone(self.stored().license)

    def test_a_license_given_as_a_string_is_wrapped(self):
        """A section built in code, rather than read back through `from_dict`"""
        crates_data = CratesData(package_name="banana_parser", license="Apache-2.0")
        self.assertIsInstance(crates_data.license, License)

    def test_an_unknown_attribute_is_still_an_error(self):
        """`to_dict` asks for every key, so the fallback cannot swallow typos"""
        with self.assertRaises(AttributeError):
            _ = self.stored().bananas

    def test_a_license_object_is_kept_as_it_is(self):
        """`from_dict` has already wrapped it, and wrapping it twice would nest it"""
        crates_data = CratesData(
            package_name="banana_parser", license=License("Apache-2.0", "crates")
        )
        self.assertEqual("Apache-2.0", str(crates_data.license))

    def test_the_round_trip_through_from_dict(self):
        """What is written is what is read back"""
        section = self.fetched().to_dict()
        self.assertEqual(
            section,
            CratesData.from_dict(dict(section)).to_dict(),
        )


class TestCratesOnTheMember(CratesTestCase):
    """How a member gets the section, and how it refreshes it"""

    @staticmethod
    def member(**kwargs):
        """A member with a crates.io URL among its packages"""
        return Member(
            name="Banana Parser",
            url="https://github.com/banana-org/banana-repo",
            uuid="banana00-0000-0000-0000-000000000000",
            **kwargs,
        )

    def test_a_submitted_url_becomes_a_section(self):
        """And the URL stays, so a later run reads the same declaration"""
        member = self.member(
            packages=[URL("https://crates.io/crates/banana_parser")],
        )
        member.upsert_sections()
        self.assertEqual(["banana_parser"], names(member.crates))
        # the declaration stays: it is what the project said, and the section is what was
        # read from it
        self.assertEqual(
            ["https://crates.io/crates/banana_parser"],
            [str(url) for url in member.packages],
        )

    def test_update_crates_refreshes_every_section(self):
        """The weekly run calls it for every member that has one"""
        member = self.member(crates=[CratesData("banana_parser")])
        with patch(
            "ecosystem.crates.request_json", side_effect=[CRATES_JSON, OWNERS_JSON]
        ):
            member.update_crates()
        self.assertEqual("0.7.0", named(member.crates, "banana_parser").version)

    def test_the_sections_round_trip_through_from_dict(self):
        """A member file is read back into the same sections it was written from"""
        member = self.member(crates=[self.fetched()])
        read_back = Member.from_dict(member.to_dict())
        self.assertEqual(
            named(member.crates, "banana_parser").to_dict(),
            named(read_back.crates, "banana_parser").to_dict(),
        )
