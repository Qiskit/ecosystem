# This code is part of Qiskit.
#
# (C) Copyright IBM 2023.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at https://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


"""
Cards for mkdocs grid https://squidfunk.github.io/mkdocs-material/reference/grids/
"""

from dataclasses import dataclass
from typing import Optional

from ecosystem.member import Member
from ecosystem.classifications import ClassificationsToml


@dataclass
class Card:
    """Base class for cards"""

    title: Optional[str] = None
    title_icon: Optional[str] = None
    title_annotation: Optional[str] = None
    body_lines: Optional[list[str]] = None

    def title_lines(self):
        """Lines with titles"""
        full_title = "-   "
        if not self.title:
            return [full_title, ""]

        if self.title_icon:
            full_title += self.title_icon + " "
        full_title += self.title
        annotation_lines = []
        if self.title_annotation:
            full_title += " (1)"
            annotation_lines = [
                "    { .annotate }",
                "",
                f"    1.  {self.title_annotation}",
                "",
            ]

        return (
            [full_title]
            + annotation_lines
            + [
                "",
                "    ---",
                "",
            ]
        )

    def generate(self):
        """Generates the text for the card by combining lines"""
        return self.title_lines() + [f"    {l}" for l in self.body_lines]

    def bullet(self, icon, value, annotation=None):
        """
        Single value bullet, wiht a single annotation (optional)
        Args:
            icon:
            value:
            annotation:

        Returns:
            list: Lines with the bullet
        """
        entry = ""
        if icon:
            entry += f"{icon} "
        entry += value
        annotation_lines = []
        if annotation:
            entry += "(1)"
            annotation_lines += [
                "{ .annotate }",
                "",
                f"1.  {annotation}",
                "",
            ]
        return [entry] + annotation_lines

    def multi_bullet(self, icon, key, values, annotations):
        """
        A key -> values bullet. Each value with an optional annotation
        Args:
            icon:
            key:
            values:
            annotations: Same lenght as values. Use None to skip

        Returns:
            list: Lines with the bullet
        """
        ret = self.bullet(icon, key)
        annotation_lines = []
        for index, value_annotation in enumerate(zip(values, annotations), start=1):
            value, annotation = value_annotation
            if annotation is None:
                continue
            ret[0] += f" {value}({index})"
            annotation_lines.append(f"{index}.  {annotation}")
        if annotation_lines:
            ret += ["{ .annotate }", ""]
            ret += annotation_lines
        ret.append("")
        return ret


