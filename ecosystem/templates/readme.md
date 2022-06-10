# Ecosystem ![ecosystem](https://img.shields.io/badge/Qiskit-Ecosystem-blueviolet) [![Tests](https://github.com/qiskit-community/ecosystem/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/qiskit-community/ecosystem/actions/workflows/tests.yml)

<!-- PROJECT LOGO -->
<br />
<p align="center">
  <p align="center">
    <a href="https://qiskit.org/">
      <img alt="Qiskit" src="https://qiskit.org/images/qiskit-logo.png" width="70" />
    </a>
  </p>
  <h3 align="center">Ecosystem</h3>
</p>


<!-- TABLE OF CONTENTS -->
<details open="open">
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li><a href="#join-the-ecosystem">Join the Ecosystem</a></li>
    <li><a href="#members">Members</a></li>
    <li><a href="#contribution-guidelines">Contribution Guidelines</a></li>
    <li><a href="#license">License</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

The Ecosystem consists of projects, tools, utilities, libraries and tutorials from a broad community of developers and researchers.
The goal of the Ecosystem is to recognize, support and accelerate development of quantum technologies using Qiskit.



## [Join the Ecosystem](https://github.com/qiskit-community/ecosystem/issues/new?labels=&template=submission.yml&title=%5BSubmission%5D%3A+)

To join the Ecosystem create a [submission issue](https://github.com/qiskit-community/ecosystem/issues/new?labels=&template=submission.yml&title=%5BSubmission%5D%3A+)
- To know more about how to pass the submission form, check the **[Notice](https://github.com/qiskit-community/ecosystem/tree/main/docs/notice.md)**


## Members ![ecosystem](https://img.shields.io/badge/Qiskit-Ecosystem-blueviolet)

{% for tier, repos in data %}
### {{ tier.capitalize() }} ![ecosystem-{{tier}}](https://img.shields.io/badge/Qiskit-{{tier.capitalize()}}-blueviolet)

|  Name | Description  |
|---|---|
{% for repo in repos -%}
| [{{ repo.name }}]({{ repo.url }}) | {{repo.description}} <br/> {% for label in repo.labels %} ![core](https://img.shields.io/badge/{{label}}-gray.svg) {% endfor %} <br/> {% for test in repo.tests_passed %} ![core](https://img.shields.io/badge/tests-{{test}}-green.svg) {% endfor %}|
{% endfor %}
{% endfor %}


## Contribution Guidelines

See the [contributing](./CONTRIBUTING.md) document to learn about the source code contribution process developers follow.

See the [code of conduct](./CODE_OF_CONDUCT.md) to learn about the social guidelines developers are expected to adhere to.

See the [open issues](https://github.com/qiskit-community/ecosystem/issues) for a list of proposed features (and known issues).



## License

Distributed under the Apache License. See [LICENSE.txt](./LICENSE) for more information.
