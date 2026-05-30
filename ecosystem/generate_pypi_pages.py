"""Generate PyPI pages for https://qiskit.github.io/ecosystem/pypi/"""

import mkdocs_gen_files

from ecosystem.cli.members import CliMembers
from ecosystem.docs.pypi_page import PypiPage

nav = mkdocs_gen_files.Nav()
for project in CliMembers().dao.get_all(sort_key=lambda x: x.name_id):
    if project.pypi:
        for package in project.pypi.values():
            pypi_page = PypiPage(project, f"pypi/{package.package_name}.md")
            pypi_page.write_page()
            nav[project.name] = f"{package.package_name}.md"

with mkdocs_gen_files.open("pipy/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
