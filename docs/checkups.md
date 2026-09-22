---
hide:
  - edit
---

# Check ups

A **check up** is a single, named membership criterion of the Qiskit Ecosystem, such as
_"have a commit within the last 12 months"_ or _"have an OSI-approved license"_.
They are re-run on every member every week, so this page is the current state of the whole
ecosystem: each check up, and the projects it is failing right now.

A failing check up is not a removal. It moves the project to
[_Under revision_](classifications.md#under-revision) and starts its
[cure period](overview.md#importance-and-cure-period); only when that period runs out without
the check up being fixed or explained does the project become [_Alumni_](classifications.md#alumni).
See [how the check ups work](overview.md#check-ups) for the mechanism, and
[for project maintainers](overview.md#for-project-maintainers) if one of these is on your
project.

??? note "All the check ups"
    {{ read_json('docs/assets/checkup.json') }}

{{ read_raw('docs/assets/checkup.md') }}
