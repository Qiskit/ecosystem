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

"""Tests for ecosystem/requirements.py, and for the card and page that render it."""

from datetime import date
from unittest import TestCase
from unittest.mock import patch

from ecosystem.docs.card import RequirementsCard
from ecosystem.docs.project_page import ProjectPage
from ecosystem.error_handling import EcosystemError
from ecosystem.github import GitHubData
from ecosystem.member import Member
from ecosystem.pypi import PyPIData
from ecosystem.requirements import RequirementsData

OWNER = "banana-org"
REPO = "banana-notebooks"

REQUIREMENTS_TXT = """
# what the notebooks need
--index-url https://example.invalid/simple
qiskit>=1.4,<3
numpy ; python_version >= "3.10"
qiskit-aer[gpu]>=0.14
"""

NO_QISKIT_TXT = """
numpy
matplotlib
"""


def listing(*names):
    """A contents-API directory listing holding `names` as files."""
    return {"entries": [{"name": name, "type": "file"} for name in names]}


def fake_request(*names, contents=REQUIREMENTS_TXT, requested=None):
    """Serves a listing holding `names`, then the contents of any file asked for.

    `contents` is either the text every file has, or a `{name: text}` mapping, for a
    repository whose requirements files do not all say the same thing.
    """

    def request(url, **kwargs):
        if requested is not None:
            requested.append(str(url))
        if str(url).endswith("/contents/"):
            return listing(*names)
        text = (
            contents
            if isinstance(contents, str)
            else contents[str(url).rsplit("/", 1)[-1]]
        )
        return kwargs["parser"](text)

    return request


