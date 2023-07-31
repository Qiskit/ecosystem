Ecosystem database
==================

This folder contains the actual ecosystem data, including the data that appears
on [qiskit.org/ecosystem](https://qiskit.org/ecosystem).

If you want to edit or remove something, go to the [`members`](./members)
folder and edit or delete the TOML file for that repo. On pushing to `main`, a
GitHub action should recompile the JSON files that
[qiskit.org/ecosystem](https://qiskit.org/ecosystem) reads from.
