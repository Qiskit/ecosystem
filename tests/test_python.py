"""Tests for ecosystem/python.py."""

from datetime import date
from unittest import TestCase
from unittest.mock import patch

from ecosystem.error_handling import EcosystemError
from ecosystem.github import GitHubData
from ecosystem.julia import JuliaData
from ecosystem.member import Member
from ecosystem.pypi import PyPIData
from ecosystem.python import PythonData, parse_setup_cfg, parse_setup_py
from ecosystem.request import URL

OWNER = "banana-org"
REPO = "banana-compiler"
CONTENTS = f"api.github.com/repos/{OWNER}/{REPO}/contents/"

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

# Qiskit releases, so that the compat fields do not need the network
QISKIT_VERSIONS = {
    "1.0.0": {"upload_at": date(2024, 2, 1)},
    "2.0.0": {"upload_at": date(2025, 4, 1)},
}


def listing(*names):
    """A contents-API directory listing holding `names` as files."""
    return {"entries": [{"name": name, "type": "file"} for name in names]}


class PythonDataTestCase(TestCase):
    """Base with the Qiskit release table stubbed out."""

    def setUp(self):
        super().setUp()
        patcher = patch.object(
            PythonData, "all_qiskit_versions", return_value=QISKIT_VERSIONS
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

        with patch("ecosystem.python.request_json", side_effect=fake_request):
            data = PythonData(owner=OWNER, repo=REPO)
            data.update_json()

        self.assertEqual(2, len(requested))
        self.assertTrue(requested[1].endswith("/pyproject.toml"))
        self.assertEqual("0.3.1", data.version)
        self.assertEqual(["pyproject.toml"], data.source)

    def test_directories_are_not_manifests(self):
        """A directory named `setup.py` would not be a manifest."""
        with patch(
            "ecosystem.python.request_json",
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

        with patch("ecosystem.python.request_json", side_effect=fake_request):
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
        with patch("ecosystem.python.request_json", side_effect=self.fake_request()):
            member.update_python()
        self.assertEqual(["banana-compiler"], list(member.python))
        self.assertEqual("0.3.1", member.python["banana-compiler"].version)

    def test_no_section_for_a_distribution_that_is_published(self):
        """The release describes it already, so a section would just duplicate it."""
        member = self.member(pypi={"banana-compiler": PyPIData("banana-compiler")})
        with patch("ecosystem.python.request_json", side_effect=self.fake_request()):
            member.update_python()
        self.assertEqual({}, member.python)

    def test_the_published_name_is_what_decides(self):
        """A repository can publish one distribution and declare another, unreleased
        one. Skipping on "publishes something" would lose the second."""
        member = self.member(pypi={"banana-cli": PyPIData("banana-cli")})
        with patch("ecosystem.python.request_json", side_effect=self.fake_request()):
            member.update_python()
        self.assertEqual(["banana-compiler"], list(member.python))

    def test_the_comparison_ignores_name_spelling(self):
        """`Banana_Compiler` in the manifest and `banana-compiler` on PyPI are one
        distribution, so the section is still not created."""
        member = self.member(pypi={"Banana_Compiler": PyPIData("Banana_Compiler")})
        with patch("ecosystem.python.request_json", side_effect=self.fake_request()):
            member.update_python()
        self.assertEqual({}, member.python)

    def test_a_julia_release_of_the_same_name_does_not_count(self):
        """Only PyPI is consulted: a Julia package is a different artifact in a
        different registry, and says nothing about whether `pip` can find this one."""
        member = self.member(julia={"banana-compiler": JuliaData("banana-compiler")})
        with patch("ecosystem.python.request_json", side_effect=self.fake_request()):
            member.update_python()
        self.assertEqual(["banana-compiler"], list(member.python))

    def test_an_existing_section_is_refreshed_even_when_published(self):
        """A section added on purpose keeps being updated, to cross-check the release."""
        member = self.member(
            pypi={"banana-compiler": PyPIData("banana-compiler")},
            python={"banana-compiler": PythonData(package_name="banana-compiler")},
        )
        with patch("ecosystem.python.request_json", side_effect=self.fake_request()):
            member.update_python()
        self.assertEqual("0.3.1", member.python["banana-compiler"].version)

    def test_section_is_rekeyed_when_the_distribution_is_renamed(self):
        """The key follows the name the repository declares now."""
        member = self.member(python={"old-name": PythonData(package_name="old-name")})
        with patch("ecosystem.python.request_json", side_effect=self.fake_request()):
            member.update_python()
        self.assertEqual(["banana-compiler"], list(member.python))

    def test_section_is_dropped_when_nothing_declares_a_distribution(self):
        """A repository that stopped being a Python package loses its section."""
        member = self.member(python={"banana-compiler": PythonData(package_name="b")})
        with patch("ecosystem.python.request_json", return_value=listing("README.md")):
            member.update_python()
        self.assertEqual({}, member.python)

    def test_a_member_without_a_github_section_is_skipped(self):
        """There is nothing to fetch from, so nothing is attempted."""
        member = Member(
            name="Banana Compiler",
            url=f"https://github.com/{OWNER}/{REPO}",
            uuid="banana-uuid-0000-0000-000000000000",
            maturity="experimental",
        )
        with patch("ecosystem.python.request_json") as request:
            member.update_python()
        self.assertEqual({}, member.python)
        request.assert_not_called()

    def test_the_declared_path_is_kept_across_updates(self):
        """`path` cannot be discovered, so a refresh must not lose it."""
        member = self.member(
            python={"banana-compiler": PythonData(path="packages/compiler")}
        )
        requested = []

        def request(url, **kwargs):
            requested.append(str(url))
            return self.fake_request()(url, **kwargs)

        with patch("ecosystem.python.request_json", side_effect=request):
            member.update_python()
        self.assertTrue(requested[0].endswith("/contents/packages/compiler/"))
        self.assertEqual("packages/compiler", member.python["banana-compiler"].path)

    def test_the_section_round_trips_through_from_dict(self):
        """A member read back from a toml file keeps its python section."""
        member = self.member()
        with patch("ecosystem.python.request_json", side_effect=self.fake_request()):
            member.update_python()
        restored = Member.from_dict(member.to_dict())
        self.assertEqual(
            member.python["banana-compiler"].to_dict(),
            restored.python["banana-compiler"].to_dict(),
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

    def test_the_key_stands_in_until_the_name_is_known(self):
        """The distribution name is inside the repository, not in the URL."""
        data = self.from_url(
            f"https://github.com/{OWNER}/Banana_Compiler/blob/main/pyproject.toml"
        )
        self.assertEqual("banana-compiler", data.key)


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

    def test_a_manifest_url_creates_the_section(self):
        """No fetching: the section is created empty and an updater fills it in."""
        member = self.member(
            [f"https://github.com/{OWNER}/{REPO}/blob/main/chemistry/pyproject.toml"]
        )
        member.upsert_sections()
        key = f"{REPO}-chemistry"
        self.assertEqual([key], list(member.python))
        self.assertEqual("chemistry", member.python[key].path)
        self.assertEqual([], member.packages)

    def test_several_manifests_in_one_repository_keep_their_own_section(self):
        """A monorepo declares one distribution per directory. The stand-in key has to
        tell them apart, or all but the last are lost before anything is fetched."""
        member = self.member(
            [
                f"https://github.com/{OWNER}/{REPO}/blob/main/hardware/pyproject.toml",
                f"https://github.com/{OWNER}/{REPO}/blob/main/packages/vision/setup.cfg",
                f"https://github.com/{OWNER}/{REPO}/blob/main/pyproject.toml",
            ]
        )
        member.upsert_sections()
        self.assertEqual(
            [f"{REPO}-hardware", f"{REPO}-packages-vision", REPO],
            list(member.python),
        )
        self.assertEqual(
            ["hardware", "packages/vision", None],
            [section.path for section in member.python.values()],
        )

    def test_the_section_is_rekeyed_by_the_first_update(self):
        """The repository name only stands in until a manifest states the real one."""
        member = self.member(
            [f"https://github.com/{OWNER}/{REPO}/blob/main/pyproject.toml"]
        )
        member.upsert_sections()
        with patch(
            "ecosystem.python.request_json",
            side_effect=TestMemberUpdatePython.fake_request(),
        ):
            member.update_python()
        self.assertEqual(["banana-compiler"], list(member.python))

    def test_a_registry_url_still_wins(self):
        """A published distribution is described by its registry section."""
        member = self.member(["https://pypi.org/project/banana-compiler/"])
        member.upsert_sections()
        self.assertEqual({}, member.python)
        self.assertEqual(["banana-compiler"], list(member.pypi))
