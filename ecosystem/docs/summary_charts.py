# This code is part of Qiskit.
#
# (C) Copyright IBM 2026.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at https://www.apache.org/licenses/LICENSE-2.0.
#
# Author: the data behind the charts of docs/summary.md.

"""The data behind the charts of docs/summary.md.

The charts used to carry hardcoded numbers, which went stale the moment a member was added.
These fragments are written on every documentation build, so the charts say what the member
files say.

Three of the four are nested donuts: a ring per level of a hierarchy the data already has.
Every ring partitions the same set, so each one sums to the same total and the sectors of
the outer rings line up with the inner ones, which is what makes the shape readable. Rows
are written in hierarchical order for the same reason: Vega-Lite stacks the arcs of a layer
in the order it reads them.
"""

import json

from ecosystem.docs import anchor, write_if_changed
from ecosystem.serializable import parse_date

#: Status by status, inside the two groups the website splits the projects into. An
#: `Alumni` project is not in the website at all; the rest are, and `Member` is the regular
#: one, which the third ring splits by how young the project is.
MEMBER_STATUS = "Member"
ALUMNI_STATUS = "Alumni"
REGULAR = {
    "Member": "Regular",
    "Early Project": "Early",
    "Very Early Project": "Very early",
}
NOT_REGULAR = ["Qiskit Project", "Under revision", "Unmaintained"]

#: What `ProjectSummaryCard.maturity_lines` promises for each maturity, which is the
#: hierarchy of the maturity donut.
SUPPORT = {
    "production-ready": "Full support",
    "bugfixing only": "Limited support",
    "deprecated": "Limited support",
    "experimental": "Limited support",
    "as-is": "No support",
    "unmaintained": "No support",
}

#: Where a member's code can be got from, most reachable first. A member is counted once,
#: under the first of these it has, so the rings add up to the number of members: a project
#: that publishes to two registries is one project, and the tables below the charts are
#: what lists everything it publishes.
PACKAGING = [
    ("pypi", "Published", "PyPI"),
    ("crates", "Published", "crates.io"),
    ("julia", "Published", "Julia"),
    ("packages", "Published", "Another registry"),
    ("python", "Declared in the repository", "pip-installable"),
    ("cargo", "Declared in the repository", "cargo-installable"),
    ("requirements", "Declared in the repository", "A requirements file"),
]

#: What a member with none of the above is called in the chart
NOTHING = "Nothing recorded"

#: Where a sector takes a reader who clicks it, relative to the summary page. A sector with
#: nothing to point at links to the top of the charts rather than nowhere: an empty `href`
#: would make a click reload the page.
HERE = "#the-ecosystem-at-a-glance"
CLASSIFICATIONS = "../classifications/"
LINKS = {
    "In the website": f"{CLASSIFICATIONS}#status",
    "Alumni": f"{CLASSIFICATIONS}#alumni",
    "Regular member": f"{CLASSIFICATIONS}#regular-members",
    "Regular": f"{CLASSIFICATIONS}#regular-members",
    "Early": f"{CLASSIFICATIONS}#early-project",
    "Very early": f"{CLASSIFICATIONS}#early-project",
    "Qiskit Project": f"{CLASSIFICATIONS}#qiskit-project",
    "Under revision": f"{CLASSIFICATIONS}#under-revision",
    "Unmaintained": f"{CLASSIFICATIONS}#unmaintained",
    "Full support": f"{CLASSIFICATIONS}#maturity",
    "Limited support": f"{CLASSIFICATIONS}#maturity",
    "No support": f"{CLASSIFICATIONS}#maturity",
    "Not declared": f"{CLASSIFICATIONS}#maturity",
    "not declared": f"{CLASSIFICATIONS}#maturity",
    # the tables of this page, which list the members a sector counts
    "PyPI": "#active-pypi-packages",
    "crates.io": "#active-crates",
    "pip-installable": "#active-pip-installable-repositories",
    "cargo-installable": "#active-cargo-installable-repositories",
    "Published": "#active-projects",
    "Declared in the repository": "#active-projects",
    NOTHING: "#active-projects",
}


