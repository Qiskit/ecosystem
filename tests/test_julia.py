"""Tests for ecosystem/julia.py."""

from datetime import date
from unittest import TestCase
from unittest.mock import patch
from urllib.parse import urlparse

from ecosystem.error_handling import EcosystemError
from ecosystem.julia import JuliaData
from ecosystem.request import URL

PACKAGE_NAME = "BananaCompiler"
PACKAGE_SLUG = "banana-compiler"
PACKAGE_UUID = "banana-compiler-uuid"
PACKAGE_PATH = "B/BananaCompiler"
JULIAPACKAGES_URL = f"https://juliapackages.com/p/{PACKAGE_SLUG}"
PACKAGE_JSON_URL = f"juliahub.com/docs/General/{PACKAGE_NAME}/stable/pkg.json"
JULIAHUB_URL = f"https://juliahub.com/ui/Packages/General/{PACKAGE_NAME}"
STATS_URL = (
    "https://julialang-logs.s3.amazonaws.com/public_outputs/"
    "current/package_requests.csv.gz"
)
REGISTRY_URL = (
    "https://raw.githubusercontent.com/JuliaRegistries/"
    "General/refs/heads/master/Registry.toml"
)
TREE_URL = f"https://github.com/JuliaRegistries/General/tree/master/{PACKAGE_PATH}"


