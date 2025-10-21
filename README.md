<!--lint ignore double-link-->

# Qiskit ecosystem

![ecosystem](https://img.shields.io/badge/Qiskit-Ecosystem-blueviolet)
[![Awesome](https://awesome.re/badge.svg)](https://awesome.re)
[![Sourcecode tests](https://github.com/Qiskit/ecosystem/actions/workflows/tests.yml/badge.svg)](https://github.com/Qiskit/ecosystem/actions/workflows/tests.yml)

<!--lint enable double-link-->

## About the ecosystem

The Qiskit Ecosystem is a collection of software and tutorials that builds on or extends Qiskit.
The goal of the Ecosystem is to celebrate, support, and accelerate development of quantum technologies using Qiskit.
View all projects at [www.ibm.com/quantum/ecosystem](https://www.ibm.com/quantum/ecosystem).

This repository handles submissions to the ecosystem and builds the web page.


## How to join

Simply fill in the [submission issue form](https://qisk.it/add-to-ecosystem).
This will automatically create a pull request adding your project to this repository.
We'll review the pull request and get back to you within a few days.

To join the ecosystem, your project must:
  - Build on, interface with, or extend the [Qiskit SDK](https://github.com/Qiskit/qiskit) in a meaningful way.
  - Be compatible with the Qiskit SDK v1.0 (or newer).
  - Have an [OSI-approved](https://opensource.org/license?categories=popular-strong-community) open-source license (preferably Apache 2.0 or MIT).
  - Adhere to our [code of conduct](./CODE_OF_CONDUCT.md) (you can enforce your own code of conduct in addition to this).
  - Have maintainer activity within the last 6 months, such as a commit.
  - New projects should be compatible with the [V2 primitives](https://docs.quantum.ibm.com/migration-guides/v2-primitives).

Once your submission has been approved and merged, it will appear on [www.ibm.com/quantum/ecosystem](https://www.ibm.com/quantum/ecosystem) within a few days.

### Add the badge to your `README.md`

Once your project is part of the Qiskit Ecosystem, you can add the badge to your `README.md`:

1. Go to your project’s file in [`./ecosystem/resources/members`](https://github.com/qiskit-community/ecosystem/tree/main/ecosystem/resources/members).
2. Copy the value of the `badge =` entry (without the double quotes).
3. Paste it into your `README.md`.

You can change the badge style by changing `style=` in the url (see [shields.io for more information](https://shields.io/badges/endpoint-badge). 

## How to update project information

To change your project's information, edit your project's file in [`./ecosystem/resources/members`](https://github.com/qiskit-community/ecosystem/tree/main/ecosystem/resources/members)
and make a pull request with the updated information.
You can also [open an issue](https://github.com/qiskit-community/ecosystem/issues/new?template=update.yml) asking us to do it, or asking us to remove your project from the Ecosystem.

## Contribution Guidelines

See the [contributing](./CONTRIBUTING.md) document to learn about the source code contribution process developers follow.

See the [code of conduct](./CODE_OF_CONDUCT.md) to learn about the social guidelines developers are expected to adhere to.

See the [open issues](https://github.com/qiskit-community/ecosystem/issues) for a list of proposed features (and known issues).


## Automatic updates

Each week, a [GitHub Action](.github/workflows/weekly-badge-and-stats-update.yml) runs to update member stats and badges.
It automatically [creates a pull request](https://github.com/Qiskit/ecosystem/issues?q=label%3A%22member%20update%22) that needs to be reviewed and merged by a maintaner.
[![Weekly | Update stats and badges](https://github.com/Qiskit/ecosystem/actions/workflows/weekly-badge-and-stats-update.yml/badge.svg)](https://github.com/Qiskit/ecosystem/actions/workflows/weekly-badge-and-stats-update.yml)
