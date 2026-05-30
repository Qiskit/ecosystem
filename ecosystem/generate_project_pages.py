"""Generate project pages for https://qiskit.github.io/ecosystem/p/"""

import mkdocs_gen_files

from ecosystem.cli.members import CliMembers
from ecosystem.docs.project_page import ProjectPage

nav = mkdocs_gen_files.Nav()
for project in CliMembers().dao.get_all(sort_key=lambda x: x.name_id):
    project_page = ProjectPage(project, f"p/{project.short_uuid}.md")
    project_page.write_page()
    nav[project.name] = f"{project.short_uuid}.md"

with mkdocs_gen_files.open("p/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