class RequirementsTestCase(TestCase):
    """Base with the Qiskit release table stubbed out."""

    def setUp(self):
        super().setUp()
        patcher = patch.object(
            RequirementsData,
            "all_qiskit_versions",
            return_value={
                "1.0.0": {"upload_at": date(2024, 2, 15)},
                "2.1.0": {"upload_at": date(2026, 6, 10)},
            },
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    @staticmethod
    def candidates(*names, requested=None):
        """The sections `candidates` finds in a repository holding `names`."""
        probe = RequirementsData(owner=OWNER, repo=REPO)
        with patch(
            "ecosystem.github_contents.request_json",
            side_effect=fake_request(*names, requested=requested),
        ):
            return probe.candidates()

    @staticmethod
    def fetched(contents=REQUIREMENTS_TXT, file="requirements.txt", requested=None):
        """A RequirementsData as if `update_json` had read `contents` from `file`."""
        data = RequirementsData(file=file, owner=OWNER, repo=REPO)
        with patch(
            "ecosystem.github_contents.request_json",
            side_effect=fake_request(file, contents=contents, requested=requested),
        ):
            data.update_json()
        return data

    @staticmethod
    def stored(**section):
        """A RequirementsData as a member file is read back: values, no network."""
        return RequirementsData(file="requirements.txt", **section)


class TestRequirementsDataScope(RequirementsTestCase):
    """Which files get a section, which is what `candidates` answers.

    The rule lives there alone, so it is the same rule for the updater, the check ups
    and the page.
    """

    def test_a_requirements_file_on_its_own_is_the_declaration(self):
        """With no manifest, the file is all the project says about Qiskit."""
        self.assertEqual(
            ["requirements.txt"],
            [section.file for section in self.candidates("requirements.txt")],
        )

    def test_every_file_that_could_be_one_is_a_candidate(self):
        """A member can declare several, so none of them is ruled out here."""
        self.assertEqual(
            ["requirements-dev.txt", "requirements.txt"],
            [
                section.file
                for section in self.candidates(
                    "requirements.txt", "README.md", "requirements-dev.txt"
                )
            ],
        )

    def test_the_names_that_count_as_a_requirements_file(self):
        """Wider than Case A's single name: see REQUIREMENTS_PATTERN for why."""
        matches = {
            "requirements.txt": True,
            "requirements-dev.txt": True,
            "requirements-qiskit.txt": True,
            "dev-requirements.txt": True,
            "REQUIREMENTS.txt": True,
            "requirements.in": False,
            "requirements": False,
            "constraints.txt": False,
            "requirements.txt.bak": False,
        }
        for name, expected in matches.items():
            with self.subTest(name=name):
                self.assertEqual(expected, bool(self.candidates(name)))

    def test_a_candidate_has_not_been_read_yet(self):
        """`candidates` costs one listing; the contents are a request per file."""
        section = self.candidates("requirements.txt")[0]
        self.assertFalse(section.fetched)
        self.assertIsNone(section.requires_qiskit)

    def test_a_manifest_means_the_manifest_is_the_declaration(self):
        """`[python.*]` describes it instead, and a pin here is usually a CI env."""
        self.assertEqual([], self.candidates("pyproject.toml", "requirements.txt"))

    def test_any_manifest_is_enough_to_stay_out(self):
        """setup.cfg and setup.py declare a distribution just as much."""
        for manifest in ["setup.cfg", "setup.py"]:
            with self.subTest(manifest=manifest):
                self.assertEqual([], self.candidates(manifest, "requirements.txt"))

    def test_no_requirements_file_is_not_an_error(self):
        """Most repositories have none; that is not a failure to report."""
        self.assertEqual([], self.candidates("README.md"))

    def test_a_directory_named_requirements_txt_is_not_the_file(self):
        """Only files are read; a `requirements.txt/` directory is not one."""
        probe = RequirementsData(owner=OWNER, repo=REPO)
        with patch(
            "ecosystem.github_contents.request_json",
            return_value={"entries": [{"name": "requirements.txt", "type": "dir"}]},
        ):
            self.assertEqual([], probe.candidates())

    def test_one_listing_then_one_read_per_file(self):
        """Every request here is cached for the day, and the listing is shared.

        `PythonData.update_json` lists the same directory for every member, so over a
        full run the listing below costs nothing.
        """
        requested = []
        sections = self.candidates("requirements.txt", requested=requested)
        self.assertEqual(1, len(requested))
        self.assertTrue(requested[0].endswith(f"/{OWNER}/{REPO}/contents/"))
        with patch(
            "ecosystem.github_contents.request_json",
            side_effect=fake_request("requirements.txt", requested=requested),
        ):
            sections[0].update_json()
        self.assertEqual(2, len(requested))
        self.assertTrue(requested[1].endswith("/contents/requirements.txt"))

    def test_fetching_needs_owner_and_repo(self):
        """A section built from stored values alone cannot be refreshed."""
        with self.assertRaises(EcosystemError):
            self.stored(requires_qiskit=">=1.0").update_json()

    def test_fetching_needs_a_file(self):
        """The probe `from_github` builds is for `candidates`, not for reading."""
        probe = RequirementsData(owner=OWNER, repo=REPO)
        with patch(
            "ecosystem.github_contents.request_json",
            side_effect=AssertionError("no network"),
        ):
            with self.assertRaises(EcosystemError):
                probe.update_json()

    def test_from_github_takes_owner_and_repo_from_the_member(self):
        """The GitHub section is where owner and repo come from."""
        data = RequirementsData.from_github(GitHubData(owner=OWNER, repo=REPO))
        self.assertEqual(OWNER, data.owner)
        self.assertEqual(REPO, data.repo)


class TestRequirementsDataRequiresQiskit(RequirementsTestCase):
    """The specifier, which is the only reason the section is kept."""

    def test_qiskit_aer_is_not_qiskit(self):
        """Only the `qiskit` distribution itself counts."""
        self.assertIsNone(self.fetched(contents="qiskit-aer>=0.14\n").requires_qiskit)

    def test_unpinned_qiskit_is_forced_to_any_version(self):
        """Depending on qiskit without saying which is not the same as not at all."""
        data = self.fetched(contents="qiskit\n")
        with self.assertLogs("ecosystem", level="WARNING"):
            self.assertEqual(">=0", data.requires_qiskit)

    def test_the_specifier_is_looked_up_once(self):
        """The compat properties read it repeatedly, and a miss logs a warning."""
        data = self.fetched(contents=NO_QISKIT_TXT)
        with patch(
            "ecosystem.qiskit_requirement.find_requires_qiskit", return_value=None
        ) as lookup:
            self.assertIsNone(data.compatible_with_qiskit_v1)
            self.assertIsNone(data.compatible_with_qiskit_v2)
        self.assertEqual(1, lookup.call_count)

    def test_a_file_without_qiskit_declares_nothing(self):
        """The updater drops the section, so the stored table never appears."""
        self.assertIsNone(self.fetched(contents=NO_QISKIT_TXT).requires_qiskit)

    def test_an_unparseable_line_is_skipped(self):
        """One bad line is reported and does not hide the qiskit requirement."""
        data = self.fetched(contents="=not a requirement\nqiskit>=2.0\n")
        with self.assertLogs("ecosystem", level="WARNING"):
            self.assertEqual(">=2.0", data.requires_qiskit)

    def test_the_mixin_derives_the_flags_from_the_specifier(self):
        """Everything else in the table follows from `requires_qiskit`."""
        self.assertEqual(
            {
                "file": "requirements.txt",
                "requires_qiskit": "<3,>=1.4",
                "compatible_with_qiskit_v1": True,
                "compatible_with_qiskit_v2": True,
                "highest_supported_qiskit_version": "2.1.0",
                "highest_supported_qiskit_release_date": date(2026, 6, 10),
            },
            self.fetched().to_dict(),
        )

    def test_the_warnings_name_the_repository(self):
        """There is no distribution here, so the repository is what gets named."""
        self.assertEqual(f"{OWNER}/{REPO}", self.fetched().declared_by)


class TestRequirementsDataRoundTrip(RequirementsTestCase):
    """A stored section has to work with no network."""

    def test_stored_values_are_returned_unfetched(self):
        """Reading a member file must not reach GitHub or PyPI."""
        section = {
            "file": "requirements.txt",
            "requires_qiskit": "~=2.1.0",
            "compatible_with_qiskit_v1": False,
            "compatible_with_qiskit_v2": True,
            "highest_supported_qiskit_version": "2.1.0",
            "highest_supported_qiskit_release_date": date(2026, 6, 10),
        }
        data = RequirementsData.from_dict(dict(section))
        with patch(
            "ecosystem.github_contents.request_json",
            side_effect=AssertionError("no network"),
        ):
            self.assertEqual(section, data.to_dict())

    def test_stored_flags_survive_a_missing_specifier(self):
        """The mixin falls back to what was stored, as it does for the other sections."""
        data = RequirementsData.from_dict(
            {"file": "requirements.txt", "compatible_with_qiskit_v2": True}
        )
        self.assertTrue(data.compatible_with_qiskit_v2)
        self.assertIsNone(data.highest_supported_qiskit_version)

    def test_owner_and_repo_are_not_serialized(self):
        """They would duplicate `[github]`, which is where they belong."""
        self.assertNotIn("owner", self.fetched().to_dict())
        self.assertNotIn("repo", self.fetched().to_dict())


class TestMemberUpdateRequirements(RequirementsTestCase):
    """`Member.update_requirements` is the entry point for the section."""

    @staticmethod
    def member(**kwargs):
        """A member with a GitHub section, which is what the updater needs."""
        return Member(
            name="Banana Notebooks",
            url=f"https://github.com/{OWNER}/{REPO}",
            uuid="banana-uuid-0000-0000-000000000000",
            maturity="experimental",
            github=GitHubData(owner=OWNER, repo=REPO),
            **kwargs,
        )

    def update(self, member, *names, contents=REQUIREMENTS_TXT):
        """Runs the updater against a repository holding `names`."""
        with patch(
            "ecosystem.github_contents.request_json",
            side_effect=fake_request(*names, contents=contents),
        ):
            member.update_requirements()
        return member.requirements

    def test_section_is_created_from_the_repository(self):
        """A repository with only a requirements file gets one section."""
        sections = self.update(self.member(), "requirements.txt")
        self.assertEqual(
            [("requirements.txt", "<3,>=1.4")],
            [(section.file, section.requires_qiskit) for section in sections],
        )

    def test_one_section_per_file_that_names_qiskit(self):
        """Breadth is deliberate: benchpress declares its Qiskit in only one of eight."""
        sections = self.update(
            self.member(), "requirements.txt", "requirements-qiskit.txt"
        )
        self.assertEqual(
            ["requirements-qiskit.txt", "requirements.txt"],
            [section.file for section in sections],
        )

    def test_a_file_that_does_not_name_qiskit_is_left_out(self):
        """The qiskit requirement is the only thing these sections are kept for."""
        sections = self.update(
            self.member(),
            "requirements.txt",
            "requirements-dev.txt",
            contents={
                "requirements.txt": REQUIREMENTS_TXT,
                "requirements-dev.txt": NO_QISKIT_TXT,
            },
        )
        self.assertEqual(["requirements.txt"], [section.file for section in sections])

    def test_no_section_when_a_manifest_declares_a_distribution(self):
        """`[python.*]` or `[pypi.*]` describes it, so this would duplicate them."""
        self.assertIsNone(
            self.update(self.member(), "pyproject.toml", "requirements.txt")
        )

    def test_no_section_when_the_file_does_not_name_qiskit(self):
        """The qiskit requirement is the only thing the table is kept for."""
        self.assertIsNone(
            self.update(self.member(), "requirements.txt", contents=NO_QISKIT_TXT)
        )

    def test_a_published_distribution_is_not_what_decides(self):
        """The rule is about manifests in the repository, not about releases."""
        member = self.member(pypi={"banana": PyPIData("banana")})
        self.assertIsNotNone(self.update(member, "requirements.txt"))

    def test_a_stale_section_is_dropped(self):
        """`to_dict` leaves out None, so that is what removes the tables on write."""
        member = self.member(requirements=[self.stored(requires_qiskit=">=1.0")])
        self.assertIsNone(self.update(member, "pyproject.toml", "requirements.txt"))

    def test_a_member_without_a_github_section_is_skipped(self):
        """There is no repository to read, and no section to invent."""
        member = Member(
            name="Banana Notebooks",
            url="https://gitlab.com/banana-org/banana-notebooks",
            maturity="experimental",
        )
        with patch(
            "ecosystem.github_contents.request_json",
            side_effect=AssertionError("no network"),
        ):
            member.update_requirements()
        self.assertIsNone(member.requirements)

    def test_the_sections_round_trip_through_from_dict(self):
        """What the updater writes is what reading the member file gives back."""
        sections = self.update(
            self.member(), "requirements.txt", "requirements-dev.txt"
        )
        member = Member.from_dict(
            {
                "name": "Banana Notebooks",
                "url": f"https://github.com/{OWNER}/{REPO}",
                "maturity": "experimental",
                "requirements": [section.to_dict() for section in sections],
            }
        )
        self.assertEqual(
            [section.to_dict() for section in sections],
            [section.to_dict() for section in member.requirements],
        )


class TestRequirementsCard(RequirementsTestCase):
    """The card, which names the file and says nothing about installing."""

    def card(self, project=True, file="requirements.txt"):
        """The card for a stored section, with or without a project behind it."""
        return RequirementsCard.from_requirements_data(
            self.fetched(file=file),
            (
                Member(
                    name="Banana Notebooks",
                    url=f"https://github.com/{OWNER}/{REPO}",
                    maturity="experimental",
                    github=GitHubData(owner=OWNER, repo=REPO),
                )
                if project
                else None
            ),
        )

    def test_the_card_is_titled_after_the_file(self):
        """A member can have several, and the filename is what tells them apart."""
        self.assertIn(
            "#### :material-file-document-outline: `requirements-dev.txt`",
            "\n".join(self.card(file="requirements-dev.txt").generate()),
        )

    def test_the_file_links_to_the_default_branch(self):
        """The branch is not stored anywhere, so the link goes through HEAD."""
        self.assertEqual(
            f"https://github.com/{OWNER}/{REPO}/blob/HEAD/requirements.txt",
            self.card().file_url,
        )
        self.assertIn(
            "**declared in** [`requirements.txt`]", "\n".join(self.card().body())
        )

    def test_the_file_is_unlinked_without_a_project(self):
        """Owner and repo live in `[github]`; without it there is no URL to guess."""
        card = self.card(project=False)
        self.assertIsNone(card.file_url)
        self.assertIn("**declared in** `requirements.txt`", "\n".join(card.body()))

    def test_there_is_nothing_to_pip_install(self):
        """No manifest means no distribution, which is the point of the section."""
        self.assertNotIn("pip install", "\n".join(self.card().body()))

    def test_the_body_carries_the_qiskit_compatibility_table(self):
        """The same table the package cards show, from the same mixin."""
        body = "\n".join(self.card().body())
        self.assertIn("Qiskit Compatibility", body)
        self.assertIn("<3,>=1.4", body)
        self.assertIn("2.1.0", body)

    def test_every_bullet_is_its_own_paragraph(self):
        """Consecutive lines would collapse into one wrapped paragraph."""
        body = self.card().body()
        end = next(i for i, line in enumerate(body) if "Qiskit Compatibility" in line)
        bullets = [i for i, line in enumerate(body[:end]) if line.startswith(":")]
        self.assertEqual(2, len(bullets))
        for index in bullets:
            with self.subTest(bullet=body[index]):
                self.assertEqual("", body[index + 1])


class TestRequirementsOnTheProjectPage(RequirementsTestCase):
    """Its own section: a requirements file is not a package."""

    def page(self, **kwargs):
        """The project page for a member, as one string."""
        project = Member(
            name="Banana Notebooks",
            url=f"https://github.com/{OWNER}/{REPO}",
            uuid="banana-uuid-0000-0000-000000000000",
            maturity="experimental",
            github=GitHubData(owner=OWNER, repo=REPO),
            **kwargs,
        )
        return "\n".join(ProjectPage(project, "p/banana.md").requirements())

    def test_the_card_is_in_its_own_section(self):
        """These members have no Packages section at all to put it in."""
        page = self.page(requirements=[self.fetched()])
        self.assertIn("### :material-file-document-outline: Requirements", page)
        self.assertIn("#### :material-file-document-outline: `requirements.txt`", page)
        self.assertIn("<3,>=1.4", page)

    def test_one_card_per_file(self):
        """A member can declare several, and the check ups read all of them."""
        page = self.page(
            requirements=[
                self.fetched(file="requirements-dev.txt"),
                self.fetched(file="requirements.txt"),
            ]
        )
        self.assertIn(
            "#### :material-file-document-outline: `requirements-dev.txt`", page
        )
        self.assertIn("#### :material-file-document-outline: `requirements.txt`", page)

    def test_no_section_without_a_requirements_table(self):
        """Which is every member but a handful."""
        self.assertEqual("", self.page())
