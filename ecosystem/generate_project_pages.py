"""Generate project pages for https://qiskit.github.io/ecosystem/p/"""

import mkdocs_gen_files
from slugify import slugify

from ecosystem.classifications import ClassificationsToml
from ecosystem.cli.members import CliMembers


class ProjectPage:  # pylint: disable=redefined-outer-name
    """represents a markdown file in docs/p/"""

    def __init__(self, project, filename):
        """each of the files in docs/p/*.md"""
        self.project = project
        self.filename = filename
        self.classifications = ClassificationsToml()

    def generate_all_lines(self):
        """Returns all the docs/p/<uuid>.md lines"""
        lines = []
        lines += self.front_matter()
        lines += self.title() + [""]
        lines += self.description() + [""]
        lines += self.general_summary()
        lines += self.badge()
        lines += self.checkups()
        lines += self.packages()
        return lines

    def general_summary(self):
        return (
            ['<div class="grid cards" markdown>', ""]
            + self.classification_card()
            + self.urls_card()
            + ["</div>"]
        )

    def packages(self):
        packages = {}
        if self.project.packages:
            sites = []
            for package in self.project.packages:
                if "visualstudio.com" in package.hostname:
                    sites.append(
                        (
                            "material-microsoft-visual-studio",
                            f"[Visual Studio Marketplace: {package.query.split('=')[1]}]({package})",
                        )
                    )
                elif "ocaml.org" in package.hostname:
                    sites.append(
                        (
                            "simple-ocaml",
                            f"[opam (OCaml Package Manager): {package.path.split('/')[2]}]({package})",
                        )
                    )
                elif "github.com" in package.hostname:
                    sites.append(
                        (
                            "simple-github",
                            f"[GitHub Package: {package.path.split('/')[5]}]({package})",
                        )
                    )
                elif "crates.io" in package.hostname:
                    sites.append(
                        (
                            "simple-rust",
                            f"[Crate: {package.path.split('/')[-1]}]({package})",
                        )
                    )
                else:
                    sites.append(
                        ("octicons-package-16", f"[{package.hostname}]({package})")
                    )
            packages[None] = ['<div class="grid cards" markdown>', " * \n"]
            packages[None] += [f"    - :{icon}: {p}" for icon, p in sites]
            packages[None] += ["</div>"]

        if self.project.pypi:
            packages["pypi"] = ['<div class="grid cards" markdown>']
            for pkg in self.project.pypi.values():
                packages["pypi"].append(
                    f" - #### :simple-python: PyPI `{pkg.package_name}`\n    ---\n"
                )
                packages["pypi"] += [
                    "    :fontawesome-regular-paper-plane: **current release** "
                    f'[{pkg.version}]( {pkg.url} "Released: {pkg.last_release_date}")',
                    "",
                ]
                packages["pypi"] += [
                    "    :material-download: "
                    f"**last month** {pkg.last_month_downloads:,} "
                    f"**last 180 days** {pkg.last_180_days_downloads:,}"
                ]
                if pkg.requires_qiskit:
                    packages["pypi"] += [
                        "",
                        "    :simple-qiskit: **Qiskit Compatibility**\n\n",
                        "    | **Requires** | V1 | V2 | highest supported |",
                        "    | -- | -- | -- | -- |",
                        f"    | {pkg.requires_qiskit} | "
                        + (
                            ":material-check-circle-outline:"
                            if pkg.compatible_with_qiskit_v1
                            else ":material-close-circle-outline:"
                        )
                        + " | "
                        + (
                            ":material-check-circle-outline:"
                            if pkg.compatible_with_qiskit_v2
                            else ":material-close-circle-outline:"
                        )
                        + f" | [{pkg.highest_supported_qiskit_version}](https://pypi.org/project/qiskit/"
                        f"{pkg.highest_supported_qiskit_version}/ "
                        f'"Released: {pkg.highest_supported_qiskit_release_date}") |',
                        "",
                    ]
            packages["pypi"] += ["</div>"]

        if self.project.julia:
            packages["julia"] = ['<div class="grid cards" markdown>']
            for pkg in self.project.julia.values():
                packages["julia"].append(
                    f" - #### :simple-julia: Julia `{pkg.package_name}`\n    ---\n"
                )
                packages["julia"] += [
                    "    :fontawesome-regular-paper-plane: **current release** "
                    f"[{pkg.version}](https://juliahub.com/ui/Packages/"
                    f'{pkg.registry}/{pkg.package_name} "Released: {pkg.release_date}")',
                    "",
                ]
                packages["julia"] += [
                    "    :fontawesome-solid-users: "
                    f"**estimated unique users** {pkg.estimated_unique_users:,} "
                ]
            packages["julia"] += ["</div>"]

        if not packages:
            return []
        ret = ["\n---\n### :material-package-variant: Packages\n"]
        ret += packages.get("pypi", [])
        ret += packages.get("julia", [])
        ret += packages.get(None, [])
        return ret

    def write_page(self):
        """takes the lines and writes them down"""
        with mkdocs_gen_files.open(self.filename, "w") as f:
            print("\n".join(self.generate_all_lines()), file=f)
        mkdocs_gen_files.set_edit_path(
            self.filename,
            f"resources/members/{project.short_uuid}.toml",
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

        if p.status != "Alumni":
            icons = {
                "production-ready": ":material-check-outline:",
                "bugfixing only": ":material-bug-check:",
                "as-is": ":material-image-broken-variant:",
                "deprecated": ":fontawesome-solid-exclamation-triangle:",
                "experimental": ":material-flask:",
            }
            ret += [
                f"    {icons[p.maturity]}{{ "
                f"title='{self.classifications.maturity_descriptions[p.maturity]}' }} "
            ]

            if p.maturity == "production-ready":
                # Full support
                ret.append(f"**{p.maturity}** (1)")
            elif p.maturity in ["bugfixing only", "deprecated", "experimental"]:
                # Limited support
                ret.append(f"**Limited support** {p.maturity} (1)")
            elif p.maturity in ["archived", "as-is"]:
                # No support
                ret.append(f"**No support** {p.maturity} (1)")
            ret += [
                "    { .annotate }",
                "",
                f"    1.  [All the projects with {p.maturity} support](#)",
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
        else:
            ret += [
                f"    :material-tag-off-outline: **No labels**",
                "    { .annotate }",
                "",
            ]
        if p.pattern_steps:
            steps = ""
            annotation = []
            for index, step in enumerate(p.pattern_steps, start=1):
                steps += f" `{step}` ({index})"
                annotation.append(
                    f"    {index}.  [All the projects tagged wit the Qiskit pattern step `{step}`](#)"
                )
            if annotation:
                annotation.append("")
            ret += [
                f"    :material-tally-mark-4: **Qiskit Pattern step** {steps}",
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
        lines = [
            "\n---\n",
            "### :material-list-status: Checkups",
            "\n",
        ]
        if not self.project.checks:
            lines.append(":material-check-all: All good")
        else:
            for checkup in self.project.checks.values():
                lines += [
                    f":{checkup.importance_icon}:"
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
            "### :simple-shieldsdotio: Badge",
            "\n",
            '<div style="display: flex;"><button '
            ' title="Copy to clipboard" '
            'data-clipboard-target="#__code___code_0 &gt; code" '
            'data-md-type="copy">',
            f'<img src="{self.project.badge.url}">',
            f'</button><pre style="width:600px; margin:0px" id="__code_0"><code tabindex="0">{self.project.badge_md}</code></pre></div>',
            f"\n**style** `{self.project.badge.style}`  \n Check out [Badges section](../badges) to learn more about how badges are used for status communicaiton or on how to change the badge style.",
        ]
        return lines

    def urls_card(self):
        """List of URLs in the project metadata"""
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
        if self.project.reference_paper:
            icon = ":material-newspaper:"
            if "arxiv.org" in self.project.reference_paper.hostname:
                icon = ":simple-arxiv:"
            if "doi.org" in project.reference_paper.hostname:
                icon = ":simple-doi:"
            if "ieee.org" in project.reference_paper.hostname:
                icon = ":simple-ieee:"
            if "acm.org" in project.reference_paper.hostname:
                icon = ":simple-acm:"
            ret.append(f"    {icon} [Reference paper]({p.reference_paper})  ")
        return ret

    def description(self):
        """returns lines with description"""
        return [">", self.project.description] if self.project.description else []


nav = mkdocs_gen_files.Nav()
for project in CliMembers().dao.get_all(sort_key=lambda x: slugify(x.name)):
    project_page = ProjectPage(project, f"p/{project.short_uuid}.md")
    project_page.write_page()
    nav[project.name] = f"{project.short_uuid}.md"

with mkdocs_gen_files.open("p/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
