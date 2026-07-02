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

"""
Pages inhttps://qiskit.github.io/ecosystem/p/<short uuid>
"""

import mkdocs_gen_files

from ecosystem.classifications import ClassificationsToml
from ecosystem.docs.card import ProjectSummaryCard, URLsCard, PypiPackageCard


class ProjectPage:  # pylint: disable=redefined-outer-name
    """represents a markdown file in docs/p/"""

    classifications = ClassificationsToml()

    def __init__(self, project, filename):
        """each of the files in docs/p/*.md"""
        self.project = project
        self.filename = filename

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
        """Summary section"""
        return (
            ['<div class="grid cards" markdown>', ""]
            + self.classification_card()
            + self.urls_card()
            + ["</div>"]
        )

    def packages(self):  # pylint: disable = too-many-branches
        """Package section"""
        packages = {}
        if self.project.packages:
            sites = []
            for package in self.project.packages:
                if "visualstudio.com" in package.hostname:
                    sites.append(
                        (
                            "material-microsoft-visual-studio",
                            "[Visual Studio Marketplace: "
                            f"{package.query.split('=')[1]}]({package})",
                        )
                    )
                elif "ocaml.org" in package.hostname:
                    sites.append(
                        (
                            "simple-ocaml",
                            "[opam (OCaml Package Manager): "
                            f"{package.path.split('/')[2]}]({package})",
                        )
                    )
                elif "github.com" in package.hostname:
                    sites.append(
                        (
                            "simple-github",
                            "[GitHub Package: "
                            f"{package.path.split('/')[5]}]({package})",
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
                packages["pypi"] += PypiPackageCard.from_pypi_data(pkg).generate()
            packages["pypi"] += ["</div>"]

        if self.project.julia:
            packages["julia"] = ['<div class="grid cards" markdown>']
            for pkg in self.project.julia.values():
                packages["julia"].append(
                    f" - #### :simple-julia: Julia `{pkg.package_name}`\n    ---\n"
                )
                version = pkg.version or "N/A"
                release_date = pkg or "N/A"
                packages["julia"] += [
                    "    :fontawesome-regular-paper-plane: **current release** "
                    f"[{version}](https://juliahub.com/ui/Packages/"
                    f'{pkg.registry}/{pkg.package_name} "Released: {release_date}")',
                    "",
                ]
                if pkg.estimated_unique_users:
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
            f"resources/members/{self.project.short_uuid}.toml",
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

    def title(self, main_title=None):
        """returns lines with title"""
        return [
            f"# {main_title or self.project.name} [:material-file-edit-outline:]"
            "(https://github.com/Qiskit/ecosystem/edit/main/resources/"
            f"members/{self.project.name_id}.toml)",
        ]

    def classification_card(self):  # pylint: disable=too-many-branches
        """Card with all the project classificaitons"""
        return ProjectSummaryCard.from_project(self.project).generate()

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
            '</button><pre style="width:600px; margin:0px" id="__code_0">'
            f'<code tabindex="0">{self.project.badge_md}</code></pre></div>',
            f"\n**style** `{self.project.badge.style}`  \n Check out [Badges section]"
            "(../badges) to learn more about how badges are used for status communicaiton "
            "or on how to change the badge style.",
        ]
        return lines

    def urls_card(self):
        """List of URLs in the project metadata"""
        return URLsCard(self.project).generate()

    def description(self):
        """returns lines with description"""
        return [">", self.project.description] if self.project.description else []
