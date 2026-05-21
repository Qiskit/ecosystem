"""Badge section."""

from dataclasses import dataclass
from typing import Optional

from .error_handling import EcosystemError, logger
from .request import URL, request_json
from .serializable import JsonSerializable


@dataclass
class BadgeData(JsonSerializable):
    """
    The Badge data related to a project, based on
    https://img.shields.io/badges/endpoint-badge
    """

    # pylint: disable=invalid-name
    url: Optional[str | URL] = None  # the bitly link to the badge
    style: Optional[str] = None  # default: "flat"
    schemaVersion: Optional[int] = None
    label: Optional[str] = None
    message: Optional[str] = None
    color: Optional[str] = None
    labelColor: Optional[str] = None
    isError: Optional[str] = None
    logoColor: Optional[str] = None
    logoSize: Optional[str] = None

    def __post_init__(self):
        if self.url:
            self.url = self.url if isinstance(self.url, URL) else URL(self.url)
        if self.style:
            if self.style not in [
                "flat",
                "flat-square",
                "plastic",
                "for-the-badge",
                "social",
            ]:
                raise EcosystemError("Entry badge.style not valid")
        else:
            self.style = "flat"

    def update_url(self, name, short_uuid):
        """If not there yet, creates a new Bitly link for the badge"""
        short_url = f"https://qisk.it/e-{short_uuid}"

        qisk_dot_it_link_check = request_json(
            short_url,
            parser=lambda x: {
                "exists": x.startswith("<svg xmlns") and x.endswith("</svg>")
            },
        )
        if qisk_dot_it_link_check["exists"]:
            self.url = short_url
        else:
            self.url = BadgeData.create_link(name, short_uuid)

    @staticmethod
    def create_link(name, short_uuid):
        long_url = (
            "https://img.shields.io/endpoint?url="
            f"https://qiskit.github.io/ecosystem/b/{short_uuid}"
        )
        keyword = f"e-{short_uuid}"
        data = {
            "long_url": long_url,
            "domain": "qisk.it",
            "keyword": keyword,
            "group_guid": "Bj9rgMHKfxH",
            "title": f'Qiskit ecosystem "{name}" badge',
            "tags": ["qiskit ecosystem badge", "permanent _do NOT remove_"],
        }
        try:
            response = request_json("https://api-ssl.bitly.com/v4/bitlinks", post=data)
        except EcosystemError as err:
            if "Bad Request (400)" in err.message:
                logger.info(
                    "Bitly creation failed: %s -> %s ", f"qisk.it/{keyword}", long_url
                )
                return None  # Sometimes, bitly errors 400 for some server-side reason
            raise err
        logger.info(
            "Bitly short link created: %s -> %s ", f"qisk.it/{keyword}", long_url
        )
        return response["link"]
