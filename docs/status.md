# Membership status

All the members have a specific status in the Qiskit Ecosystem.
Most of them are regular **members**, which is the default status.

If at some point one of the membership criteria checkup fails, then the status moves to **under review**.
Depending on how critical is the failing checkup, there is some cure period to remove the pending compliance.
If the failing check up persists or is not explained after this period, the project gets moved to "alumni" and removed from [the Qiskit Ecosystem website](http://qisk.it/ecosystem).

!!! tip
    An **alumni project can be reconsidered to be a Qiskit Ecosystem member at any point**.
    Just PR the Qiskit Ecosystem repository removing the `member.status` entry in the project TOML file.   

??? note "Short descriptions"
    {{ read_json('docs/assets/status.json') }}

## Member

The project is an approved member of the Qiskit Ecosystem

## Alumni

The project used to be part of the Qiskit Ecosystem

## Under review

The project needs to review some of the check up issues to stay in the Qiskit Ecosystem

## Qiskit Project

Approved Qiskt Project