class TestJuliaData(TestCase):
    """Tests for Julia project metadata."""

    def _mock_request_json(self, *responses):
        pending = list(responses)

        def request_json(url, **_kwargs):
            if not pending:
                raise AssertionError(f"unexpected network request: {url}")
            expected_url, payload = pending.pop(0)
            self.assertEqual(expected_url, url)
            if isinstance(payload, Exception):
                raise payload
            return payload

        return request_json

    @staticmethod
    def _registry_payload(name=PACKAGE_NAME, path=PACKAGE_PATH):
        return {"packages": {PACKAGE_UUID: {"name": name, "path": path}}}

    def test_from_url_accepts_juliahub_ui_url(self):
        """JuliaHub URLs include the registry and package name in the path."""
        data = JuliaData.from_url(urlparse(JULIAHUB_URL))

        self.assertEqual(data.package_name, PACKAGE_NAME)
        self.assertEqual(data.registry, "General")

    def test_from_url_accepts_juliapackages_url(self):
        """JuliaPackages URLs defer package-name parsing until update_json."""
        data = JuliaData.from_url(urlparse(JULIAPACKAGES_URL))

        self.assertEqual(data.juliapackages_url, JULIAPACKAGES_URL)
        self.assertIsNone(data.package_name)

    def test_from_url_returns_none_for_unrelated_host(self):
        """Unrecognized hosts are ignored by JuliaData."""
        self.assertIsNone(
            JuliaData.from_url(urlparse(f"https://example.com/{PACKAGE_NAME}.jl"))
        )

    def test_from_url_rejects_malformed_known_hosts(self):
        """Known Julia hosts must use the expected URL shape."""
        with self.assertRaises(EcosystemError):
            JuliaData.from_url(
                urlparse(f"https://juliahub.com/packages/{PACKAGE_NAME}")
            )

        with self.assertRaises(EcosystemError):
            JuliaData.from_url(
                urlparse(f"https://juliapackages.com/package/{PACKAGE_SLUG}")
            )

    def test_to_dict_reads_fetched_json_and_filters_none_values(self):
        """JuliaHub JSON values fetched by update_json are exposed through to_dict."""
        data = JuliaData(package_name=PACKAGE_NAME)

        with patch(
            "ecosystem.julia.request_json",
            side_effect=self._mock_request_json(
                (
                    PACKAGE_JSON_URL,
                    {
                        "version": "1.2.3",
                        "license": "MIT",
                        "homepage": "",
                        "release_date": "Jan 2024",
                        "uuid": PACKAGE_UUID,
                    },
                ),
                (JULIAHUB_URL, {}),
                (STATS_URL, {"request_addrs": "42"}),
                (REGISTRY_URL, self._registry_payload()),
                (TREE_URL, {}),
            ),
        ):
            data.update_json()

        self.assertEqual(
            data.to_dict(),
            {
                "package_name": PACKAGE_NAME,
                "registry": "General",
                "version": "1.2.3",
                "license": "MIT",
                "release_date": date(2024, 1, 1),
                "juliahub_url": URL(JULIAHUB_URL),
                "general_registry_url": URL(TREE_URL),
                "uuid": PACKAGE_UUID,
                "estimated_unique_users": 42,
            },
        )

    def test_juliahub_json_defaults_to_empty_dict(self):
        """juliahub_json hides the internal None state from callers."""
        self.assertEqual(JuliaData(package_name=PACKAGE_NAME).juliahub_json, {})

    def test_get_juliahub_url_sets_url_when_probe_succeeds(self):
        """A successful JuliaHub probe stores the canonical UI URL."""
        data = JuliaData(package_name=PACKAGE_NAME)

        with patch(
            "ecosystem.julia.request_json",
            side_effect=self._mock_request_json((JULIAHUB_URL, {})),
        ) as request_json:
            data.get_juliahub_url()

        self.assertEqual(
            [call.args[0] for call in request_json.call_args_list], [JULIAHUB_URL]
        )
        self.assertEqual(data.juliahub_url, URL(JULIAHUB_URL))

    def test_get_juliahub_url_clears_url_when_probe_fails(self):
        """A failed JuliaHub probe leaves no stale URL."""
        data = JuliaData(package_name=PACKAGE_NAME)
        data.juliahub_url = URL(JULIAHUB_URL)

        with patch(
            "ecosystem.julia.request_json",
            side_effect=self._mock_request_json(
                (JULIAHUB_URL, EcosystemError("JuliaHub unavailable"))
            ),
        ) as request_json:
            data.get_juliahub_url()

        self.assertEqual(
            [call.args[0] for call in request_json.call_args_list], [JULIAHUB_URL]
        )
        self.assertIsNone(data.juliahub_url)

    def test_get_general_registry_url_sets_url_for_matching_package(self):
        """General registry matches are converted to GitHub tree URLs."""
        data = JuliaData(package_name=PACKAGE_NAME)

        with patch(
            "ecosystem.julia.request_json",
            side_effect=self._mock_request_json(
                (REGISTRY_URL, self._registry_payload()),
                (TREE_URL, {}),
            ),
        ) as request_json:
            data.get_general_registry_url()

        self.assertEqual(
            [call.args[0] for call in request_json.call_args_list],
            [REGISTRY_URL, TREE_URL],
        )
        self.assertEqual(data.general_registry_url, URL(TREE_URL))

    def test_get_general_registry_url_skips_non_general_registry(self):
        """Only the General Julia registry is currently resolved."""
        data = JuliaData(package_name=PACKAGE_NAME, registry="Private")

        with patch("ecosystem.julia.request_json") as request_json:
            self.assertIsNone(data.get_general_registry_url())

        request_json.assert_not_called()
        self.assertIsNone(data.general_registry_url)

    def test_get_general_registry_url_ignores_missing_package(self):
        """Missing packages do not produce registry URLs."""
        data = JuliaData(package_name=PACKAGE_NAME)
        registry = {"packages": {"other-uuid": {"name": "Other", "path": "O/Other"}}}

        with patch(
            "ecosystem.julia.request_json",
            side_effect=self._mock_request_json((REGISTRY_URL, registry)),
        ) as request_json:
            self.assertIsNone(data.get_general_registry_url())

        self.assertEqual(
            [call.args[0] for call in request_json.call_args_list],
            [REGISTRY_URL],
        )
        self.assertIsNone(data.general_registry_url)

    def test_estimated_unique_users_uses_download_stats_when_available(self):
        """Download statistics override constructor kwargs."""
        data = JuliaData(package_name=PACKAGE_NAME, estimated_unique_users=1)

        self.assertEqual(data.estimated_unique_users, 1)

        with patch(
            "ecosystem.julia.request_json",
            side_effect=self._mock_request_json(
                (PACKAGE_JSON_URL, {"uuid": PACKAGE_UUID}),
                (JULIAHUB_URL, {}),
                (STATS_URL, {"request_addrs": "42"}),
                (REGISTRY_URL, self._registry_payload()),
                (TREE_URL, {}),
            ),
        ):
            data.update_json()

        self.assertEqual(data.estimated_unique_users, 42)

    def test_update_json_populates_related_julia_metadata(self):
        """update_json combines JuliaPackages, JuliaHub, downloads, and registry data."""
        data = JuliaData(juliapackages_url=JULIAPACKAGES_URL)

        with patch(
            "ecosystem.julia.request_json",
            side_effect=self._mock_request_json(
                (JULIAPACKAGES_URL, {"package_name": PACKAGE_NAME}),
                (PACKAGE_JSON_URL, {"uuid": PACKAGE_UUID, "version": "1.2.3"}),
                (JULIAHUB_URL, {}),
                (STATS_URL, {"request_addrs": "7"}),
                (REGISTRY_URL, self._registry_payload()),
                (TREE_URL, {}),
            ),
        ) as request_json:
            data.update_json()

        self.assertEqual(
            [call.args[0] for call in request_json.call_args_list],
            [
                JULIAPACKAGES_URL,
                PACKAGE_JSON_URL,
                JULIAHUB_URL,
                STATS_URL,
                REGISTRY_URL,
                TREE_URL,
            ],
        )
        self.assertEqual(data.package_name, PACKAGE_NAME)
        self.assertEqual(data.version, "1.2.3")
        self.assertEqual(data.estimated_unique_users, 7)
        self.assertEqual(data.juliahub_url, URL(JULIAHUB_URL))
        self.assertEqual(data.general_registry_url, URL(TREE_URL))
