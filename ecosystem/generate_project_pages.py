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
"""

import csv
import mkdocs_gen_files

from ecosystem.cli.members import CliMembers
from ecosystem.docs.project_page import ProjectPage
from ecosystem.docs.pypi_page import PypiPage

project_nav = mkdocs_gen_files.Nav()
pypi_nav = mkdocs_gen_files.Nav()

active_projects = []
active_pypi = []

for project in CliMembers().dao.get_all(sort_key=lambda x: x.name_id):
    project_page = ProjectPage(project, f"p/{project.short_uuid}.md")
    project_page.write_page()
    project_nav[project.name] = f"{project.short_uuid}.md"
    if project.status != "Alumni":
        active_projects.append(
            {
                "name": f"<a href='../p/{project.short_uuid}'>{project.name}</a>",
                "status": project.status or "Active project",
                "maturity": project.maturity,
            }
        )
    if project.pypi:
        for package in project.pypi.values():
            pypi_page = PypiPage(package, project, f"pypi/{package.package_name}.md")
            pypi_page.write_page()
            pypi_nav[package.package_name] = f"{package.package_name}.md"
            if project.status != "Alumni":
                active_pypi.append(
                    {
                        "name": f"<a href='../pypi/{package.package_name}'>"
                        f"{package.package_name}</a>",
                        "status": project.status or "Active project",
                        "maturity": project.maturity,
                    }
                )

with mkdocs_gen_files.open("p/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(project_nav.build_literate_nav())

with mkdocs_gen_files.open("pypi/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(pypi_nav.build_literate_nav())

with open("docs/assets/active_projects.csv", mode="w") as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=["name", "status", "maturity"])
    writer.writeheader()
    writer.writerows(active_projects)

with open("docs/assets/active_pypi.csv", mode="w") as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=["name", "status", "maturity"])
    writer.writeheader()
    writer.writerows(active_pypi)
