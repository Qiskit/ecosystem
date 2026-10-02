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


"""Pages in https://qiskit.github.io/ecosystem/pypi/<package-name>"""

from ecosystem.docs.card import ProjectSummaryCard, PypiPackageCard
from .project_page import ProjectPage


class PypiPage(ProjectPage):
    """represents a markdown file in docs/pypi/"""

    def __init__(self, package, project, filename):
        """each of the files in docs/pypi/*.md"""
        super().__init__(project, filename)
        self.package = package

    def generate_all_lines(self):
        """Returns all the docs/p/<uuid>.md lines"""
        lines = []
        lines += self.front_matter()
        lines += self.title(self.package.package_name) + [""]
        lines += self.description() + [""]
        lines += self.general_summary()
        # lines += self.checkups()
        return lines

    def general_summary(self):
        return (
            ['<div class="grid cards" markdown>', ""]
            + self.pypi_card()
            + self.project_card()
            + ["</div>"]
        )

    def description(self):
        """package summary, pip install command and the PyPI project page"""
        lines = []
        if self.package.description:
            lines += [f"> {self.package.description}", ""]
        lines.append(f":simple-python: `pip install {self.package.package_name}`")
        lines += ["", f":simple-pypi: [{self.pypi_url}]({self.pypi_url})"]
        return lines

    @property
    def pypi_url(self):
        """The PyPI project page of the package.

        `self.package.url` comes from PyPI itself, but a package that was never fetched (or
        does not exist anymore) has none, and the URL is a function of the name anyway.
        """
        return (
            self.package.url or f"https://pypi.org/project/{self.package.package_name}/"
        )

    def pypi_card(self):
        """Python pacakge"""
        card = PypiPackageCard.from_pypi_data(self.package)
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