class ProjectSummaryCard(Card):
    """Project card, with classifications"""

    def __init__(
        self,
        licence=None,
        interfaces=None,
        category=None,
        labels=None,
        pattern_steps=None,
        ibm_maintained=None,
        status=None,
        maturity=None,
    ):
        self.license = licence
        self.interfaces = interfaces
        self.category = category
        self.labels = labels
        self.pattern_steps = pattern_steps
        self.ibm_maintained = ibm_maintained
        self.status = status
        self.maturity = maturity
        self.classifications = ClassificationsToml()

        super().__init__(
            self.status_title,
            self.status_icon,
            self.status_annotation,
            self.classifications_lines,
        )

    @classmethod
    def from_project(cls, project: Member):
        """Create a card from a Member object"""
        return ProjectSummaryCard(
            licence=project.license,
            status=project.status,
            maturity=project.maturity,
            interfaces=project.interfaces,
            category=project.category,
            labels=project.labels,
            pattern_steps=project.pattern_steps,
            ibm_maintained=project.ibm_maintained,
        )

    @property
    def status_title(self):
        """Title with memmber.status"""
        match self.status:
            case "Qiskit Project":
                return (
                    "**Qiskit Project**{{style='font-size: 1.25em;' "
                    f"title='{self.classifications.status_descriptions['Qiskit Project']}'}}"
                )
            case "Alumni":
                return (
                    "**Alumni project**{{style='font-size: 1.25em;' "
                    f"title='{self.classifications.status_descriptions['Alumni']}'}}"
                )
            case "Under revision":
                return (
                    "**Project under revision**{{style='font-size: 1.25em;' "
                    f"title='{self.classifications.status_descriptions['Under revision']}'}}"
                )
            case _:
                return (
                    "**Qiskit Ecosystem Member**{{style='font-size: 1.25em;' "
                    f"title='{self.classifications.status_descriptions['Member']}'}}"
                )

    @property
    def status_icon(self):
        """Icon for title"""
        match self.status:
            case "Qiskit Project":
                return ":simple-qiskit:"
            case "Alumni":
                return ":material-account-remove:"
            case "Under revision":
                return ":material-account-alert:"
            case _:
                return ""

    @property
    def status_annotation(self):
        """Annotation for title"""
        match self.status:
            case "Qiskit Project":
                return "[All the Qiskit Projects](../status/#qiskit-project)"
            case "Alumni":
                return "[All the Alumni projects](../status/#alumni)"
            case "Under revision":
                return "[All the projects under revision](../status/#under-revision)"
            case _:
                return "[All the regular Members](../status/#regular-members)"

    @property
    def classifications_lines(self):
        """All the bullets inthe main card"""
        ret = []
        ret += self.maturity_lines()
        ret += self.license_lines()
        ret += self.interfaces_lines()
        ret += self.category_lines()
        ret += self.labels_lines()
        ret += self.pattern_steps_lines()
        ret += self.ibm_maintained_lines()
        return ret

    def maturity_lines(self):
        """Bullet with member.maturity"""
        ret = []
        if self.status == "Alumni":
            return ret
        icons = {
            "production-ready": ":material-check-outline:",
            "bugfixing only": ":material-bug-check:",
            "as-is": ":material-image-broken-variant:",
            "deprecated": ":fontawesome-solid-exclamation-triangle:",
            "experimental": ":material-flask:",
            "archived": ":material-archive:",
        }
        if self.maturity == "production-ready":
            # Full support
            return self.bullet(
                icons["production-ready"],
                f"**{self.maturity}**{{title='"
                f"{self.classifications.maturity_descriptions[self.maturity]}'}}",
                "[All the production-ready project](#)",
            )
        if self.maturity in ["bugfixing only", "deprecated", "experimental"]:
            # Limited support
            return self.bullet(
                icons[self.maturity],
                "**Limited support**{{title='"
                f"{self.classifications.maturity_descriptions[self.maturity]}'}} {self.maturity}",
                "[All the production-ready project](#)",
            )
        if self.maturity in ["archived", "as-is"]:
            # No support
            return self.bullet(
                icons[self.maturity],
                "**No support**{{title='"
                f"{self.classifications.maturity_descriptions[self.maturity]}'}} {self.maturity}",
                "[All the projects without support](#)",
            )
        return ret

    def license_lines(self):
        """Bullet for member.license"""
        if self.license:
            return self.bullet(
                ":material-scale-balance:",
                f"**License** {self.license}",
                f"[All the projects with {self.license}](#)",
            )
        return []

    def interfaces_lines(self):
        """Bullet for member.interfaces"""
        if self.interfaces:
            return self.multi_bullet(
                ":material-api:",
                (" **Interface**" if len(self.interfaces) == 1 else " **Interfaces**"),
                [f"`{l}`" for l in self.interfaces],
                [f"[All the projects with {l} interface](#)" for l in self.interfaces],
            )
        return []

    def category_lines(self):
        """Bullet for member.category"""
        if self.category:
            return self.bullet(
                ":material-label:",
                f"**Category** `{self.category}`",
                f"[All the projects in the {self.category} category](#)",
            )
        return []

    def labels_lines(self):
        """Multi-bullet with member.labels"""
        if self.labels:
            return self.multi_bullet(
                ":material-tag-multiple-outline:",
                (" **Labels**" if len(self.labels) == 1 else " **Labels**"),
                [f"`{l}`" for l in self.labels],
                [f"[All the projects labeled with `{l}`](#)" for l in self.labels],
            )
        return self.bullet(":material-tag-off-outline:", "**No labels**")

    def pattern_steps_lines(self):
        """Bullet for member.pattern_steps"""
        if self.pattern_steps:
            return self.multi_bullet(
                ":material-tally-mark-4:",
                (
                    " **Qiskit Pattern steps**"
                    if len(self.pattern_steps) == 1
                    else " **Qiskit Pattern step**"
                ),
                [f"`{l}`" for l in self.pattern_steps],
                [
                    f"All the projects tagged wit the Qiskit Pattern step `{l}`](#)"
                    for l in self.pattern_steps
                ],
            )
        return []

    def ibm_maintained_lines(self):
        """Bullet for member.ibm_maintained"""
        if self.ibm_maintained:
            return self.bullet(
                ":material-office-building:",
                "IBM maintained",
                "[All the projects maintained by IBM](#)",
            )
        return []


