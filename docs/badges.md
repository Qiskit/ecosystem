# Badges

Projects of the [Qiskit Ecosystem](https://qisk.it/ecosystem) are invited to proudly display it in their `README.md` file. 
For adding the badge to your project:

1. Find your project in the following table.
2. Copy the `markdown` code.
3. Paste it into your `README.md`.

??? note "Badges table for all projects"
    {{ read_raw('docs/assets/badges_table.md') }}

If you want to change the badge style, follow the instructions in [Change the badge style](#change-the-badge-style).

Additionally, the Qiskit Ecosystem badge is also a way to signal the project maintainer the [membership status](status.md):

If a project badge looks like ![under revision](https://img.shields.io/endpoint?url=https://qiskit.github.io/ecosystem/b/example_under-revision) this means that the project is not passing some of the Qiskit Ecosystem criteria and it is being considered for removal.
Check out the project page for details.
Once a project gets removed, their badge turn into ![under revision](https://img.shields.io/endpoint?url=https://qiskit.github.io/ecosystem/b/example_alumni)

## Change the badge style

To change the badge style, PR [the project toml file](https://github.com/Qiskit/ecosystem/tree/main/resources/members) changing the `badge.style` entry to one of these possible values:

`flat`: ![flat badge](https://img.shields.io/endpoint?url=https://qiskit.github.io/ecosystem/b/example_flat)

`flat-square`: ![flat-square badge](https://img.shields.io/endpoint?url=https://qiskit.github.io/ecosystem/b/example_flat-square)

`plastic`: ![plastic badge](https://img.shields.io/endpoint?url=https://qiskit.github.io/ecosystem/b/example_plastic)

`for-the-badge`: ![for-the-badge badge](https://img.shields.io/endpoint?url=https://qiskit.github.io/ecosystem/b/example_for-the-badge)

`social`: ![social badge](https://img.shields.io/endpoint?url=https://qiskit.github.io/ecosystem/b/example_social)

