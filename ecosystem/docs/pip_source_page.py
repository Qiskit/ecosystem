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


"""Pages in https://qiskit.github.io/ecosystem/pip-source/<package-name>

The counterpart of `pypi_page` for a distribution that a repository declares but does
not publish: everything here comes from the manifests in the repository, so there is no
release to date, no download count, and often no version at all.
"""

from ecosystem.docs import command_block
from ecosystem.docs.card import ProjectSummaryCard, PipSourcePackageCard
from .project_page import ProjectPage


class PipSourcePage(ProjectPage):
    """represents a markdown file in docs/pip-source/"""

    def __init__(self, package, project, filename):
        """each of the files in docs/pip-source/*.md"""
        super().__init__(project, filename)
        self.package = package

    def generate_all_lines(self):
        """Returns all the docs/pip-source/<package-name>.md lines"""
        lines = []
        lines += self.front_matter()
        lines += self.title(self.package.package_name) + [""]
        lines += self.description() + [""]
        lines += self.general_summary()
        return lines

    def general_summary(self):
        return (
            ['<div class="grid cards" markdown>', ""]
            + self.pip_source_card()
            + self.project_card()
            + ["</div>"]
        )

    def description(self):
        """package summary, and the one command that installs it.

        The install line is a fenced block outside the card rather than a bullet inside it:
        it is what a reader came for, and a block is the only thing with a copy button. The
        manifests it was read from are in the card instead, next to the fields they declare.
        """
        lines = []
        if self.package.description:
            lines += [f"> {self.package.description}", ""]
        lines += [
            ":material-information-outline: Not published to a package registry. "
            "The metadata below is what the repository itself declares.",
            "",
        ]
        if self.card.pip_target:
            lines += command_block(f"pip install {self.card.pip_target}")
        return lines

    @property
    def card(self):
        """The distribution as its repository declares it"""
        return PipSourcePackageCard.from_python_data(self.package, self.project)

    def pip_source_card(self):
        """The card, untitled: the page title is already the distribution name"""
        card = self.card
        card.title = None
        return card.generate()

    def project_card(self):
        """Project summary, with project name in the title"""
        card = ProjectSummaryCard.from_project(self.project)
        card.body_lines = [
            f":material-code-tags: **Project** [{self.project.name}]"
            f"(../p/{self.project.short_uuid}.md)",
            "",
        ] + card.body_lines
        return card.generate()
