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

"""Tests for ecosystem/python.py."""

from datetime import date
from unittest import TestCase
from unittest.mock import patch

from tests.common import named, names as package_names
from ecosystem.error_handling import EcosystemError
from ecosystem.github import GitHubData
from ecosystem.julia import JuliaData
from ecosystem.member import Member
from ecosystem.pypi import PyPIData
from ecosystem.python import (
    PythonData,
    parse_requirements,
    parse_setup_cfg,
    parse_setup_py,
)
from ecosystem.request import URL

OWNER = "banana-org"
REPO = "banana-compiler"

PYPROJECT = """
[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[project]
name = "Banana_Compiler"
version = "0.3.1"
description = "Compiles bananas"
requires-python = ">=3.9"
license = "Apache-2.0"
dependencies = ["qiskit>=1.2,<3", "numpy"]
"""

SETUP_CFG = """
[metadata]
name = banana-compiler
version = 0.0.9
description = Compiles bananas, slowly
classifiers =
    License :: OSI Approved :: MIT License
    Programming Language :: Python :: 3

[options]
python_requires = >=3.7
install_requires =
    qiskit-terra>=0.19
    qiskit>=0.45
"""

SETUP_PY = """
from setuptools import setup, find_packages

VERSION = read_version_from_somewhere()

setup(
    name="banana-compiler",
    version=VERSION,
    license="Apache 2.0",
    install_requires=["qiskit>=1.0"],
    packages=find_packages(),
)
"""

REQUIREMENTS_TXT = """
# the dependencies setup.py reads
-r requirements-dev.txt
--index-url https://example.invalid/simple
qiskit>=1.4,<3
numpy ; python_version >= "3.10"
qiskit-aer[gpu]>=0.14
"""

SETUP_PY_DEFERRED = """
from setuptools import setup

with open("requirements.txt") as f:
    REQUIREMENTS = f.read().splitlines()

setup(
    name="banana-compiler",
    version="0.3.1",
    install_requires=REQUIREMENTS,
)
"""


def listing(*names):
    """A contents-API directory listing holding `names` as files."""
    return {"entries": [{"name": name, "type": "file"} for name in names]}


