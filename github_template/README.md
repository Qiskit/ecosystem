# My awesome Project !
- This project is a template project with everything need to be add inside the __Qiskit Ecosystem__.
- The workflows inside this template are the same than the one running adding and weekly checks.

## Structure
- .pylinrc : config file for python linter
- .coveragerc : config file for python coverage
- tox.ini : file for running tox cmd
- .gitignore : python gitignore content
- requirements.txt : install for running project
- requirements-dev.txt : install for dev the project
- setup.py : python module/package configuration
- setup.cfg : python module/package configuration
- ecosystem.json : config file for Ecosystem testing
- src/ : repository for all the source of the project
- tests/ : repository for the units tests of the project

## Tests execution
- Run for style checks `tox -elint`
- Run for tests `tox -epy39`
- Run coverage `tox -ecoverage`
- Run black `tox -eblack`
  - Run black on unitary file `black <file>`

## Actions
- The worflow tests.yml is here to tests automatically the units tests, coverage lint and black at every push.

### Qiskit actions
- The workflows qiskit.yml is here to tests the project are still update with the actual and dev version of Qiskit.
