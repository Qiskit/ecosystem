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


"""Pages in https://qiskit.github.io/ecosystem/cargo-source/<crate-name>

The counterpart of `pip_source_page` for Rust: a crate the repository declares and does
not publish, so everything here comes from the `Cargo.toml` on the default branch. There
is no release to date and no download count, and the way in is a git dependency.
"""

from ecosystem.docs import command_block
from ecosystem.docs.card import ProjectSummaryCard, CargoPackageCard
from .project_page import ProjectPage


class CargoPage(ProjectPage):
    """represents a markdown file in docs/cargo-source/"""

    def __init__(self, crate, project, filename):
        """each of the files in docs/cargo-source/*.md"""
        super().__init__(project, filename)
        self.crate = crate

    def generate_all_lines(self):
        """Returns all the docs/cargo-source/<crate-name>.md lines"""
        lines = []
        lines += self.front_matter()
        lines += self.title(self.crate.package_name) + [""]
        lines += self.description() + [""]
        lines += self.general_summary()
        return lines

    def general_summary(self):
        return (
            ['<div class="grid cards" markdown>', ""]
            + self.cargo_card()
            + self.project_card()
            + ["</div>"]
        )

    def description(self):
        """crate summary, and the one command that adds it as a dependency.

        The command is a fenced block outside the card, for the copy button a block has;
        the manifest it was read from is a link inside the card, beside the fields it
        declares.
        """
        lines = []
        if self.crate.description:
            lines += [f"> {self.crate.description}", ""]
        lines += [
            ":material-information-outline: Not published to crates.io. The metadata below "
            "is what the repository itself declares, and a project depends on a crate like "
            "this one through its git URL.",
            "",
        ]
        if self.card.cargo_target:
            lines += command_block(self.card.cargo_target)
        return lines

    @property
    def card(self):
        """The crate as its repository declares it"""
        return CargoPackageCard.from_cargo_data(self.crate, self.project)

    def cargo_card(self):
        """The crate card, untitled: the page title is already the crate name"""
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
