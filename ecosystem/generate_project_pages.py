"""Generate project pages for https://qiskit.github.io/ecosystem/p/"""

import mkdocs_gen_files

from ecosystem.classifications import ClassificationsToml
from ecosystem.cli.members import CliMembers

nav = mkdocs_gen_files.Nav()


class ProjectPage:  # pylint: disable=redefined-outer-name
    """represents a markdown file in docs/p/"""

    def __init__(self, project, filename):
        """each of the files in docs/p/*.md"""
        self.project = project
        self.filename = filename
        self.classifications = ClassificationsToml()

    def generate_all_lines(self):
        """Returns all the docs/p/<project>.md lines"""
        lines = []
        lines += self.front_matter()
        lines += self.title() + [""]
        lines += self.description() + [""]
        lines += self.general_summary() + [""]
        lines += self.badge() + [""]
        lines += self.checkups()
        lines.append("</div>")
        return lines

    def write_page(self):
        """takes the lines and writes them down"""
        with mkdocs_gen_files.open(self.filename, "w") as f:
            print("\n".join(self.generate_all_lines()), file=f)
        mkdocs_gen_files.set_edit_path(
            self.filename,
            f"resources/members/{project.name_id}.toml",
        )

    def front_matter(self):
        """returns lines with front matter"""
        fm = []
        if self.project.status == "Qiskit Project":
            fm.append("icon: simple/qiskit")
        elif self.project.status == "Alumni":
            fm.append("icon: material/account-remove")
        elif self.project.status == "Under review":
            fm.append("icon: material/account-alert")
        else:
            fm.append("icon: material/account")
        return ["---"] + fm + ["---"] if fm else []

    def title(self):
        """returns lines with title"""
        return [
            f"# {self.project.name} [:material-file-edit-outline:]"
            "(https://github.com/Qiskit/ecosystem/edit/main/resources/"
            f"members/{self.project.name_id}.toml)",
        ]

    def general_summary(self):
        """grid with summary"""
        return (
            ['<div class="grid cards" markdown>', ""]
            + self.classification_card()
            + self.urls_card()
            # + ["</div>"]
        )

    def classification_card(self):  # pylint: disable=too-many-branches
        """
        -   **Qiskit Project** (1)
            { .annotate }

            1.  [All the Qiskit Projects](#)

            ---
        """
        ret = []
        p = self.project
        if p.status is None:
            ret += [
                "-   **Qiskit Ecosystem Member**",
                "",
                "    ---",
                "",
            ]

        if p.status == "Qiskit Project":
            ret += [
                "-   :simple-qiskit: **Qiskit Project** (1)",
                "    { .annotate }",
                "",
                f"    1.  {self.classifications.status_descriptions['Qiskit Project']} <br/>"
                "[All the Qiskit Projects](#../status.md#qiskit-project)",
                "",
                "    ---",
                "",
            ]

        if p.status == "Alumni":
            ret += [
                "-   :material-account-remove: **Alumni project** (1)",
                "    { .annotate }",
                "",
                f"    1. {self.classifications.status_descriptions['Alumni']} <br/>"
                "[All the Alumni projects](../status.md#alumni)",
                "",
                "    ---",
                "",
            ]

        if p.status == "Under revision":
            ret += [
                "-   :material-account-alert: **Project under revision**{ title="
                f"'{self.classifications.status_descriptions['Under revision']}'"
                " } (1)",
                "    { .annotate }",
                "",
                f"    1.  {self.classifications.status_descriptions['Under revision']} <br/>"
                "[All the projects under revision](../status.md#under-revision)",
                "",
                "    ---",
                "",
            ]

        if p.licence:
            ret += [
                f"    :material-scale-balance: **License** {p.licence} (1)",
                "    { .annotate }",
                "",
                f"    1.  [All the projects with {p.licence}](#)",
                "",
            ]
        if p.interfaces:
            interfaces = ""
            annotation = []
            for index, interface in enumerate(p.interfaces, start=1):
                interfaces += f" `{interface}` ({index})"
                annotation.append(
                    f"    {index}.  [All the projects with interface `{interface}`](#)"
                )
            if annotation:
                annotation.append("")
            ret += [
                f"    :material-api: **Main interface** {interfaces}",
                "    { .annotate }",
                "",
            ] + annotation
        if p.category:
            ret += [
                f"    :material-label: **Category** `{p.category}` (1)",
                "    { .annotate }",
                "",
                f"    1.  [All the projects in the `{p.category}` category](#)",
                "",
            ]
        if p.labels:
            labels = ""
            annotation = []
            for index, label in enumerate(p.labels, start=1):
                labels += f" `{label}` ({index})"
                annotation.append(
                    f"    {index}.  [All the projects with label `{label}`](#)"
                )
            if annotation:
                annotation.append("")
            ret += [
                f"    :material-tag-multiple-outline: **Labels** {labels}",
                "    { .annotate }",
                "",
            ] + annotation
        if p.ibm_maintained:
            ret += [
                "    :material-office-building: IBM maintained (1)",
                "    { .annotate }",
                "",
                "    1.  [All the projects maintained by IBM](#)",
                "",
            ]
        return ret

    def checkups(self):
        """Checkups card"""
        lines = ["\n", "- ### :material-list-status: Checkups", "\n", "    ---", "\n"]
        if self.project.checks is None:
            lines.append("    All good")
        else:
            for checkup in self.project.checks.values():
                lines += [
                    f"    :{checkup.importance_icon}:"
                    f'{{ title="{checkup.importance} - {checkup.importance_description}" }} '
                    f'`[{checkup.id}]`{{title="{checkup.title}"}} - {checkup.details}  '
                ]
        return lines

    def badge(self):
        """Badge card"""
        if self.project.badge_md is None:
            return []
        lines = [
            "\n",
            "- ### :simple-shieldsdotio: Badge",
            "\n",
            "    ---",
            f"![{self.project.name} badge]({self.project.badge.url}) <button "
            'class="md-code__button" title="Copy to clipboard" '
            'data-clipboard-target="#__code_0 &gt; code" '
            'data-md-type="copy"></button>',
            " **style** `flat` ",
            '    ```markdown title="paste this in README.md"',
            "",
            "    " + self.project.badge_md,
            "    ```",
            "",
        ]
        return lines

    def urls_card(self):
        """
        - :material-web: **URLs**

            ---

            :material-web-box: [Website](<link>)
            :octicons-file-code-16: [Source code](<link>)
            :material-file-document: [Documentation](<link>)

        """
        ret = []
        p = self.project
        ret += ["- ### :material-web: **URLs**", "", "    ---", ""]
        if self.project.website:
            ret.append(f"    :material-web-box: [Website]({p.website})  ")
        if self.project.url:
            ret.append(f"    :octicons-file-code-16: [Source code]({p.url})  ")
        if self.project.documentation:
            ret.append(
                f"    :material-file-document: [Documentation]({p.documentation})  "
            )
        return ret

    def description(self):
        """returns lines with description"""
        return [">", self.project.description] if self.project.description else []


for project in CliMembers().dao.get_all():
    project_page = ProjectPage(project, f"p/{project.name_id}.md")
    project_page.write_page()

with mkdocs_gen_files.open("references/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