class URLsCard(Card):
    """List of URLs"""

    def __init__(self, project: Member):
        """ret += ["- ### :material-web: **URLs**", "", "    ---", ""]"""
        self.project = project
        super().__init__(
            title="URLs",
            title_icon="### :material-web:",
            body_lines=self.list_of_links(),
        )

    def list_of_links(self):
        """List of links for the URL card"""
        ret = []
        if self.project.website:
            ret.append(f":material-web-box: [Website]({self.project.website})  ")
        if self.project.url:
            ret.append(f":octicons-file-code-16: [Source code]({self.project.url})  ")
        if self.project.documentation:
            ret.append(
                f":material-file-document: [Documentation]({self.project.documentation})  "
            )
        if self.project.reference_paper:
            icon = ":material-newspaper:"
            if "arxiv.org" in self.project.reference_paper.hostname:
                icon = ":simple-arxiv:"
            if "doi.org" in self.project.reference_paper.hostname:
                icon = ":simple-doi:"
            if "ieee.org" in self.project.reference_paper.hostname:
                icon = ":simple-ieee:"
            if "acm.org" in self.project.reference_paper.hostname:
                icon = ":simple-acm:"
            ret.append(f"{icon} [Reference paper]({self.project.reference_paper})  ")
        return ret


class PypiPackageCard(Card):
    """Python package card"""

    def __init__(
        self,
        package_name=None,
        version=None,
        url=None,
        last_release_date=None,
        last_month_downloads=None,
        last_180_days_downloads=None,
        requires_qiskit=None,
        highest_supported_qiskit_release_date=None,
        highest_supported_qiskit_version=None,
        compatible_with_qiskit_v1=None,
        compatible_with_qiskit_v2=None,
    ):
        self.package_name = package_name
        self.version = version
        self.url = url
        self.last_release_date = last_release_date
        self.last_month_downloads = last_month_downloads
        self.last_180_days_downloads = last_180_days_downloads
        self.requires_qiskit = requires_qiskit
        self.highest_supported_qiskit_release_date = (
            highest_supported_qiskit_release_date
        )
        self.highest_supported_qiskit_version = highest_supported_qiskit_version
        self.compatible_with_qiskit_v1 = compatible_with_qiskit_v1
        self.compatible_with_qiskit_v2 = compatible_with_qiskit_v2

        super().__init__(
            title=f"PyPI `{self.package_name}`",
            title_icon="#### :simple-python:",
            body_lines=self.body(),
        )

    @classmethod
    def from_pypi_data(cls, package):
        """Construct a card from a PyPIData"""
        return PypiPackageCard(
            package_name=package.package_name,
            version=package.version,
            url=package.url,
            last_release_date=package.last_release_date,
            last_month_downloads=package.last_month_downloads,
            last_180_days_downloads=package.last_180_days_downloads,
            requires_qiskit=package.requires_qiskit,
            highest_supported_qiskit_release_date=package.highest_supported_qiskit_release_date,
            highest_supported_qiskit_version=package.highest_supported_qiskit_version,
            compatible_with_qiskit_v1=package.compatible_with_qiskit_v1,
            compatible_with_qiskit_v2=package.compatible_with_qiskit_v2,
        )

    def body(self):
        """Returns a list of lines for the the card body"""
        ret = [
            ":fontawesome-regular-paper-plane: **current release** "
            f'[{self.version}]( {self.url} "Released: {self.last_release_date}")',
            "",
        ]
        if self.last_month_downloads and self.last_180_days_downloads:
            ret += [
                ":material-download: "
                f"**last month** {self.last_month_downloads:,} "
                f"**last 180 days** {self.last_180_days_downloads:,}"
            ]
        if self.requires_qiskit:
            ret += [
                "",
                ":simple-qiskit: **Qiskit Compatibility**\n\n",
                "| **Requires** | V1 | V2 | highest supported |",
                "| -- | -- | -- | -- |",
                f"| {self.requires_qiskit} | "
                + (
                    ":material-check-circle-outline:"
                    if self.compatible_with_qiskit_v1
                    else ":material-close-circle-outline:"
                )
                + " | "
                + (
                    ":material-check-circle-outline:"
                    if self.compatible_with_qiskit_v2
                    else ":material-close-circle-outline:"
                )
                + f" | [{self.highest_supported_qiskit_version}](https://pypi.org/project/qiskit/"
                f"{self.highest_supported_qiskit_version}/ "
                f'"Released: {self.highest_supported_qiskit_release_date}") |',
                "",
            ]

        return ret
