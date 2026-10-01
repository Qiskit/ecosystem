# Ecosystem Validations

This directory holds the [PyTest](https://docs.pytest.org) tests that implement the Qiskit Ecosystem
check ups. Each test is wired to a check up through the `checker` field in
[`resources/checks.toml`](../../resources/checks.toml), which is the single source of truth for the
check up ids, titles, descriptions, categories, importance levels and cure periods.

Documentation lives on the website, generated from that file:

- **[How the check ups work](https://qiskit.github.io/ecosystem/overview/#check-ups)**: when they
  run, how a failure is recorded, expected failures, and the full catalog.
- **[For project maintainers](https://qiskit.github.io/ecosystem/overview/#for-project-maintainers)**:
  what to do when a check up fails on your project.
- **[Membership status](https://qiskit.github.io/ecosystem/classifications/#status)**: how failing check ups move a
  project to _Under revision_ and eventually to _Alumni_.

The files here are `checkup_*.py` and the check ups in them are `checkup_*` functions, not pytest's
default `test_*`: the unit tests of this repository live in [`tests/`](../../tests) and are run by
CI, while these run once a week against the member data, so neither suite should ever collect the
other one. That takes telling pytest the names, which `CHECKUP_COLLECTION` in
[`__init__.py`](__init__.py) does for every run that collects them.

To add a check up, add its entry to `resources/checks.toml` and, if it can be tested automatically,
the check up here that the entry's `checker` points to.
