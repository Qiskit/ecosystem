# Ecosystem Validations


Once your project is part of the [Qiskit Ecosystem website](https://qisk.it/ecosystem), some checks will be ran on the project regularly.
If your project file has one or more `[validation.*]` entries, it is because some of those validation checks failed on the project.

<details>
<summary>Joining criteria</summary>

To join the Qiskit Ecosystem, a project must:

  - [[000](#000)] Build on, interface with, or extend the [Qiskit SDK](https://github.com/Qiskit/qiskit) in a meaningful way.
  - [[Q20](#Q20)] Be compatible with the Qiskit SDK v2.0 (or newer).
  - [[001](#001)] Have an [OSI-approved](https://opensource.org/license?categories=popular-strong-community) open-source license (preferably Apache 2.0 or MIT).
  - [[COC](#COC)] Adhere to the [Qiskit code of conduct](https://qisk.it/coc) (you can enforce your own code of conduct in addition to this).
  - [[G00](#G00)] Have maintainer activity within the last 6 months, such as a commit.
  - [[P20](#P20)] New projects should be compatible with the [V2 primitives](https://docs.quantum.ibm.com/migration-guides/v2-primitives).

</details>

---

### Build on, interface with, or extend the Qiskit in a meaningful way <a id='000'></a>

|   id  | applies to | category | related to |
|  :---:  | :---: | :---: | :---: |
|`[000]`|     all    | GENERAL


Software in the Qiskit Ecosystem should related to Qiskit projects in some meaningful way.
Software that manipulate Qiskit data structure (such as transpiler plugins) are good examples of that.
If the connection with Qiskit is not that obvious, consider having a tutorial or how-to guide explaining a use-case for Qiskit users.

---

### <a id='001'>Have an OSI-approved license</a>

|   id  | applies to | category | related to |
|  :---:  | :---: | :---: | :---: |
|`[001]`|     all    | GENERAL

Software in the Qiskit Ecosystem should be licensed with an OSI-approved open-source license.
While Apache 2.0 or MIT are preferred, [any license approved by OSI](https://opensource.org/license) is acceptable.

---

<h3 id="COC">Adhere to the Qiskit CoC</h3>

|   id  | applies to | category | related to |
|  :---:  | :---: | :---: | :---: |
|`[COC]`|     all    | GENERAL

Project submitters should adhere to the [Qiskit code of conduct](https://qisk.it/coc).
If the submitter is the project maintainer, they can enforce your their code of conduct in addition to the one coming from Qiskit.

---

### <a id='Q20'>Be compatible with the Qiskit SDK v2 or newer</a>


|   id  | applies to | category | related to |
|  :---:  | :---: | :---: | :---: |
|`[Q20]`|     all    | GENERAL

If the software depends on Qiskit SDK, there should exist a supported released that is compatible with the Qiskit SDK v2.0 or newer.

---

### <a id='G06'>Have maintainer activity within the last 6 months</a>


|   id  | applies to | category | related to |
|  :---:  | :---: | :---: | :---: |
|`[G06]`| GitHub projects | GENERAL

Projects available on GitHub should have some activity within the last 6 months, such as a commit.


---

### <a id='PQ1'>Be installable with `qiskit>=1.0`</a>


|   id  | applies to | category | related to |
|  :---:  | :---: | :---: | :---: |
|`[PQ1]`| Python packages | GENERAL


If the project build Python packages that depend on Qiskit SDK, they all should be installable with `qiskit >=1.0`.


---

### <a id='PQ1'>Python package license-related metadata should be OSI-approved</a>


|   id  | applies to | category | related to |
|  :---:  | :---: | :---: | :---: |
|`[PQ1]`| Python packages | GENERAL


If the project build Python packages that depend on Qiskit SDK, the license-related metadata of all of them should be an [OSI-approved](https://opensource.org/license?categories=popular-strong-community) open-source license.

---

### <a id='P20'>Primitive interface should be v2-compatible</a>


|   id  | applies to | category | related to |
|  :---:  | :---: | :---: | :---: |
|`[P20]`| label:"Compute provider" | GENERAL


If the project implements a Qiskit primitive interface, it should be compatible with the [V2 primitives](https://docs.quantum.ibm.com/migration-guides/v2-primitives) API.

---