class PythonDataTestCase(TestCase):
    """Base with the Qiskit release table stubbed out."""

    def setUp(self):
        super().setUp()
        patcher = patch.object(
            PythonData,
            "all_qiskit_versions",
            return_value={
                "1.0.0": {"upload_at": date(2024, 2, 1)},
                "2.0.0": {"upload_at": date(2025, 4, 1)},
            },
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    @staticmethod
    def fetched(**manifests):
        """A PythonData as if `update_json` had found `manifests`."""
        data = PythonData(owner=OWNER, repo=REPO)
        data._pyproject = manifests.get("pyproject")  # pylint: disable=protected-access
        data._setup_cfg = manifests.get("setup_cfg")  # pylint: disable=protected-access
        data._setup_py = manifests.get("setup_py")  # pylint: disable=protected-access
        data._requirements = manifests.get(  # pylint: disable=protected-access
            "requirements"
        )
        return data


class TestParseSetupPy(TestCase):
    """setup.py is read statically, never executed."""

    def test_literal_and_deferred_kwargs_are_separated(self):
        """Literal arguments are read; computed ones are only named."""
        parsed = parse_setup_py(SETUP_PY)
        self.assertEqual("banana-compiler", parsed["literals"]["name"])
        self.assertEqual(["qiskit>=1.0"], parsed["literals"]["install_requires"])
        self.assertEqual(["version", "packages"], parsed["deferred"])

    def test_setup_is_not_executed(self):
        """A setup.py with side effects is parsed without running them."""
        parsed = parse_setup_py(
            "raise SystemExit('boom')\nsetup(name='banana-compiler')\n"
        )
        self.assertEqual("banana-compiler", parsed["literals"]["name"])

    def test_namespaced_setup_call_is_found(self):
        """`setuptools.setup(...)` is recognized as well as a bare `setup(...)`."""
        parsed = parse_setup_py("import setuptools\nsetuptools.setup(name='banana')\n")
        self.assertEqual("banana", parsed["literals"]["name"])

    def test_unparseable_file_warns_and_yields_nothing(self):
        """A setup.py that does not compile is reported, not raised on."""
        with self.assertLogs("ecosystem", level="WARNING"):
            parsed = parse_setup_py("def (:\n")
        self.assertEqual({"literals": {}, "deferred": []}, parsed)

    def test_no_setup_call(self):
        """A module without a setup() call yields nothing."""
        self.assertEqual({"literals": {}, "deferred": []}, parse_setup_py("x = 1\n"))


class TestParseSetupCfg(TestCase):
    """setup.cfg is INI, so its lists are indented strings."""

    def test_sections_become_dicts(self):
        """[metadata] and [options] are both available."""
        parsed = parse_setup_cfg(SETUP_CFG)
        self.assertEqual("banana-compiler", parsed["metadata"]["name"])
        self.assertEqual(">=3.7", parsed["options"]["python_requires"])

    def test_unparseable_file_warns_and_yields_nothing(self):
        """A setup.cfg that is not INI is reported, not raised on."""
        with self.assertLogs("ecosystem", level="WARNING"):
            self.assertEqual({}, parse_setup_cfg("[unclosed\n"))


class TestPythonDataFields(PythonDataTestCase):
    """Field reading over the three manifests."""

    def test_pep_621_pyproject(self):
        """A modern pyproject.toml provides every field on its own."""
        import tomllib  # pylint: disable=import-outside-toplevel

        data = self.fetched(pyproject=tomllib.loads(PYPROJECT))
        self.assertEqual(
            {
                "package_name": "banana-compiler",
                "version": "0.3.1",
                "license": "Apache-2.0",
                "description": "Compiles bananas",
                "requires_python": ">=3.9",
                "requires_qiskit": "<3,>=1.2",
                "compatible_with_qiskit_v1": True,
                "compatible_with_qiskit_v2": True,
                "highest_supported_qiskit_release_date": date(2025, 4, 1),
                "highest_supported_qiskit_version": "2.0.0",
                "build_backend": "setuptools.build_meta",
                "source": ["pyproject.toml"],
                "deferred": [],
            },
            data.to_dict(),
        )

    def test_package_name_is_canonicalized(self):
        """`Banana_Compiler` is the same distribution as `banana-compiler`."""
        import tomllib  # pylint: disable=import-outside-toplevel

        data = self.fetched(pyproject=tomllib.loads(PYPROJECT))
        self.assertEqual("banana-compiler", data.package_name)

    def test_setup_cfg_lists_are_split(self):
        """Indented multi-line INI values are read as lists."""
        data = self.fetched(setup_cfg=parse_setup_cfg(SETUP_CFG))
        self.assertEqual(["qiskit-terra>=0.19", "qiskit>=0.45"], data.dependencies)
        self.assertEqual(">=0.45", data.requires_qiskit)
        self.assertEqual(">=3.7", data.requires_python)

    def test_setup_py_only(self):
        """A legacy project still yields a name, license and requires_qiskit."""
        data = self.fetched(setup_py=parse_setup_py(SETUP_PY))
        self.assertEqual("banana-compiler", data.package_name)
        self.assertEqual("Apache-2.0", str(data.license))
        self.assertEqual(">=1.0", data.requires_qiskit)
        self.assertEqual(["packages", "version"], data.deferred)

    def test_pyproject_wins_over_the_older_manifests(self):
        """Precedence is pyproject.toml, then setup.cfg, then setup.py."""
        import tomllib  # pylint: disable=import-outside-toplevel

        data = self.fetched(
            pyproject=tomllib.loads(PYPROJECT),
            setup_cfg=parse_setup_cfg(SETUP_CFG),
            setup_py=parse_setup_py(SETUP_PY),
        )
        self.assertEqual("0.3.1", data.version)
        self.assertEqual("Apache-2.0", str(data.license))
        self.assertEqual(["pyproject.toml", "setup.cfg", "setup.py"], data.source)

    def test_setup_cfg_wins_over_setup_py(self):
        """Without a pyproject.toml, setup.cfg is the authority."""
        data = self.fetched(
            setup_cfg=parse_setup_cfg(SETUP_CFG), setup_py=parse_setup_py(SETUP_PY)
        )
        self.assertEqual("0.0.9", data.version)
        self.assertEqual("Compiles bananas, slowly", data.description)

    def test_no_manifest_is_not_an_error(self):
        """A repository with no packaging metadata reports nothing declared."""
        data = self.fetched()
        self.assertFalse(data.fetched)
        self.assertIsNone(data.package_name)
        self.assertIsNone(data.requires_qiskit)
        self.assertEqual({"source": [], "deferred": []}, data.to_dict())


class TestPythonDataLicense(PythonDataTestCase):
    """`[project].license` has more than one shape, and P12 reads this field."""

    def test_spdx_string(self):
        """PEP 639 gives the license as an SPDX expression."""
        data = self.fetched(pyproject={"project": {"license": "MIT"}})
        self.assertEqual("MIT", str(data.license))

    def test_license_table_with_text(self):
        """The pre-PEP-639 table carries the name under `text`."""
        data = self.fetched(
            pyproject={"project": {"license": {"text": "BSD-3-Clause"}}}
        )
        self.assertEqual("BSD-3-Clause", str(data.license))

    def test_license_table_with_file_is_not_a_license_name(self):
        """`{file = "LICENSE.txt"}` names a file, so it declares no license name."""
        data = self.fetched(pyproject={"project": {"license": {"file": "LICENSE.txt"}}})
        self.assertIsNone(data.license)

    def test_falls_back_to_the_trove_classifier(self):
        """With no `license` key, the classifier is read the way PyPI's is."""
        data = self.fetched(setup_cfg=parse_setup_cfg(SETUP_CFG))
        self.assertEqual("MIT", str(data.license))


class TestPythonDataDeferred(PythonDataTestCase):
    """What the build backend computes cannot be read from the manifests."""

    def test_dynamic_version_is_not_reported_as_a_version(self):
        """`dynamic = ["version"]` means the manifest does not state a version."""
        data = self.fetched(
            pyproject={"project": {"name": "banana", "dynamic": ["version"]}}
        )
        self.assertIsNone(data.version)
        self.assertEqual(["version"], data.deferred)

    def test_dynamic_dependencies_separates_from_no_qiskit(self):
        """A deferred dependency list is not the same as not needing Qiskit."""
        deferred = self.fetched(
            pyproject={"project": {"name": "banana", "dynamic": ["dependencies"]}}
        )
        declared = self.fetched(
            pyproject={"project": {"name": "banana", "dependencies": ["numpy"]}}
        )
        self.assertIsNone(deferred.requires_qiskit)
        self.assertIsNone(declared.requires_qiskit)
        self.assertEqual(["dependencies"], deferred.deferred)
        self.assertEqual([], declared.deferred)

    def test_dynamic_and_setup_py_deferred_are_merged(self):
        """Both manifests can defer, and the union is reported once, sorted."""
        data = self.fetched(
            pyproject={"project": {"name": "banana", "dynamic": ["version"]}},
            setup_py=parse_setup_py(SETUP_PY),
        )
        self.assertEqual(["packages", "version"], data.deferred)


class TestPythonDataRequiresQiskit(PythonDataTestCase):
    """`requires_qiskit` drives every compat field."""

    def test_qiskit_terra_is_not_qiskit(self):
        """Only a requirement named `qiskit` counts."""
        data = self.fetched(
            pyproject={"project": {"dependencies": ["qiskit-terra>=0.19"]}}
        )
        self.assertIsNone(data.requires_qiskit)

    def test_unpinned_qiskit_is_forced_to_any_version(self):
        """A bare `qiskit` dependency is warned about and read as `>=0`."""
        data = self.fetched(pyproject={"project": {"dependencies": ["qiskit"]}})
        with self.assertLogs("ecosystem", level="WARNING"):
            self.assertEqual(">=0", data.requires_qiskit)

    def test_specifier_is_computed_once(self):
        """Repeated reads do not re-warn: the compat fields all go through here."""
        data = self.fetched(pyproject={"project": {"dependencies": ["qiskit"]}})
        with self.assertLogs("ecosystem", level="WARNING") as logs:
            data.to_dict()
        self.assertEqual(1, len(logs.records))

    def test_unparseable_requirement_is_skipped(self):
        """A broken requirement string is reported and does not stop the scan."""
        data = self.fetched(
            pyproject={"project": {"dependencies": ["not a requirement!", "qiskit>=2"]}}
        )
        with self.assertLogs("ecosystem", level="WARNING"):
            self.assertEqual(">=2", data.requires_qiskit)

    def test_compat_flags_follow_the_specifier(self):
        """A Qiskit 2-only project is not compatible with the v1 series."""
        data = self.fetched(pyproject={"project": {"dependencies": ["qiskit>=2.0"]}})
        self.assertFalse(data.compatible_with_qiskit_v1)
        self.assertTrue(data.compatible_with_qiskit_v2)
        self.assertEqual("2.0.0", data.highest_supported_qiskit_version)


class TestParseRequirements(TestCase):
    """requirements.txt is one requirement per line, plus pip's own options."""

    def test_options_and_comments_are_dropped(self):
        """Only requirement lines survive; `-r` is not followed."""
        self.assertEqual(
            [
                "qiskit>=1.4,<3",
                'numpy ; python_version >= "3.10"',
                "qiskit-aer[gpu]>=0.14",
            ],
            parse_requirements(REQUIREMENTS_TXT),
        )

    def test_inline_comments_and_blank_lines(self):
        """A trailing comment is not part of the requirement."""
        self.assertEqual(
            ["qiskit>=2.0"], parse_requirements("\nqiskit>=2.0  # the SDK\n\n")
        )

    def test_continuation_lines_are_joined(self):
        """A backslash continues the requirement on the next line."""
        self.assertEqual(
            ["qiskit >=1.4, <3"], parse_requirements("qiskit \\\n>=1.4, <3\n")
        )

    def test_a_direct_url_requirement_is_kept(self):
        """`Requirement` parses these, so they are not this parser's problem."""
        self.assertEqual(
            ["qiskit @ git+https://github.com/Qiskit/qiskit.git@main"],
            parse_requirements(
                "qiskit @ git+https://github.com/Qiskit/qiskit.git@main"
            ),
        )


class TestPythonDataRequirementsFallback(PythonDataTestCase):
    """requirements.txt fills in dependencies the manifests only point at."""

    def test_a_deferred_install_requires_falls_back_to_the_file(self):
        """`install_requires=REQUIREMENTS` is read from the file it reads."""
        data = self.fetched(
            setup_py=parse_setup_py(SETUP_PY_DEFERRED),
            requirements=parse_requirements(REQUIREMENTS_TXT),
        )
        self.assertEqual(["install_requires"], data.deferred)
        self.assertEqual("<3,>=1.4", data.requires_qiskit)
        self.assertTrue(data.compatible_with_qiskit_v2)

    def test_the_file_is_reported_as_the_source(self):
        """A section has to say the value came from outside the manifests."""
        data = self.fetched(
            setup_py=parse_setup_py(SETUP_PY_DEFERRED),
            requirements=parse_requirements(REQUIREMENTS_TXT),
        )
        self.assertEqual(["setup.py", "requirements.txt"], data.source)

    def test_a_declaring_manifest_wins(self):
        """The file is a fallback, not an override: `[project]` stays authoritative."""
        import tomllib  # pylint: disable=import-outside-toplevel

        data = self.fetched(
            pyproject=tomllib.loads(PYPROJECT),
            requirements=parse_requirements("qiskit==1.0.0\n"),
        )
        self.assertEqual("<3,>=1.2", data.requires_qiskit)
        self.assertEqual(["pyproject.toml"], data.source)

    def test_setup_cfg_dependencies_win_too(self):
        """Every manifest rung comes before the file."""
        data = self.fetched(
            setup_cfg=parse_setup_cfg(SETUP_CFG),
            requirements=parse_requirements("qiskit==1.0.0\n"),
        )
        self.assertEqual(">=0.45", data.requires_qiskit)
        self.assertEqual(["setup.cfg"], data.source)

    def test_a_requirements_file_alone_declares_no_distribution(self):
        """It is not a manifest: with no manifest there is nothing to fill in."""
        requested = []

        def fake_request(url, **kwargs):
            requested.append(str(url))
            if str(url).endswith("/contents/"):
                return listing("requirements.txt", "README.md")
            return kwargs["parser"](REQUIREMENTS_TXT)

        with patch("ecosystem.github_contents.request_json", side_effect=fake_request):
            data = PythonData(owner=OWNER, repo=REPO)
            data.update_json()

        self.assertTrue(requested[1].endswith("/requirements.txt"))
        self.assertFalse(data.fetched)
        self.assertIsNone(data.package_name)

    def test_it_is_fetched_with_the_manifests(self):
        """One listing, then the manifest and the requirements file."""

        def fake_request(url, **kwargs):
            if str(url).endswith("/contents/"):
                return listing("setup.py", "requirements.txt")
            if str(url).endswith("/setup.py"):
                return kwargs["parser"](SETUP_PY_DEFERRED)
            return kwargs["parser"](REQUIREMENTS_TXT)

        with patch("ecosystem.github_contents.request_json", side_effect=fake_request):
            data = PythonData(owner=OWNER, repo=REPO)
            data.update_json()

        self.assertEqual("<3,>=1.4", data.requires_qiskit)
        self.assertEqual(["setup.py", "requirements.txt"], data.source)


class TestPythonDataRoundTrip(PythonDataTestCase):
    """A stored section has to work with no network."""

    def test_stored_values_are_returned_unfetched(self):
        """Every serialized field survives `from_dict` without a fetch."""
        stored = {
            "package_name": "banana-compiler",
            "version": "0.3.1",
            "license": "Apache-2.0",
            "description": "Compiles bananas",
            "requires_python": ">=3.9",
            "requires_qiskit": ">=1.2",
            "build_backend": "setuptools.build_meta",
            "path": "packages/compiler",
            "source": ["pyproject.toml"],
            "deferred": ["version"],
        }
        data = PythonData.from_dict(dict(stored))
        self.assertEqual(
            stored
            | {
                "compatible_with_qiskit_v1": True,
                "compatible_with_qiskit_v2": True,
                "highest_supported_qiskit_release_date": date(2025, 4, 1),
                "highest_supported_qiskit_version": "2.0.0",
            },
            data.to_dict(),
        )


class TestPythonDataFetching(PythonDataTestCase):
    """`update_json` lists the directory, then reads what is there."""

    def test_only_present_manifests_are_requested(self):
        """A repository with one manifest costs one listing and one read."""
        requested = []

        def fake_request(url, **kwargs):
            requested.append(str(url))
            if str(url).endswith("/contents/"):
                return listing("pyproject.toml", "README.md")
            return kwargs["parser"](PYPROJECT)

        with patch("ecosystem.github_contents.request_json", side_effect=fake_request):
            data = PythonData(owner=OWNER, repo=REPO)
            data.update_json()

        self.assertEqual(2, len(requested))
        self.assertTrue(requested[1].endswith("/pyproject.toml"))
        self.assertEqual("0.3.1", data.version)
        self.assertEqual(["pyproject.toml"], data.source)

    def test_directories_are_not_manifests(self):
        """A directory named `setup.py` would not be a manifest."""
        with patch(
            "ecosystem.github_contents.request_json",
            return_value={"entries": [{"name": "setup.py", "type": "dir"}]},
        ):
            data = PythonData(owner=OWNER, repo=REPO)
            data.update_json()
        self.assertFalse(data.fetched)

    def test_path_is_used_for_a_monorepo(self):
        """Manifests are read from `path` when they are not at the root."""
        requested = []

        def fake_request(url, **kwargs):  # pylint: disable=unused-argument
            requested.append(str(url))
            return listing()

        with patch("ecosystem.github_contents.request_json", side_effect=fake_request):
            PythonData(owner=OWNER, repo=REPO, path="packages/compiler").update_json()

        self.assertTrue(requested[0].endswith("/contents/packages/compiler/"))

    def test_fetching_needs_owner_and_repo(self):
        """A section built from stored values alone cannot be refreshed."""
        with self.assertRaises(EcosystemError):
            PythonData(package_name="banana-compiler").update_json()

    def test_from_github_takes_owner_and_repo_from_the_member(self):
        """The GitHub section is where owner and repo come from."""
        github = type("FakeGitHub", (), {"owner": OWNER, "repo": REPO})()
        data = PythonData.from_github(github, path="packages/compiler")
        self.assertEqual(OWNER, data.owner)
        self.assertEqual(REPO, data.repo)
        self.assertEqual("packages/compiler", data.path)


class TestMemberUpdatePython(PythonDataTestCase):
    """`Member.update_python` is the entry point for the section."""

    @staticmethod
    def member(**kwargs):
        """A member with a GitHub section, which is what the updater needs."""
        return Member(
            name="Banana Compiler",
            url=f"https://github.com/{OWNER}/{REPO}",
            uuid="banana-uuid-0000-0000-000000000000",
            maturity="experimental",
            github=GitHubData(owner=OWNER, repo=REPO),
            **kwargs,
        )

    @staticmethod
    def fake_request(manifest=PYPROJECT, name="pyproject.toml"):
        """Serves a directory listing holding `name`, then that manifest."""

        def request(url, **kwargs):
            if str(url).endswith(("/contents/", "/")):
                return listing(name)
            return kwargs["parser"](manifest)

        return request

    def test_section_is_created_from_the_repository(self):
        """The distribution name is discovered, so the updater creates the section."""
        member = self.member()
        with patch(
            "ecosystem.github_contents.request_json", side_effect=self.fake_request()
        ):
            member.update_python()
        self.assertEqual(["banana-compiler"], package_names(member.python))
        self.assertEqual("0.3.1", named(member.python, "banana-compiler").version)

    def test_no_section_for_a_distribution_that_is_published(self):
        """The release describes it already, so a section would just duplicate it."""
        member = self.member(pypi=[PyPIData("banana-compiler")])
        with patch(
            "ecosystem.github_contents.request_json", side_effect=self.fake_request()
        ):
            member.update_python()
        self.assertEqual([], member.python)

    def test_the_published_name_is_what_decides(self):
        """A repository can publish one distribution and declare another, unreleased
        one. Skipping on "publishes something" would lose the second."""
        member = self.member(pypi=[PyPIData("banana-cli")])
        with patch(
            "ecosystem.github_contents.request_json", side_effect=self.fake_request()
        ):
            member.update_python()
        self.assertEqual(["banana-compiler"], package_names(member.python))

    def test_the_comparison_ignores_name_spelling(self):
        """`Banana_Compiler` in the manifest and `banana-compiler` on PyPI are one
        distribution, so the section is still not created."""
        member = self.member(pypi=[PyPIData("Banana_Compiler")])
        with patch(
            "ecosystem.github_contents.request_json", side_effect=self.fake_request()
        ):
            member.update_python()
        self.assertEqual([], member.python)

    def test_a_julia_release_of_the_same_name_does_not_count(self):
        """Only PyPI is consulted: a Julia package is a different artifact in a
        different registry, and says nothing about whether `pip` can find this one."""
        member = self.member(julia=[JuliaData("banana-compiler")])
        with patch(
            "ecosystem.github_contents.request_json", side_effect=self.fake_request()
        ):
            member.update_python()
        self.assertEqual(["banana-compiler"], package_names(member.python))

    def test_an_existing_section_is_refreshed_even_when_published(self):
        """A section added on purpose keeps being updated, to cross-check the release."""
        member = self.member(
            pypi=[PyPIData("banana-compiler")],
            python=[PythonData(package_name="banana-compiler")],
        )
        with patch(
            "ecosystem.github_contents.request_json", side_effect=self.fake_request()
        ):
            member.update_python()
        self.assertEqual("0.3.1", named(member.python, "banana-compiler").version)

    def test_section_is_rekeyed_when_the_distribution_is_renamed(self):
        """The key follows the name the repository declares now."""
        member = self.member(python=[PythonData(package_name="old-name")])
        with patch(
            "ecosystem.github_contents.request_json", side_effect=self.fake_request()
        ):
            member.update_python()
        self.assertEqual(["banana-compiler"], package_names(member.python))

    def test_section_is_dropped_when_nothing_declares_a_distribution(self):
        """A repository that stopped being a Python package loses its section."""
        member = self.member(python=[PythonData(package_name="b")])
        with patch(
            "ecosystem.github_contents.request_json", return_value=listing("README.md")
        ):
            member.update_python()
        self.assertEqual([], member.python)

    def test_a_member_without_a_github_section_is_skipped(self):
        """There is nothing to fetch from, so nothing is attempted."""
        member = Member(
            name="Banana Compiler",
            url=f"https://github.com/{OWNER}/{REPO}",
            uuid="banana-uuid-0000-0000-000000000000",
            maturity="experimental",
        )
        with patch("ecosystem.github_contents.request_json") as request:
            member.update_python()
        self.assertEqual([], member.python)
        request.assert_not_called()

    def test_the_declared_path_is_kept_across_updates(self):
        """`path` cannot be discovered, so a refresh must not lose it."""
        member = self.member(python=[PythonData(path="packages/compiler")])
        requested = []

        def request(url, **kwargs):
            requested.append(str(url))
            return self.fake_request()(url, **kwargs)

        with patch("ecosystem.github_contents.request_json", side_effect=request):
            member.update_python()
        self.assertTrue(requested[0].endswith("/contents/packages/compiler/"))
        self.assertEqual(
            "packages/compiler", named(member.python, "banana-compiler").path
        )

    def test_the_section_round_trips_through_from_dict(self):
        """A member read back from a toml file keeps its python section."""
        member = self.member()
        with patch(
            "ecosystem.github_contents.request_json", side_effect=self.fake_request()
        ):
            member.update_python()
        restored = Member.from_dict(member.to_dict())
        self.assertEqual(
            named(member.python, "banana-compiler").to_dict(),
            named(restored.python, "banana-compiler").to_dict(),
        )


class TestPythonDataFromUrl(PythonDataTestCase):
    """A manifest URL is how a distribution that is on no registry is submitted."""

    @staticmethod
    def from_url(url):
        """The section a submitted URL creates, if any."""
        return PythonData.from_url(URL(url))

    def test_a_manifest_at_the_repository_root(self):
        """The common case: one distribution, declared at the top of the repository."""
        data = self.from_url(f"https://github.com/{OWNER}/{REPO}/blob/main/setup.cfg")
        self.assertEqual((OWNER, REPO), (data.owner, data.repo))
        self.assertIsNone(data.path)

    def test_a_manifest_in_a_subdirectory_declares_the_path(self):
        """`path` cannot be discovered, so the URL is the only way to state it."""
        data = self.from_url(
            f"https://github.com/{OWNER}/{REPO}/blob/main/packages/compiler/pyproject.toml"
        )
        self.assertEqual("packages/compiler", data.path)

    def test_the_branch_is_dropped(self):
        """Manifests are always read from the default branch."""
        data = self.from_url(
            f"https://github.com/{OWNER}/{REPO}/blob/v0.3.1/pyproject.toml"
        )
        self.assertEqual((OWNER, REPO, None), (data.owner, data.repo, data.path))

    def test_other_urls_are_not_claimed(self):
        """A repository or release link is left in `packages` for something else."""
        for url in (
            f"https://github.com/{OWNER}/{REPO}",
            f"https://github.com/{OWNER}/{REPO}/releases/tag/v0.3.1",
            "https://pypi.org/project/banana-compiler/",
        ):
            with self.subTest(url=url):
                self.assertIsNone(self.from_url(url))

    def test_a_github_blob_that_is_not_a_manifest_is_an_error(self):
        """The URL was meant as a manifest, so pointing at the wrong file is a typo."""
        with self.assertRaises(EcosystemError):
            self.from_url(f"https://github.com/{OWNER}/{REPO}/blob/main/README.md")


class TestUpsertSectionsPython(PythonDataTestCase):
    """`upsert_sections` turns a submitted manifest URL into a `[python.*]` section."""

    @staticmethod
    def member(packages):
        """A submitted member, with no sections yet beyond its package URLs."""
        return Member(
            name="Banana Compiler",
            url=f"https://github.com/{OWNER}/{REPO}",
            uuid="banana-uuid-0000-0000-000000000000",
            maturity="experimental",
            packages=[URL(package) for package in packages],
        )

    def test_a_manifest_url_writes_no_table_before_it_is_read(self):
        """A `[python.*]` table has to carry `package_name`, and only the manifest says what
        it is. A stub keyed by a stand-in is a member file the schema rejects, and a pattern
        cannot be keyed at all, so the declaration in `packages` is the whole record until
        `update_python` reads the repository."""
        member = self.member(
            [f"https://github.com/{OWNER}/{REPO}/blob/main/chemistry/pyproject.toml"]
        )
        member.upsert_sections()
        self.assertEqual([], member.python)
        self.assertEqual(
            [f"https://github.com/{OWNER}/{REPO}/blob/main/chemistry/pyproject.toml"],
            [str(url) for url in member.packages],
        )

    def test_a_declared_manifest_is_what_the_updater_reads(self):
        """The section comes from the declaration rather than from a stub left behind."""
        member = self.member(
            [f"https://github.com/{OWNER}/{REPO}/blob/main/chemistry/pyproject.toml"]
        )
        member.upsert_sections()
        self.assertEqual(
            ["chemistry"], [s.path for s in member.declared_distributions()]
        )

    def test_a_pattern_declares_a_directory_of_distributions(self):
        """A monorepo says it in one line, resolved against the repository on every run."""
        member = self.member(
            [f"https://github.com/{OWNER}/{REPO}/blob/main/packages/*/pyproject.toml"]
        )
        tree = [
            "pyproject.toml",
            "packages/one/pyproject.toml",
            "packages/two/setup.cfg",
            "packages/two/pyproject.toml",
            "packages/three/README.md",
            "other/four/pyproject.toml",
        ]
        with patch.object(PythonData, "_request_tree", return_value=tree):
            declared = member.declared_distributions()
        self.assertEqual(["packages/one", "packages/two"], [s.path for s in declared])

    def test_a_pattern_does_not_claim_a_manifest_one_level_off(self):
        """`*` does not cross `/`, so the depth of the pattern is the depth it matches."""
        member = self.member(
            [f"https://github.com/{OWNER}/{REPO}/blob/main/packages/*/pyproject.toml"]
        )
        with patch.object(
            PythonData,
            "_request_tree",
            return_value=["packages/pyproject.toml", "packages/a/b/pyproject.toml"],
        ):
            self.assertEqual([], member.declared_distributions())

    def test_a_directory_added_later_is_picked_up(self):
        """Which is why the pattern is kept rather than expanded once at submission."""
        member = self.member(
            [f"https://github.com/{OWNER}/{REPO}/blob/main/packages/*/pyproject.toml"]
        )
        tree = ["packages/one/pyproject.toml"]
        with patch.object(PythonData, "_request_tree", side_effect=lambda: tree):
            self.assertEqual(1, len(member.declared_distributions()))
            tree.append("packages/two/pyproject.toml")
            self.assertEqual(2, len(member.declared_distributions()))

    def test_a_manifest_name_is_never_a_pattern(self):
        """The basename has to be a manifest, or the URL is not a manifest URL at all."""
        with self.assertRaises(EcosystemError):
            PythonData.from_url(
                URL(f"https://github.com/{OWNER}/{REPO}/blob/main/packages/*/*.toml")
            )

    def test_several_manifests_in_one_repository_are_each_declared(self):
        """A monorepo declares one distribution per directory, and each is read from its own
        declaration: before the manifests are read there is nothing to tell them apart.
        """
        member = self.member(
            [
                f"https://github.com/{OWNER}/{REPO}/blob/main/chemistry/pyproject.toml",
                f"https://github.com/{OWNER}/{REPO}/blob/main/physics/setup.cfg",
            ]
        )
        member.upsert_sections()
        self.assertEqual([], member.python)
        self.assertEqual(
            ["chemistry", "physics"],
            sorted(s.path for s in member.declared_distributions()),
        )

    def test_the_section_is_keyed_by_the_name_the_manifest_states(self):
        """Which is only known once the repository has been read."""
        member = self.member(
            [f"https://github.com/{OWNER}/{REPO}/blob/main/pyproject.toml"]
        )
        member.upsert_sections()
        with patch(
            "ecosystem.github_contents.request_json",
            side_effect=TestMemberUpdatePython.fake_request(),
        ):
            member.update_python()
        self.assertEqual(["banana-compiler"], package_names(member.python))

    def test_a_member_that_is_one_directory_reads_only_that_directory(self):
        """Two templates of one repository are two members, and neither of them is the
        distribution the repository root publishes: that one overwrote the other's page.
        """
        member = self.member([])
        member.github = GitHubData(
            owner=OWNER, repo=REPO, tree="main/chemistry/sqd_pcm"
        )
        self.assertEqual("chemistry/sqd_pcm", member.github.subdirectory)
        with patch(
            "ecosystem.github_contents.request_json",
            side_effect=TestMemberUpdatePython.fake_request(),
        ) as request:
            member.update_python()
        asked = [str(call.args[0]) for call in request.call_args_list]
        self.assertTrue(
            all("contents/chemistry/sqd_pcm/" in url for url in asked), asked
        )

    def test_a_stored_section_from_elsewhere_in_the_repository_is_dropped(self):
        """It describes the repository, which is somebody else's member"""
        member = self.member([])
        member.github = GitHubData(
            owner=OWNER, repo=REPO, tree="main/chemistry/sqd_pcm"
        )
        member.python = [
            PythonData(package_name="the-whole-repository", source=["pyproject.toml"])
        ]
        with patch(
            "ecosystem.github_contents.request_json",
            side_effect=lambda url, **kwargs: {"entries": []},
        ):
            member.update_python()
        self.assertEqual([], member.python)

    def test_a_branch_on_its_own_is_the_whole_repository(self):
        """`/tree/main` says which branch, not which directory"""
        self.assertIsNone(GitHubData(owner=OWNER, repo=REPO, tree="main").subdirectory)
        self.assertIsNone(GitHubData(owner=OWNER, repo=REPO).subdirectory)

    def test_a_registry_url_still_wins(self):
        """A published distribution is described by its registry section."""
        member = self.member(["https://pypi.org/project/banana-compiler/"])
        member.upsert_sections()
        self.assertEqual([], member.python)
        self.assertEqual(["banana-compiler"], package_names(member.pypi))
