"""Tests for ecosystem/julia.py."""

from datetime import date
from unittest import TestCase
from unittest.mock import patch
from urllib.parse import urlparse

from ecosystem.error_handling import EcosystemError
from ecosystem.julia import JuliaData
from ecosystem.request import URL


class TestJuliaData(TestCase):
    """Tests for Julia project metadata."""

    @staticmethod
    def _mock_request_json(payloads):
        def request_json(url, **_kwargs):
            if url not in payloads:
                raise AssertionError(f"unexpected network request: {url}")
            payload = payloads[url]
            if isinstance(payload, Exception):
                raise payload
            return payload

        return request_json

    def test_from_url_accepts_juliahub_ui_url(self):
        """JuliaHub URLs include the registry and package name in the path."""
        data = JuliaData.from_url(
            urlparse("https://juliahub.com/ui/Packages/General/Flux")
        )

        self.assertEqual(data.package_name, "Flux")
        self.assertEqual(data.registry, "General")

    def test_from_url_accepts_juliapackages_url(self):
        """JuliaPackages URLs defer package-name parsing until update_json."""
        data = JuliaData.from_url(urlparse("https://juliapackages.com/p/flux"))

        self.assertEqual(data.juliapackages_url, "https://juliapackages.com/p/flux")
        self.assertIsNone(data.package_name)

    def test_from_url_returns_none_for_unrelated_host(self):
        """Unrecognized hosts are ignored by JuliaData."""
        self.assertIsNone(JuliaData.from_url(urlparse("https://example.com/Flux.jl")))

    def test_from_url_rejects_malformed_known_hosts(self):
        """Known Julia hosts must use the expected URL shape."""
        with self.assertRaises(EcosystemError):
            JuliaData.from_url(urlparse("https://juliahub.com/packages/Flux"))

        with self.assertRaises(EcosystemError):
            JuliaData.from_url(urlparse("https://juliapackages.com/package/flux"))

    def test_to_dict_reads_juliahub_json_and_filters_none_values(self):
        """JuliaHub JSON values are exposed through to_dict."""
        data = JuliaData(package_name="Flux")
        setattr(
            data,
            "_juliahub_json",
            {
                "version": "1.2.3",
                "license": "MIT",
                "homepage": "",
                "release_date": "Jan 2024",
                "uuid": "flux-uuid",
            },
        )

        self.assertEqual(
            data.to_dict(),
            {
                "package_name": "Flux",
                "registry": "General",
                "version": "1.2.3",
                "license": "MIT",
                "release_date": date(2024, 1, 1),
                "uuid": "flux-uuid",
            },
        )

    def test_juliahub_json_defaults_to_empty_dict(self):
        """juliahub_json hides the internal None state from callers."""
        self.assertEqual(JuliaData(package_name="Flux").juliahub_json, {})

    def test_get_juliahub_url_sets_url_when_probe_succeeds(self):
        """A successful JuliaHub probe stores the canonical UI URL."""
        data = JuliaData(package_name="Flux")
        url = "https://juliahub.com/ui/Packages/General/Flux"

        with patch(
            "ecosystem.julia.request_json",
            side_effect=self._mock_request_json({url: {}}),
        ) as request_json:
            data.get_juliahub_url()

        self.assertEqual([call.args[0] for call in request_json.call_args_list], [url])
        self.assertEqual(data.juliahub_url, URL(url))

    def test_get_juliahub_url_clears_url_when_probe_fails(self):
        """A failed JuliaHub probe leaves no stale URL."""
        data = JuliaData(package_name="Flux")
        url = "https://juliahub.com/ui/Packages/General/Flux"
        data.juliahub_url = URL(url)

        with patch(
            "ecosystem.julia.request_json",
            side_effect=self._mock_request_json(
                {url: EcosystemError("JuliaHub unavailable")}
            ),
        ) as request_json:
            data.get_juliahub_url()

        self.assertEqual([call.args[0] for call in request_json.call_args_list], [url])
        self.assertIsNone(data.juliahub_url)

    def test_get_general_registry_url_sets_url_for_matching_package(self):
        """General registry matches are converted to GitHub tree URLs."""
        data = JuliaData(package_name="Flux")
        registry = {"packages": {"flux-uuid": {"name": "Flux", "path": "F/Flux"}}}
        registry_url = (
            "https://raw.githubusercontent.com/JuliaRegistries/"
            "General/refs/heads/master/Registry.toml"
        )
        tree_url = "https://github.com/JuliaRegistries/General/tree/master/F/Flux"

        with patch(
            "ecosystem.julia.request_json",
            side_effect=self._mock_request_json({registry_url: registry, tree_url: {}}),
        ) as request_json:
            data.get_general_registry_url()

        self.assertEqual(
            [call.args[0] for call in request_json.call_args_list],
            [registry_url, tree_url],
        )
        self.assertEqual(data.general_registry_url, URL(tree_url))

    def test_get_general_registry_url_skips_non_general_registry(self):
        """Only the General Julia registry is currently resolved."""
        data = JuliaData(package_name="Flux", registry="Private")

        with patch("ecosystem.julia.request_json") as request_json:
            self.assertIsNone(data.get_general_registry_url())

        request_json.assert_not_called()
        self.assertIsNone(data.general_registry_url)

    def test_get_general_registry_url_ignores_missing_package(self):
        """Missing packages do not produce registry URLs."""
        data = JuliaData(package_name="Flux")
        registry = {"packages": {"other-uuid": {"name": "Other", "path": "O/Other"}}}
        registry_url = (
            "https://raw.githubusercontent.com/JuliaRegistries/"
            "General/refs/heads/master/Registry.toml"
        )

        with patch(
            "ecosystem.julia.request_json",
            side_effect=self._mock_request_json({registry_url: registry}),
        ) as request_json:
            self.assertIsNone(data.get_general_registry_url())

        self.assertEqual(
            [call.args[0] for call in request_json.call_args_list],
            [registry_url],
        )
        self.assertIsNone(data.general_registry_url)

    def test_estimated_unique_users_uses_download_stats_when_available(self):
        """Download statistics override constructor kwargs."""
        data = JuliaData(package_name="Flux", estimated_unique_users=1)

        self.assertEqual(data.estimated_unique_users, 1)

        setattr(data, "_package_requests_json", {"request_addrs": "42"})

        self.assertEqual(data.estimated_unique_users, 42)

    def test_update_json_populates_related_julia_metadata(self):
        """update_json combines JuliaPackages, JuliaHub, downloads, and registry data."""
        data = JuliaData(juliapackages_url="https://juliapackages.com/p/flux")
        registry = {"packages": {"flux-uuid": {"name": "Flux", "path": "F/Flux"}}}
        package_url = "https://juliapackages.com/p/flux"
        package_json_url = "juliahub.com/docs/General/Flux/stable/pkg.json"
        juliahub_url = "https://juliahub.com/ui/Packages/General/Flux"
        stats_url = (
            "https://julialang-logs.s3.amazonaws.com/public_outputs/"
            "current/package_requests.csv.gz"
        )
        registry_url = (
            "https://raw.githubusercontent.com/JuliaRegistries/"
            "General/refs/heads/master/Registry.toml"
        )
        tree_url = "https://github.com/JuliaRegistries/General/tree/master/F/Flux"

        with patch(
            "ecosystem.julia.request_json",
            side_effect=self._mock_request_json(
                {
                    package_url: {"package_name": "Flux"},
                    package_json_url: {"uuid": "flux-uuid", "version": "1.2.3"},
                    juliahub_url: {},
                    stats_url: {"request_addrs": "7"},
                    registry_url: registry,
                    tree_url: {},
                }
            ),
        ) as request_json:
            data.update_json()

        self.assertEqual(
            [call.args[0] for call in request_json.call_args_list],
            [
                package_url,
                package_json_url,
                juliahub_url,
                stats_url,
                registry_url,
                tree_url,
            ],
        )
        self.assertEqual(data.package_name, "Flux")
        self.assertEqual(data.version, "1.2.3")
        self.assertEqual(data.estimated_unique_users, 7)
        self.assertEqual(data.juliahub_url, URL(juliahub_url))
        self.assertEqual(data.general_registry_url, URL(tree_url))
