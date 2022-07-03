<!--lint ignore double-link-->

# Ecosystem ![ecosystem](https://img.shields.io/badge/Qiskit-Ecosystem-blueviolet) [![Awesome](https://awesome.re/badge.svg)](https://awesome.re) [![Tests](https://github.com/qiskit-community/ecosystem/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/qiskit-community/ecosystem/actions/workflows/tests.yml)

<!--lint enable double-link-->

<br />
<p align="center">
  <p align="center">
    <a href="https://qiskit.org/">
      <img alt="Qiskit" src="https://qiskit.org/images/qiskit-logo.png" width="70" />
    </a>
  </p>
  <h3 align="center">Ecosystem</h3>
</p>

## Contents
1. [About The Project](#about-the-project)
2. [Join the Ecosystem](#join-the-ecosystem)
3. [Members](#members)
4. [Contribution Guidelines](#contribution-guidelines)


## About The Project

The Ecosystem consists of projects, tools, utilities, libraries and tutorials from a broad community of developers and researchers.
The goal of the Ecosystem is to recognize, support and accelerate development of quantum technologies using Qiskit.

[Read more about this project](./docs/project_overview.md).

## [Join the Ecosystem](https://github.com/qiskit-community/ecosystem/issues/new?labels=&template=submission.yml&title=%5BSubmission%5D%3A+)

To join the Ecosystem create a [submission issue](https://github.com/qiskit-community/ecosystem/issues/new?labels=&template=submission.yml&title=%5BSubmission%5D%3A+)


## Members

{% for tier, repos in data %}

<details>
  <summary>
    <b>{{ tier.capitalize() }}</b> ({{ repos|length }})
  </summary>
  
<hr/>
<img src="https://img.shields.io/badge/Qiskit-{{tier.capitalize()}}-blueviolet">

|  Name | Description  |
|---|---|
{% for repo in repos -%}
| [{{ repo.name }}]({{ repo.url }}) | {{repo.description}} <br/> {% for label in repo.labels %} ![core](https://img.shields.io/badge/{{label}}-gray.svg) {% endfor %} <br/> {% for test in repo.tests_passed %} ![core](https://img.shields.io/badge/tests-{{test}}-green.svg) {% endfor %}|
{% endfor %}
<hr/>

</details>

{% endfor %}


## Contribution Guidelines

See the [contributing](./CONTRIBUTING.md) document to learn about the source code contribution process developers follow.

See the [code of conduct](./CODE_OF_CONDUCT.md) to learn about the social guidelines developers are expected to adhere to.

See the [open issues](https://github.com/qiskit-community/ecosystem/issues) for a list of proposed features (and known issues).

