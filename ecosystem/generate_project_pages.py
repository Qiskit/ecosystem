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

"""Generate pages for:
- all projects - pages for https://qiskit.github.io/ecosystem/p/
- pypi packages - pages for https://qiskit.github.io/ecosystem/pypi/
- pip-installable repositories - pages for https://qiskit.github.io/ecosystem/pip-source/
"""

import csv
import io

import mkdocs_gen_files

from ecosystem.cli.members import CliMembers
from ecosystem.docs import write_if_changed
from ecosystem.docs.pip_source_page import PipSourcePage
from ecosystem.docs.project_page import ProjectPage
from ecosystem.docs.pypi_page import PypiPage

project_nav = mkdocs_gen_files.Nav()
pypi_nav = mkdocs_gen_files.Nav()
pip_source_nav = mkdocs_gen_files.Nav()

#: The columns of each table of the summary page. The project one says how many check ups
#: it is failing and how many it has an explanation for, which no other page says per
#: project: the check up page lists the projects per check up instead.
PROJECT_FIELDS = [
    "name",
    "status",
    "maturity",
    "failing check ups",
    "xfailed check ups",
]
PACKAGE_FIELDS = ["name", "status", "maturity"]

active_projects = []
active_pypi = []
active_pip_source = []

for project in CliMembers().dao.get_all(sort_key=lambda x: x.name_id):
    project_page = ProjectPage(project, f"p/{project.short_uuid}.md")
    project_page.write_page()
    project_nav[project.name] = f"{project.short_uuid}.md"
    if not project.is_alumni:
        active_projects.append(
            {
                "name": f"<a href='../p/{project.short_uuid}'>{project.name}</a>",
                "status": project.status or "Active project",
                "maturity": project.maturity,
                "failing check ups": len(project.failing_checkups),
                "xfailed check ups": len(project.xfails),
            }
        )
    if project.pypi:
        for package in project.pypi.values():
            pypi_page = PypiPage(package, project, f"pypi/{package.package_name}.md")
            pypi_page.write_page()
            pypi_nav[package.package_name] = f"{package.package_name}.md"
            if not project.is_alumni:
                active_pypi.append(
                    {
                        "name": f"<a href='../pypi/{package.package_name}'>"
                        f"{package.package_name}</a>",
                        "status": project.status or "Active project",
                        "maturity": project.maturity,
                    }
                )
    if project.python:
        for package in project.python.values():
            pip_source_page = PipSourcePage(
                package, project, f"pip-source/{package.package_name}.md"
            )
            pip_source_page.write_page()
            pip_source_nav[package.package_name] = f"{package.package_name}.md"
            if not project.is_alumni:
                active_pip_source.append(
                    {
                        "name": f"<a href='../pip-source/{package.package_name}'>"
                        f"{package.package_name}</a>",
                        "status": project.status or "Active project",
                        "maturity": project.maturity,
                    }
                )

with mkdocs_gen_files.open("p/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(project_nav.build_literate_nav())

with mkdocs_gen_files.open("pypi/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(pypi_nav.build_literate_nav())

with mkdocs_gen_files.open("pip-source/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(pip_source_nav.build_literate_nav())


def as_csv(rows, fieldnames=None):
    """The rows as CSV text, with the header the table of that page wants.

    `fieldnames` is given rather than read off the first row: a table can legitimately have
    no rows at all, and the file still has to be a CSV `read_csv` can render.
    """
    buffer = io.StringIO()
    # \n, not the csv default \r\n, so the content compares equal on the next build
    writer = csv.DictWriter(
        buffer, fieldnames=fieldnames or PACKAGE_FIELDS, lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


# written only when the content changed, so a build does not trigger the next one
write_if_changed(
    "docs/assets/active_projects.csv", as_csv(active_projects, PROJECT_FIELDS)
)
write_if_changed("docs/assets/active_pypi.csv", as_csv(active_pypi))
write_if_changed("docs/assets/pip_source.csv", as_csv(active_pip_source))