def ring(level, counts):
    """The rows of one ring of a donut, in the order they are stacked.

    `counts` is an ordered mapping of sector label to how many projects it holds. A sector
    with nothing in it is left out rather than drawn as a zero-width arc. `order` is the
    position in the ring: Vega-Lite would otherwise stack the arcs by colour, and the rings
    would stop lining up.
    """
    sectors = [(label, count) for label, count in counts.items() if count]
    total = sum(count for _, count in sectors)
    return [
        {
            "ring": level,
            "order": order,
            "label": label,
            "count": count,
            # of the ring, and every ring partitions the same projects, so the share of a
            # sector and of the one around it are comparable
            "share": round(count / total, 4),
            "url": link(label),
        }
        for order, (label, count) in enumerate(sectors)
    ]


def link(label):
    """Where a sector takes a reader who clicks it.

    A maturity is a section of the classifications page that `LINKS` does not spell out one
    by one: `anchor` builds the same id the heading got.
    """
    if label in LINKS:
        return LINKS[label]
    if label in SUPPORT:
        return f"{CLASSIFICATIONS}#{anchor(label)}"
    return HERE


def status_rings(projects):
    """Three rings: in the website or not, then the status, then how young the project is.

    The middle ring keeps `Member` as one sector, which the outer ring splits into the three
    ages of a regular member. The other sectors have nothing to split, so they are drawn
    again at the same size, which is what keeps the rings aligned.
    """
    status = {}
    for project in projects:
        status[project.status or MEMBER_STATUS] = (
            status.get(project.status or MEMBER_STATUS, 0) + 1
        )
    regular = sum(status.get(name, 0) for name in REGULAR)
    members = sum(count for name, count in status.items() if name != ALUMNI_STATUS)

    rows = ring(
        1, {"In the website": members, ALUMNI_STATUS: status.get(ALUMNI_STATUS, 0)}
    )
    rows += ring(
        2,
        {"Regular member": regular}
        | {name: status.get(name, 0) for name in NOT_REGULAR}
        | {ALUMNI_STATUS: status.get(ALUMNI_STATUS, 0)},
    )
    rows += ring(
        3,
        {label: status.get(name, 0) for name, label in REGULAR.items()}
        | {name: status.get(name, 0) for name in NOT_REGULAR}
        | {ALUMNI_STATUS: status.get(ALUMNI_STATUS, 0)},
    )
    return rows


def maturity_rings(projects):
    """Two rings: what support the maturity promises, then the maturity itself.

    Alumni are out: a project that is no longer a member promises nothing, which is why
    its page shows no maturity either.
    """
    maturities = {}
    for project in projects:
        if project.is_alumni:
            continue
        maturities[project.maturity or "not declared"] = (
            maturities.get(project.maturity or "not declared", 0) + 1
        )
    levels = ["Full support", "Limited support", "No support", "Not declared"]
    inner = {level: 0 for level in levels}
    outer = {}
    for level in levels:
        for maturity, count in maturities.items():
            if SUPPORT.get(maturity, "Not declared") == level:
                inner[level] += count
                outer[maturity] = count
    return ring(1, inner) + ring(2, outer)


def packaging_rings(projects):
    """Two rings: whether the code is published anywhere, then where from.

    See `PACKAGING`: each member is counted once, under the first kind it has.
    """
    groups = {}
    kinds = {}
    for project in projects:
        if project.is_alumni:
            continue
        for attribute, group, kind in PACKAGING:
            if getattr(project, attribute, None):
                break
        else:
            group, kind = NOTHING, NOTHING
        groups[group] = groups.get(group, 0) + 1
        kinds[kind] = kinds.get(kind, 0) + 1
    order = ["Published", "Declared in the repository", NOTHING]
    inner = {group: groups.get(group, 0) for group in order}
    # the outer ring follows the inner one, group by group, or the sectors do not line up
    outer = {}
    for group in order:
        for kind in [k for _, g, k in PACKAGING if g == group] or [NOTHING]:
            if kinds.get(kind):
                outer[kind] = kinds[kind]
    return ring(1, inner) + ring(2, outer)


