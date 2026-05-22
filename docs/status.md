# Membership status

All the members have a specific status in the Qiskit Ecosystem.
Most of them are regular **members**, which is the default status.

??? note "Short descriptions"
    {{ read_json('docs/assets/status.json') }}

## Members
There are 3 kind of members: Regular Members, Qiskit Projects, and projects Under revision 

### Regular members

{{ read_raw('docs/assets/member.md') }}

### Qiskit Project

{{ read_raw('docs/assets/qiskit-project.md') }}

### Under revision

If at some point one of the membership criteria checkup fails, then the status moves to **under review**.
Depending on how critical is the failing checkup, there is some cure period to remove the pending compliance.
If the failing check up persists or is not explained after this period, the project gets moved to _Alumni_ and removed from [the Qiskit Ecosystem website](http://qisk.it/ecosystem).

{{ read_raw('docs/assets/under-revision.md') }}

## Alumni

These projects are no longer in the Qiskit Ecosystem website, most probably because they no longer fulfill the criteria.
If you think there is a mistake, please [open an issue](https://github.com/Qiskit/ecosystem/issues/new?template=02_update.yml).

!!! tip
    An **alumni project can be reconsidered for Qiskit Ecosystem membership at any point**.
    Just PR the Qiskit Ecosystem repository removing the `member.status` entry in the project TOML file.

{{ read_raw('docs/assets/alumni.md') }}
