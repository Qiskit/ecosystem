---
hide:
  - edit
---

# Qiskit Ecosystem project overview

The Qiskit Ecosystem consists of projects, tools, utilities, libraries and tutorials from a broad community of developers and researchers.
The goal of the Ecosystem is to recognize, support and accelerate development of quantum technologies using Qiskit.

## Contents

- [Background](#background)
  - [Adding a project to the ecosystem](#adding-a-project-to-the-ecosystem)
- [Check ups](#check-ups)
  - [Importance and cure period](#importance-and-cure-period)
  - [Categories](#categories)
  - [When automation runs](#when-automation-runs)
  - [How a failing check up is recorded](#how-a-failing-check-up-is-recorded)
  - [Check ups that are not tests](#check-ups-that-are-not-tests)
  - [Expected failures](#expected-failures)
  - [The whole list](#the-whole-list)
- [For project maintainers](#for-project-maintainers)
- [Architecture](#architecture)
  - [Storage](#storage)
  - [Webpage](#webpage)

## Background

As number of projects in Qiskit ecosystem is growing, we found it useful to create 
a curated list of libraries, open source repos, guides, games, demos, and other resources in order to
accelerate development of quantum technologies and provide more visibility for community projects.

### Adding a project to the ecosystem

Anyone can add their project for review to be included in the ecosystem by
[submitting an issue](https://qisk.it/add-to-ecosystem/).
A submission is reviewed against the same [check ups](#check-ups) that keep running afterwards,
so a project joins by passing them and stays by keeping them passing.

## Check ups

Membership in the Qiskit Ecosystem is not a one-time decision: it is checked continuously.
A **check up** is a single, named membership criterion, such as _"have a commit within the last 12 months"_ or _"have an OSI-approved license"_.

Every check up has:

- an **id** of three characters, like `[G07]` or `[001]`, which is what shows up in the project pages and in the project data,
- an **importance**, which determines how much time there is to fix it (see [below](#importance-and-cure-period)),
- a **category**, which says what kind of criterion it is (see [below](#categories)),
- an **applies to**, since not every criterion makes sense for every project. For example, `Python packages` check ups are only run on projects that publish to PyPI.

All the check ups are declared in
[`resources/checks.toml`](https://github.com/Qiskit/ecosystem/blob/main/resources/checks.toml),
which is the single source of truth: the [check up list](checkups.md) and every project page are generated from it.
Most check ups also declare a `checker`, which is the [PyTest](https://docs.pytest.org) test that implements them, under
[`ecosystem/validation/`](https://github.com/Qiskit/ecosystem/tree/main/ecosystem/validation).
For instance, `[G07]` is implemented by `test_github.py::test_G07`.

### Importance and cure period

Every check up has a **cure period**: how many days a member can keep failing it before losing its
membership. A cure period of _0 days_ means the check up has to pass at all times, while
_no deadline_ (`cure_period_in_days = -1`) means the opposite: the check up shows up as pending, so
the project is [_Under revision_](status.md#under-revision), but it never retires the project on
its own.

The cure period is a property of the check up, and most check ups do not state one: they take the
default of their importance level.

{{ read_raw('docs/assets/checkup-importance.md') }}

The cure period each check up ends up with is in the [check up list](checkups.md).

### Categories

{{ read_raw('docs/assets/checkup-categories.md') }}

### When automation runs

All the automation run by [GitHub Actions](https://github.com/Qiskit/ecosystem/tree/main/.github/workflows):

- **Daily**, `Daily | Update member data` refreshes the data that the check ups look at (GitHub repository activity, PyPI and Julia package metadata, ...) and commits it into the project files.
  This is why a fix in a project can take a day to be visible, and a release can take a day to be noticed.
- **Weekly** (Thursdays), `Weekly | Update member status` runs `python manager.py members update_checkups` on every non-alumni member, and then recomputes the [membership status](status.md) with `python manager.py members update_status`.
  The result is not pushed directly: it opens a pull request labeled `member update`, so a human reviews any status change before it reaches the website.
- Both commands take `-e`, a list of things to leave out of the run. A value is a check up
  [importance](#importance-and-cure-period) or [category](#categories) ("a check up of this kind
  does not change the status"), or a [membership status](status.md) ("projects already in this
  status are left alone"). So the weekly run is `update_checkups -e alumni` followed by
  `update_status -e "recommendation, alumni, qiskit-project"`: alumni stay alumni, _Qiskit
  Projects_ are governed differently, and a recommendation alone is not enough to put a project
  under revision.
- **On submission and on member updates**, `Member validations` runs the check ups on the single project of the pull request.
  A new candidate has to pass everything but the recommendations before it can be merged.

### How a failing check up is recorded

Each member is a TOML file under
[`resources/members`](https://github.com/Qiskit/ecosystem/tree/main/resources/members).
A check up that does not pass is stored there as a `[checks.<ID>]` table:

```toml
[checks.P10]
since = 2026-07-09
details = "Python package qiskit-algorithms declared itself compatible to a not-yet-released major version of Qiskit"
```

- `since` is the date the check up started failing. It is **not** reset while the check up keeps failing, so `since` + cure period is the deadline.
- `details` is the assertion message of the checker: the concrete reason, with the offending package, URL or date.
- `discussion` and `source` may point to the issue where the situation is being discussed or tracked.

A passing check up leaves no trace: if the failure is fixed, the whole `[checks.<ID>]` table disappears on the next weekly run, and with it the deadline.

### Check ups that are not tests

Some criteria cannot be tested automatically: whether a project [interfaces with Qiskit in a meaningful way](checkups.md#000), for example, or whether a primitive implementation is [V2-compatible](checkups.md#020).
Those check ups have no `checker`.
Instead, they are created by a human and carry a `source`, the URL of the GitHub issue where the problem is tracked, usually in the project's own repository:

```toml
[checks.Q20]
since = 2026-09-15
source = "https://github.com/rigetti/qiskit-rigetti/issues/53"
```

For these, the weekly run does not execute a test: it looks at the state of that issue.
If the issue is closed, that is noted in `details` (`the source issue is closed as completed`, for instance) and a human decides what to do.
A closed issue does not remove the check up by itself, because closing an issue does not necessarily mean the situation is solved.

### Expected failures

A check up can be failing for a good reason.
In that case, a maintainer of the Qiskit Ecosystem adds an `xfailed` entry with the explanation, and the failure stops counting towards the membership status:

```toml
[checks.G07]
xfailed = "The project is feature-complete and the maintainers still answer issues"
xfailed_until = 2027-01-31
```

`xfailed_until` is optional and makes the explanation expire.
An explanation without it never expires.
Once the date passes, the check up is evaluated as a regular one again, which is a way of saying _"this is fine for now, let us look at it again in six months"_.

### The whole list

Every check up, with the projects that are currently failing it, is listed in
[Check ups](checkups.md).

## For project maintainers

Your project is a member of the Qiskit Ecosystem, and the [check ups](#check-ups) above run on it every week.
Here is what that means in practice.

### Where to see how your project is doing

Your project page (`https://qiskit.github.io/ecosystem/p/<short uuid>/`) has a **Checkups** section.
If everything passes, it says _All good_.
Otherwise, it lists one line per failing check up: the icon is the [importance](#importance-and-cure-period), the `[ID]` links to [that check up](checkups.md), and the text is the concrete reason.

The [badge](badges.md) is the other signal: it turns orange when the project is _Under revision_, so adding it to your `README.md` is also a way of noticing that something needs your attention.

### What happens if a check up fails

Failing a check up is not an immediate removal, unless its importance is `CRITICAL`.
The project moves to the [_Under revision_](status.md#under-revision) status and the cure period of the check up starts counting from its `since` date.
If it is still failing (and unexplained) when the cure period is over, the project becomes [_Alumni_](status.md#alumni) and is removed from [the website](https://qisk.it/ecosystem).

Being _Alumni_ is reversible: a project can be reconsidered at any point by opening a pull request that removes the `member.status` entry from its TOML file.

### What you can do about it

1. **Fix it upstream.** Most check ups look at your repository or at your published packages, so the fix lives there: a release compatible with the latest Qiskit, a `LICENSE` file GitHub can recognize, a commit. The data is refreshed daily and the check ups run weekly, so give it a few days before worrying.
2. **Fix the metadata.** Some check ups are about what the Qiskit Ecosystem knows about your project (a broken URL, a too-long description, a wrong category). Those are fixed in your project's TOML file, either with a pull request to [this repository](https://github.com/Qiskit/ecosystem) or by [opening an update issue](https://github.com/Qiskit/ecosystem/issues/new?template=02_update.yml).
3. **Explain it.** If a check up genuinely does not apply to your project, say so in an issue. If we agree, it is recorded as an [expected failure](#expected-failures) and stops affecting your status.
4. **Declare your support expectations.** A project that is intentionally not maintained anymore is not a problem, as long as it says so: setting the [maturity](maturity.md) to `as-is` or `deprecated` marks it as [_Unmaintained_](status.md#unmaintained) and exempts it from the activity check ups.

### Where to ask

- Open an issue in [the Qiskit Ecosystem repository](https://github.com/Qiskit/ecosystem/issues).
- Ask in the [`#qiskit-ecosystem` Slack channel](https://qiskit.slack.com/archives/C04RHE56N93) ([sign up](https://qisk.it/join-slack) if you are not in the workspace yet).

## Architecture

The rest of this page is about how the repository itself is put together, which is what you
need when changing the Qiskit Ecosystem rather than taking part in it.

Everything is designed to run through GitHub Actions, so the `ecosystem` Python package is a
runner of CLI commands to be executed from steps in those workflows. There is no server and no
database: the member files in the repository are the data, and the website is a build artifact.

The entrypoint is the ``manager.py`` file in the root of the repository.

```shell
python manager.py <CMD> <NAME_OF_FUNCTION_IN_MANAGER_FILE> <POSITIONAL_ARGUMENT> [FLAGS]
```

The commands that run the check ups (`members update_checkups` and `members update_status`) are
the ones described in [When automation runs](#when-automation-runs).

### Storage

We store each member of the ecosystem as a TOML file under
[`resources/members`](https://github.com/Qiskit/ecosystem/tree/main/resources/members);
these are the files you should edit when adding / updating members to the
ecosystem. Access to these files is handled programmatically through the
[`DAO`](https://github.com/Qiskit/ecosystem/blob/main/ecosystem/dao.py)
class.

### Webpage

This documentation site is built with [MkDocs](https://www.mkdocs.org) from the `docs/` directory.
Some of its pages are not written by hand: the project pages under `docs/p/` are generated at build
time from the member files, and the tables injected with `read_raw`/`read_json` come from
`docs/assets/`, which is regenerated by `python manager.py members update_docs_assets`.

To build everything, run:

```sh
tox -e website
```

The result lands in `website/`, and a GitHub action publishes it on every push to main.
Besides the pages, the command generates:

- `website/ecosystem.json`, the machine-readable dump of all the member data,
- `website/b/`, the [shields.io](https://shields.io) endpoints behind the [badges](badges.md),
- `website/index.html`, an HTML file that redirects to the ecosystem page. This is needed because we
  used to host the ecosystem page on GitHub pages, so it overwrites the index that MkDocs generates.
