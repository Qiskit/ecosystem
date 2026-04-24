import mkdocs_gen_files

from ecosystem.classifications import ClassificationsToml
from ecosystem.cli.members import CliMembers

classifications = ClassificationsToml()


def front_matter(p):
    """returns lines with front matter"""
    fm = []
    if p.status == "Qiskit Project":
        fm.append("icon: simple/qiskit")
    elif p.status == "Alumni":
        fm.append("icon: material/note-remove-outline")
    elif p.status == "Under review":
        fm.append("icon: fontawesome/regular/commenting")
    return ["---"] + fm + ["---"] if fm else []


def title(p):
    """returns lines with title"""
    return [
        f"# {p.name} [:material-file-edit-outline:]"
        "(https://github.com/Qiskit/ecosystem/edit/main/resources/"
        f"members/{p.name_id}.toml)",
    ]


def description(p):
    """returns lines with description"""
    return [">", p.description] if p.description else []


def classification_card(p):
    """
    -   **Qiskit Project** (1)
        { .annotate }

        1.  [All the Qiskit Projects](#)

        ---
    """
    ret = []
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
            "    1.  [All the Qiskit Projects](#)",
            "",
            "    ---",
            "",
        ]

    if p.status == "Alumni":
        ret += [
            "-   :material-note-remove-outline: **Alumni project** (1)",
            "    { .annotate }",
            "",
            "    1.  [All the Alumni projects](#)",
            "",
            "    ---",
            "",
        ]

    if p.status == "Under review":
        ret += [
            "-   :fontawesome-regular-commenting: **Project under review**{ title="
            f"'{classifications.status_descriptions['Under review']}'"
            " } (1)",
            "    { .annotate }",
            "",
            "    1.  [All the projects under review](#)",
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
    if p.interface:
        ret += [
            f"    :material-api Main interface `{p.interface}` (1)",
            "    { .annotate }",
            "",
            f"    1.  [All the projects with `{p.interface}` interface](#)",
            "",
        ]
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
            f"    :material-office-building: IBM maintained (1)",
            "    { .annotate }",
            "",
            f"    1.  [All the projects maintained by IBM](#)",
            "",
        ]
    return ret


def urls_card(p):
    """
    - :material-web: **URLs**

        ---

        :material-web-box: [Website](<link>)
        :octicons-file-code-16: [Source code](<link>)
        :material-file-document: [Documentation](<link>)

    """
    ret = []
    ret += ["- :material-web: **URLs**", "", "    ---", ""]
    if p.website:
        ret.append(f"    :material-web-box: [Website]({p.website})  ")
    if p.url:
        ret.append(f"    :octicons-file-code-16: [Source code]({p.url})  ")
    if p.documentation:
        ret.append(f"    :material-file-document: [Documentation]({p.documentation})  ")
    return ret


def general_summary(p):
    """grid with summary"""
    return (
        ['<div class="grid cards" markdown>', ""]
        + classification_card(p)
        + urls_card(p)
        + ["</div>"]
    )
    """
    
    :material-api: Main interface `Python` (1)
    { .annotate }
    
    1.  [All the projects with `Python` interface](#)
    
    :material-label: `Circuit simulator` (1)
    { .annotate }
    
    1.  [All the projects `Circuit simulator` category](#)
    
    :material-tag-multiple-outline: `provider` (1) `other` (2)
    { .annotate }

    1.  [All the projects with `provider` label ](#)
    2.  [All the projects with `other` label](#)
    
    :material-office-building: IBM maintained (1)
    { .annotate }

    1.  [All the projects maintained by IBM](#)

- :material-web: **URLs** 

    ---

    :material-web-box: [Website](#)  
    :octicons-file-code-16: [Source code](#)  
    :material-file-document: [Documentation](https://qiskit.github.io/qiskit-aer/)

</div>

    """


nav = mkdocs_gen_files.Nav()

for project in CliMembers().dao.get_all():
    filename = f"p/{project.name_id}.md"
    lines = []
    lines += front_matter(project)
    lines += title(project) + [""]
    lines += description(project) + [""]
    lines += general_summary(project) + [""]

    with mkdocs_gen_files.open(filename, "w") as f:
        print("\n".join(lines), file=f)

    mkdocs_gen_files.set_edit_path(
        filename,
        f"resources/members/{project.name_id}.toml",
    )

with mkdocs_gen_files.open("references/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
