"""Tests for ecosystem/pypi.py."""

from datetime import datetime
import json
import tempfile
import unittest
from unittest.mock import mock_open, patch

from ecosystem.error_handling import EcosystemError
from ecosystem.pypi import PyPIData
from ecosystem.request import URL


class TestPyPIData(unittest.TestCase):  # pylint: disable=too-many-public-methods
    """Tests for PyPIData."""

    def _update_with_pypi_json(self, pypi_data, pypi_payload):
        """Populate a PyPIData object through its public update flow."""
        with patch("ecosystem.pypi.request_json", return_value=pypi_payload):
            with patch.object(PyPIData, "request_pypistats", return_value={}):
                pypi_data.update_json()

    def test_package_names_are_canonicalized_and_serialized(self):
        """Package names are normalized and dicts omit missing values."""
        pypi_data = PyPIData(
            "banana-compiler",
            version="1.0.0",
            requires_qiskit=">=1,<2",
            last_month_downloads=123,
        )
        qiskit_versions = {
            "1.0.0": {"upload_at": datetime(2024, 1, 1)},
            "2.0.0": {"upload_at": datetime(2025, 1, 1)},
        }

        self.assertEqual("banana-compiler", pypi_data.package_name)
        with patch.object(
            PyPIData, "all_qiskit_versions", return_value=qiskit_versions
        ):
            self.assertDictEqual(
                {
                    "package_name": "banana-compiler",
                    "version": "1.0.0",
                    "requires_qiskit": ">=1,<2",
                    "compatible_with_qiskit_v1": True,
                    "compatible_with_qiskit_v2": False,
                    "highest_supported_qiskit_release_date": datetime(2024, 1, 1),
                    "highest_supported_qiskit_version": "1.0.0",
                    "last_month_downloads": 123,
                },
                pypi_data.to_dict(),
            )
            self.assertIsInstance(repr(pypi_data), str)

    def test_package_name_validation(self):
        """Invalid package names are rejected by canonicalization."""
        with self.assertRaises(ValueError):
            PyPIData("invalid package name")

    def test_from_url_accepts_pypi_project_urls(self):
        """PyPI project URLs are converted to data objects."""
        pypi_data = PyPIData.from_url(URL("https://pypi.org/project/banana-compiler/"))

        self.assertEqual("banana-compiler", pypi_data.package_name)

    def test_from_url_ignores_non_pypi_urls(self):
        """Non-PyPI URLs are ignored."""
        self.assertIsNone(
            PyPIData.from_url(URL("https://example.com/project/banana-compiler/"))
        )

    def test_from_url_rejects_invalid_pypi_urls(self):
        """Malformed PyPI project URLs raise an ecosystem error."""
        with self.assertLogs("ecosystem", level="ERROR"):
            with self.assertRaises(EcosystemError):
                PyPIData.from_url(URL("https://pypi.org/simple/banana-compiler/"))

    def test_update_json_fetches_pypi_and_pypistats_data(self):
        """update_json stores PyPI and stats payloads."""
        pypi_payload = {"info": {"version": "1.2.3"}}
        stats_payload = {"recent_downloads": {"last_month": 10}}
        pypi_data = PyPIData("banana-compiler")

        with patch("ecosystem.pypi.request_json", return_value=pypi_payload) as request:
            with patch.object(
                PyPIData, "request_pypistats", return_value=stats_payload
            ) as request_stats:
                pypi_data.update_json()

        request.assert_called_once_with("pypi.org/pypi/banana-compiler/json")
        request_stats.assert_called_once_with()
        self.assertEqual(pypi_payload, pypi_data.pypi_json)
        self.assertEqual(10, pypi_data.last_month_downloads)

    def test_update_json_ignores_pypi_fetch_errors(self):
        """update_json tolerates unavailable PyPI package JSON."""
        pypi_data = PyPIData("banana-compiler")

        def raise_error(*_args, **_kwargs):
            raise EcosystemError("boom")

        with patch("ecosystem.pypi.request_json", side_effect=raise_error):
            with patch.object(PyPIData, "request_pypistats", return_value={}):
                with self.assertLogs("ecosystem", level="ERROR"):
                    pypi_data.update_json()

        self.assertFalse(pypi_data.pypi_json)

    def test_getattr_reads_aliases_from_pypi_json(self):
        """Aliased attributes are read from fetched PyPI JSON."""
        pypi_data = PyPIData("banana-compiler")
        self._update_with_pypi_json(
            pypi_data,
            {
                "info": {
                    "version": "1.2.3",
                    "package_url": "https://pypi.org/project/banana-compiler/",
                    "license_expression": "Apache-2.0",
                }
            },
        )

        self.assertEqual("1.2.3", pypi_data.version)
        self.assertEqual("https://pypi.org/project/banana-compiler/", pypi_data.url)
        self.assertEqual("Apache-2.0", pypi_data.license)
        with self.assertRaises(AttributeError):
            getattr(pypi_data, "$.missing")

    def test_getattr_applies_json_type_and_reduce_hooks(self):
        """Custom JSONPath hooks can convert and combine multiple JSON values."""
        pypi_data = PyPIData("banana-compiler")
        self._update_with_pypi_json(pypi_data, {"values": ["1", "2", "3"]})
        PyPIData.json_types["$.values.*"] = int
        PyPIData.reduce["$.values.*"] = lambda left, right: left + right

        try:
            self.assertEqual(6, getattr(pypi_data, "$.values.*"))
        finally:
            del PyPIData.json_types["$.values.*"]
            del PyPIData.reduce["$.values.*"]

    def test_getattr_reads_kwargs_without_pypi_json(self):
        """Keyword arguments are the fallback data source."""
        pypi_data = PyPIData("banana-compiler", version="1.2.3")

        self.assertEqual("1.2.3", pypi_data.version)
        with self.assertRaises(AttributeError):
            getattr(pypi_data, "$.missing")

    def test_last_release_date_prefers_explicit_value(self):
        """Explicit release dates are returned without inspecting JSON."""
        release_date = datetime(2024, 1, 1)
        pypi_data = PyPIData("banana-compiler", last_release_date=release_date)

        self.assertEqual(release_date, pypi_data.last_release_date)

    def test_last_release_date_uses_latest_file_upload(self):
        """The most recent upload for the current version is used."""
        pypi_data = PyPIData("banana-compiler")
        self._update_with_pypi_json(
            pypi_data,
            {
                "info": {"version": "1.2.3"},
                "releases": {
                    "1.2.3": [
                        {"upload_time": "2024-01-01T01:00:00"},
                        {"upload_time": "2024-02-03T04:05:06"},
                    ]
                },
            },
        )

        self.assertEqual(datetime(2024, 2, 3, 4, 5, 6), pypi_data.last_release_date)

    def test_last_release_date_returns_none_without_release_files(self):
        """Missing current release file metadata yields no release date."""
        pypi_data = PyPIData("banana-compiler")
        self._update_with_pypi_json(
            pypi_data, {"info": {"version": "1.2.3"}, "releases": {}}
        )

        self.assertIsNone(pypi_data.last_release_date)

    def test_requires_qiskit_reads_dependency_specifier(self):
        """requires_dist is parsed to find the qiskit specifier."""
        pypi_data = PyPIData("banana-compiler")
        self._update_with_pypi_json(
            pypi_data,
            {
                "info": {
                    "requires_dist": ["numpy>=2", "qiskit>=1,<3; python_version>'3'"]
                }
            },
        )

        self.assertEqual("<3,>=1", pypi_data.requires_qiskit)

    def test_requires_qiskit_forces_empty_specifier(self):
        """A bare qiskit dependency is treated as qiskit>=0."""
        pypi_data = PyPIData("banana-compiler")
        self._update_with_pypi_json(pypi_data, {"info": {"requires_dist": ["qiskit"]}})

        with self.assertLogs("ecosystem", level="WARNING"):
            self.assertEqual(">=0", pypi_data.requires_qiskit)

    def test_requires_qiskit_returns_none_when_absent(self):
        """Packages without a qiskit dependency return None."""
        pypi_data = PyPIData("banana-compiler")
        self._update_with_pypi_json(
            pypi_data, {"info": {"requires_dist": ["numpy>=2"]}}
        )

        self.assertIsNone(pypi_data.requires_qiskit)

    def test_qiskit_compatibility_and_highest_supported_version(self):
        """Compatibility helpers inspect available Qiskit releases."""
        pypi_data = PyPIData("banana-compiler", requires_qiskit=">=1,<2")
        qiskit_versions = {
            "0.45.0": {"upload_at": datetime(2023, 1, 1)},
            "1.0.0": {"upload_at": datetime(2024, 1, 1)},
            "1.2.0": {"upload_at": datetime(2024, 5, 1)},
            "2.0.0": {"upload_at": datetime(2025, 1, 1)},
        }

        with patch.object(
            PyPIData, "all_qiskit_versions", return_value=qiskit_versions
        ):
            self.assertTrue(pypi_data.compatible_with_qiskit_v1)
            self.assertFalse(pypi_data.compatible_with_qiskit_v2)
            self.assertEqual("1.2.0", pypi_data.highest_supported_qiskit_version)
            self.assertEqual(
                datetime(2024, 5, 1), pypi_data.highest_supported_qiskit_release_date
            )
            self.assertEqual(
                ("1.2.0", datetime(2024, 5, 1)),
                pypi_data.highest_supported_qiskit_version_and_release_date,
            )

    def test_qiskit_compatibility_returns_none_without_requirement(self):
        """Compatibility is unknown when no qiskit requirement exists."""
        pypi_data = PyPIData("banana-compiler")

        self.assertIsNone(pypi_data.compatible_with_qiskit(1))
        self.assertIsNone(pypi_data.highest_supported_qiskit_version)
        self.assertIsNone(pypi_data.highest_supported_qiskit_release_date)
        self.assertIsNone(pypi_data.highest_supported_qiskit_version_and_release_date)

    def test_highest_supported_version_returns_none_without_matching_version(self):
        """No supported release yields no highest supported version/date tuple."""
        pypi_data = PyPIData("banana-compiler", requires_qiskit=">=3")
        qiskit_versions = {
            "1.0.0": {"upload_at": datetime(2024, 1, 1)},
            "2.0.0": {"upload_at": datetime(2025, 1, 1)},
        }

        with patch.object(
            PyPIData, "all_qiskit_versions", return_value=qiskit_versions
        ):
            self.assertIsNone(
                pypi_data.highest_supported_qiskit_version_and_release_date
            )

    def test_all_qiskit_versions_loads_cached_file(self):
        """Qiskit release metadata is read from the package cache file."""
        pypi_data = PyPIData("banana-compiler")
        cache_content = json.dumps({"1.0.0": {"upload_at": "2024-01-01T00:00:00"}})

        with patch("ecosystem.pypi.path.dirname", return_value="/cache"):
            with patch("builtins.open", mock_open(read_data=cache_content)):
                versions = pypi_data.all_qiskit_versions()

        self.assertEqual({"1.0.0": {"upload_at": datetime(2024, 1, 1)}}, versions)

    def test_all_qiskit_versions_fetches_and_writes_when_forced(self):
        """Forced updates fetch Qiskit releases from PyPI and cache them."""
        pypi_data = PyPIData("banana-compiler")
        qiskit_payload = {
            "releases": {
                "1.0.0": [
                    {"upload_time_iso_8601": "2024-01-01T00:00:00"},
                    {"upload_time_iso_8601": "2024-01-02T00:00:00"},
                ],
                "2.0.0": [{"upload_time_iso_8601": "2025-01-01T00:00:00"}],
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("ecosystem.pypi.path.dirname", return_value=tmpdir):
                with patch("ecosystem.pypi.request_json", return_value=qiskit_payload):
                    versions = pypi_data.all_qiskit_versions(force_update=True)
                with open(
                    f"{tmpdir}/all_qiskit_versions.json", encoding="utf8"
                ) as file:
                    cached_versions = json.load(file)

        self.assertEqual(datetime(2024, 1, 2), versions["1.0.0"]["upload_at"])
        self.assertEqual("2024-01-02 00:00:00", cached_versions["1.0.0"]["upload_at"])

    def test_all_qiskit_versions_fetches_when_cache_missing(self):
        """A missing cache file triggers a PyPI refresh."""
        pypi_data = PyPIData("banana-compiler")
        qiskit_payload = {
            "releases": {"1.0.0": [{"upload_time_iso_8601": "2024-01-01T00:00:00"}]}
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("ecosystem.pypi.path.dirname", return_value=tmpdir):
                with patch("ecosystem.pypi.request_json", return_value=qiskit_payload):
                    with self.assertLogs("ecosystem", level="WARNING"):
                        versions = pypi_data.all_qiskit_versions()

        self.assertEqual(datetime(2024, 1, 1), versions["1.0.0"]["upload_at"])

    def test_all_qiskit_versions_rejects_releases_without_dates(self):
        """Qiskit releases without upload dates are treated as invalid."""
        pypi_data = PyPIData("banana-compiler")
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("ecosystem.pypi.path.dirname", return_value=tmpdir):
                with patch(
                    "ecosystem.pypi.request_json",
                    return_value={"releases": {"1.0.0": []}},
                ):
                    with self.assertLogs("ecosystem", level="ERROR"):
                        with self.assertRaises(EcosystemError):
                            pypi_data.all_qiskit_versions(force_update=True)

    def test_request_pypistats_combines_recent_and_overall_data(self):
        """PyPIStats recent and overall responses are normalized."""
        pypi_data = PyPIData("banana-compiler")
        recent = {"type": "recent_downloads", "data": {"last_month": 42}}
        overall = {
            "type": "overall_downloads",
            "data": [
                {"category": "with_mirrors", "downloads": 10},
                {"category": "with_mirrors", "downloads": 11},
                {"category": "without_mirrors", "downloads": 7},
                {"category": "without_mirrors", "downloads": 8},
            ],
        }

        with patch(
            "ecosystem.pypi.request_json", side_effect=[recent, overall]
        ) as request:
            stats = pypi_data.request_pypistats()

        self.assertEqual(
            {
                "recent_downloads": {"last_month": 42},
                "overall_downloads": {"with_mirrors": 21, "without_mirrors": 15},
            },
            stats,
        )
        self.assertEqual(
            [
                "https://pypistats.org/api/packages/banana-compiler/recent",
                "https://pypistats.org/api/packages/banana-compiler/overall",
            ],
            [call.args[0] for call in request.call_args_list],
        )

    def test_request_pypistats_returns_partial_data_for_missing_package(self):
        """A PyPIStats 404 stops fetching and returns data collected so far."""
        pypi_data = PyPIData("banana-compiler")
        recent = {"type": "recent_downloads", "data": {"last_month": 42}}

        def missing_package(*_args, **_kwargs):
            if missing_package.calls == 0:
                missing_package.calls += 1
                return recent
            raise EcosystemError("Bad response: Not Found (404)")

        missing_package.calls = 0

        with patch("ecosystem.pypi.request_json", side_effect=missing_package):
            with self.assertLogs("ecosystem", level="ERROR"):
                self.assertEqual(
                    {"recent_downloads": {"last_month": 42}},
                    pypi_data.request_pypistats(),
                )

    def test_request_pypistats_reraises_non_404_errors(self):
        """Unexpected PyPIStats errors are re-raised."""
        pypi_data = PyPIData("banana-compiler")

        def raise_error(*_args, **_kwargs):
            raise EcosystemError("rate limited")

        with patch("ecosystem.pypi.request_json", side_effect=raise_error):
            with self.assertLogs("ecosystem", level="ERROR"):
                with self.assertRaises(EcosystemError):
                    pypi_data.request_pypistats()

    def test_download_properties_fall_back_to_kwargs(self):
        """Download properties use kwargs until stats JSON has been fetched."""
        pypi_data = PyPIData(
            "banana-compiler", last_month_downloads=1, last_180_days_downloads=2
        )

        self.assertEqual(1, pypi_data.last_month_downloads)
        self.assertEqual(2, pypi_data.last_180_days_downloads)

    def test_download_properties_read_pypistats_json(self):
        """Download properties read normalized PyPIStats JSON."""
        pypi_data = PyPIData("banana-compiler")
        stats_payload = {
            "recent_downloads": {"last_month": 3},
            "overall_downloads": {"without_mirrors": 4},
        }

        with patch("ecosystem.pypi.request_json", return_value={}):
            with patch.object(
                PyPIData, "request_pypistats", return_value=stats_payload
            ):
                pypi_data.update_json()

        self.assertEqual(3, pypi_data.last_month_downloads)
        self.assertEqual(4, pypi_data.last_180_days_downloads)
