---
hide:
  - edit
---

# Classifications

A **classification** is one of the handful of properties every Qiskit Ecosystem member
carries. Some of them are **declared** by the project in its
[member file](https://github.com/Qiskit/ecosystem/tree/main/resources/members), and some are
**derived** by the ecosystem tooling from the project data.
They are what the first card of every project page
(`https://qiskit.github.io/ecosystem/p/<short uuid>/`) summarizes, and this page is the
current state of the whole ecosystem: every classification, every value it can take, and the
projects that carry it right now.

The values of each classification, and their short descriptions, come from
[`resources/classifications.toml`](https://github.com/Qiskit/ecosystem/blob/main/resources/classifications.toml).

| Classification | Member field | Per project | Set by |
| --- | --- | --- | --- |
| [Status](#status) | `member.status` | exactly one | the tooling |
| [Maturity](#maturity) | `member.maturity` | exactly one (mandatory) | the project |
| [Category](#category) | `member.category` | exactly one | the project |
| [Labels](#labels) | `member.labels` | any number | the project |
| [Interfaces](#interfaces) | `member.interfaces` | any number | the project |
| [IBM maintained](#ibm-maintained) | `member.ibm_maintained` | yes or no | the tooling, at submission time |

## Status

The status is the standing of a project in the Qiskit Ecosystem.
Most members are regular **members**, which is the default status.

It is the one classification the submitter does not choose: it is derived from the project
data, such as the age of the source code repository, the declared [maturity](#maturity), and
the [check ups](checkups.md) the project is not passing.

??? note "Short descriptions"
    {{ read_json('docs/assets/status.json') }}

There are 6 kind of members: _Regular Members_ (the default), _Qiskit Projects_, _Early Projects_, _Very Early Projects_, _Unmaintained_ projects, and projects _Under revision_

<a id="member"></a>

### Regular members

{{ read_raw('docs/assets/member.md') }}

### Qiskit Project

{{ read_raw('docs/assets/qiskit-project.md') }}

<a id="early-project"></a>

### (Very) Early Project

A regular member whose source code repository is **less than 12 months old** (as reported by `member.github.created_at`). If the repository is less than 3 months old, the project is a _Very Early Project_ instead.

This status is derived automatically and it is not a rejection: it is a hint for potential users that the project is still young, and that its momentum and long-term support are less demonstrated than in an established project.
It is also a counterweight to the self-reported [maturity](#maturity): a submitter can declare a project as `production-ready`, but a repository created a few months ago carries this status next to that claim.

The status disappears on its own: as soon as the repository turns 12 months old, the next status update moves the project to a [regular member](#regular-members).
Projects with a pending [check up](#under-revision) are _Under revision_ instead, since that status takes precedence.

While a project is young, the activity [check ups](#under-revision) use a tighter window: instead of the flat 12 months since the last commit, a commit is expected within two thirds of the age of the repository (with a floor of 2 months), since a young project that stops committing has little track record to fall back on.

!!! tip
    _Very Early Projects_ are automatically excluded from the Qiskit Ecosystem website until they are 3 months old.
    Meanwhile, they are genuinely Qiskit Ecosystem members, so they can use their badge and have all the regular benefits.

{{ read_raw('docs/assets/early-projects.md') }}

<a id="unmaintained"></a>

### Unmaintained

A regular member whose self-declared [maturity](#maturity) is `as-is` or `deprecated`, that is, a project with no active maintenance expectations.

Since these projects are not expected to be maintained, they are exempt from the activity [check ups](#under-revision).

The status disappears as soon as the project declares a maturity level with maintenance expectations.
Projects with a pending [check up](#under-revision) are _Under revision_ instead, since that status takes precedence.

!!! tip
    _Unmaintained Projects_ stay in the Qiskit Ecosystem website like any other member: the lack of maintenance is intentional and declared upfront, so it is shown as part of the project information and not treated as a compliance issue.
    A project that quietly stops being maintained is a different story: sooner or later the activity [check ups](#under-revision) notice it, and it ends up as [Alumni](#alumni).

{{ read_raw('docs/assets/unmaintained.md') }}

### Under revision

If at some point one of the membership criteria checkup fails, then the status moves to **Under revision**.
Depending on how critical the failing checkup is, there is some cure period to remove the pending compliance.
If the failing check up persists or is not explained after this period, the project gets moved to _Alumni_ and removed from [the Qiskit Ecosystem website](http://qisk.it/ecosystem).

{{ read_raw('docs/assets/under-revision.md') }}

### Alumni

These projects are no longer in the Qiskit Ecosystem website, most probably because they no longer fulfill the criteria.
If you think there is a mistake, please [open an issue](https://github.com/Qiskit/ecosystem/issues/new?template=02_update.yml).

!!! tip
    An **alumni project can be reconsidered for Qiskit Ecosystem membership at any point**.
    Just PR the Qiskit Ecosystem repository removing the `member.status` entry in the project TOML file.

{{ read_raw('docs/assets/alumni.md') }}

## Maturity

Qiskit Ecosystem members have to be explicit on their support expectations, as well as their
stability. The maturity level is what the project claims about itself, from `production-ready`
to `deprecated`, and it is the only classification a member file must declare.

Unlike the [status](#status), it is not inferred from the source code repository activity.
Because it is a declaration and not an observation, it also has consequences: a project with
no maintenance expectations (`as-is` or `deprecated`) becomes [_Unmaintained_](#unmaintained)
and is exempt from the activity check ups.

??? note "Short descriptions"
    {{ read_json('docs/assets/maturity.json') }}

{{ read_raw('docs/assets/maturity.md') }}

## Category

The category says what kind of software the project is, such as a circuit simulator or a
transpiler plugin. A project has exactly one, so it is the coarsest way of navigating the
ecosystem.

??? note "Short descriptions"
    {{ read_json('docs/assets/category.json') }}

{{ read_raw('docs/assets/category.md') }}

## Labels

Labels describe what the project does or which technology it involves, and a project can
carry as many as apply (or none at all). Where the [category](#category) answers _what kind
of software is this_, labels answer _what else is worth knowing about it_.

??? note "Short descriptions"
    {{ read_json('docs/assets/labels.json') }}

{{ read_raw('docs/assets/labels.md') }}

## Interfaces

Interfaces are the languages and APIs the project can be used from, such as `Python`, `C`, or
`Julia`. A project offering more than one lists them all.

??? note "Short descriptions"
    {{ read_json('docs/assets/interfaces.json') }}

{{ read_raw('docs/assets/interfaces.md') }}

## IBM maintained

A project is flagged as IBM maintained when the ecosystem tooling sees it as coming from IBM
at submission time: the contact address of the submission is an `ibm.com` one, or the source
code repository is in the [Qiskit GitHub organization](https://github.com/Qiskit).

Unlike the classifications above, this one is a flag and not a list of values, so it has no
short descriptions of its own. It is informative for users, and it is also what makes two
check ups apply: [`[I00]`](checkups.md#I00), which expects an IBM-maintained project to live
in an IBM-controlled GitHub organization, and [`[G11]`](checkups.md#G11), which turns the
recommendation of archiving an unmaintained repository into a stronger one when that
organization is IBM-controlled.

{{ read_raw('docs/assets/ibm-maintained.md') }}
