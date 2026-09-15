# Membership status

All the members have a specific status in the Qiskit Ecosystem.
Most of them are regular **members**, which is the default status.

Unlike [maturity](maturity.md), the status is not chosen by the submitter: it is derived automatically from the project data.

??? note "Short descriptions"
    {{ read_json('docs/assets/status.json') }}

## Members
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
It is also a counterweight to the self-reported [maturity](maturity.md): a submitter can declare a project as `production-ready`, but a repository created a few months ago carries this status next to that claim.

The status disappears on its own: as soon as the repository turns 12 months old, the next status update moves the project to a [regular member](#regular-members).
Projects with a pending [check up](#under-revision) are _Under revision_ instead, since that status takes precedence.

While a project is young, the activity [check ups](#under-revision) use a tighter window: instead of the flat 12 months since the last commit, a commit is expected within two thirds of the age of the repository (with a floor of 2 months), since a young project that stops committing has little track record to fall back on.

!!! tip
    _Very Early Projects_ are automatically excluded from the Qiskit Ecosystem website until they are 3 months old.
    Meanwhile, they are genuinely Qiskit Ecosystem members, so they can use their badge and have all the regular benefits.

{{ read_raw('docs/assets/early-projects.md') }}

<a id="unmaintained"></a>

### Unmaintained

A regular member whose self-declared [maturity](maturity.md) is `as-is` or `deprecated`, that is, a project with no active maintenance expectations.

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

## Alumni

These projects are no longer in the Qiskit Ecosystem website, most probably because they no longer fulfill the criteria.
If you think there is a mistake, please [open an issue](https://github.com/Qiskit/ecosystem/issues/new?template=02_update.yml).

!!! tip
    An **alumni project can be reconsidered for Qiskit Ecosystem membership at any point**.
    Just PR the Qiskit Ecosystem repository removing the `member.status` entry in the project TOML file.

{{ read_raw('docs/assets/alumni.md') }}
