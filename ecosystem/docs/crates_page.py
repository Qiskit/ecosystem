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


"""Pages in https://qiskit.github.io/ecosystem/crates/<crate-name>

The counterpart of `pypi_page` for the Rust registry: one page per published crate, so a
reader who arrived looking for the crate lands on something about the crate rather than on
the project that happens to publish it.
"""

from ecosystem.docs import command_block
from ecosystem.docs.card import ProjectSummaryCard, CratesPackageCard
from .project_page import ProjectPage


class CratesPage(ProjectPage):
    """represents a markdown file in docs/crates/"""

    def __init__(self, crate, project, filename):
        """each of the files in docs/crates/*.md"""
        super().__init__(project, filename)
        self.crate = crate

    def generate_all_lines(self):
        """Returns all the docs/crates/<crate-name>.md lines"""
        lines = []
        lines += self.front_matter()
        lines += self.title(self.crate.package_name) + [""]
        lines += self.description() + [""]
        lines += self.general_summary()
        return lines

    def general_summary(self):
        return (
            ['<div class="grid cards" markdown>', ""]
            + self.crates_card()
            + self.project_card()
            + ["</div>"]
        )

    def description(self):
        """crate summary, how to depend on it, and the crates.io page"""
        lines = []
        if self.crate.description:
            lines += [f"> {self.crate.description}", ""]
        lines += command_block(f"cargo add {self.crate.package_name}")
        lines += ["", f":simple-rust: [{self.crate.url}]({self.crate.url})"]
        return lines

    def crates_card(self):
        """The crate as crates.io describes it"""
        card = CratesPackageCard.from_crates_data(self.crate)
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