def repository_years(projects):
    """How many member repositories were created each year, by the maturity they declare.

    One row per year and maturity, which the chart stacks: the shape says how the ecosystem
    grew, and the colours say what the projects of each year promise.

    `github.created_at` is the repository's own age, not the day the project joined, which
    nothing records. A member whose repository was never read has no year to count.
    """
    years = {}
    for project in projects:
        created_at = parse_date(getattr(project.github, "created_at", None))
        if project.is_alumni or not created_at:
            continue
        maturity = project.maturity or "not declared"
        years[(created_at.year, maturity)] = (
            years.get((created_at.year, maturity), 0) + 1
        )
    total = sum(years.values())
    # the maturities in the order the support they promise does, so a stack reads from the
    # strongest promise to the weakest
    order = list(SUPPORT) + ["not declared"]
    return [
        {
            "year": year,
            "maturity": maturity,
            "count": count,
            "share": round(count / total, 4),
            "url": link(maturity),
        }
        for (year, maturity), count in sorted(
            years.items(),
            key=lambda item: (
                item[0][0],
                order.index(item[0][1]) if item[0][1] in order else len(order),
            ),
        )
    ]


def totals(projects):
    """The counts a reader (or a badge) wants as one number each.

    Written as a flat JSON object so a shields.io dynamic badge can ask for `$.members`
    without walking anything.
    """
    status = {}
    for project in projects:
        status[project.status or MEMBER_STATUS] = (
            status.get(project.status or MEMBER_STATUS, 0) + 1
        )
    alumni = status.get(ALUMNI_STATUS, 0)
    return {
        "projects": len(projects),
        "members": len(projects) - alumni,
        "alumni": alumni,
        "qiskit_projects": status.get("Qiskit Project", 0),
        "regular_members": sum(status.get(name, 0) for name in REGULAR),
        "early_projects": status.get("Early Project", 0)
        + status.get("Very Early Project", 0),
        "under_revision": status.get("Under revision", 0),
        "unmaintained": status.get("Unmaintained", 0),
    }


def members_badge(projects):
    """The members count as a shields.io endpoint badge.

    https://shields.io/badges/endpoint-badge renders whatever this says, so the colour and
    the label live here rather than in the URL every reader would otherwise have to spell
    out.
    """
    return {
        "schemaVersion": 1,
        "label": "ecosystem members",
        "message": str(totals(projects)["members"]),
        "color": "8A3FFC",
    }


def as_json(data):
    """`data` as JSON text, with the trailing newline a file deserves.

    JSON rather than CSV: Vega-Lite reads either, and a JSON file is also what a
    shields.io dynamic badge can query (`https://shields.io/badges/dynamic-json-badge`).
    """
    return json.dumps(data, indent=2) + "\n"


#: The fragments the summary page reads: what each one is called, and what builds it
FRAGMENTS = [
    ("summary_status", status_rings),
    ("summary_maturity", maturity_rings),
    ("summary_packaging", packaging_rings),
    ("summary_years", repository_years),
    ("summary_totals", totals),
    ("members_badge", members_badge),
]


def fragments(projects):
    """The fragments as {filename: text}, for whoever is publishing them"""
    return {f"{name}.json": as_json(build(projects)) for name, build in FRAGMENTS}


def write_all(projects, directory="docs/assets"):
    """Writes the fragments to disk, for a `manager.py` run outside a documentation build.

    A build publishes them through `mkdocs_gen_files` instead (see
    `ecosystem/generate_docs_assets.py`): the charts and the badge fetch these files from
    the site at runtime, and mkdocs only copies what was in `docs/` when the build started
    or what a plugin registered.
    """
    for name, text in fragments(projects).items():
        write_if_changed(f"{directory}/{name}", text)
