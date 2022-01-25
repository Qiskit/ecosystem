# Notice
This file explain what are the miniam requierements to be able to add your project in the **Qiskit Ecosystem**.

## Table of content
- [Requierements](#requierements)
  - [Files minimal](#minimal)  
  - [lint](#lint)  
  - [tests / coverage](#tests) 
  - [qiskit](#qiskit)  
- [Project template](#template)


## Requierements <a class="anchor" id="requierements"></a>

### Files minimal <a class="anchor" id="minimal"></a>
- ecosystem.json
  - Should content the command you use to run your pylint, coverage, black and unitests. Also should content the name of your requierements file, etc...
  <details><summary>Example :</summary>
  <pre>
  {
    "dependencies_files": [
        "requirements.txt",
        "requirements-dev.txt"
    ],
    "extra_dependencies": [
        "pytest"
    ],
    "language": {
        "name": "python",
        "versions": ["3.9"]
    },
    "tests_command": [
        "pytest"
    ],
    "styles_check_command": [
        "pylint -rn src tests"
    ],
    "coverages_check_command": [
        "coverage3 run -m pytest",
        "coverage3 report --fail-under=80"
    ]
  }
  </pre>
  </details> 
  
- requierements.txt
  - Should content all of your dependance to install in order to run your project

### lint <a class="anchor" id="lint"></a>
Your project have to match our style requierement, the template file for pylintrc is as follow --> [here](https://github.com/qiskit-community/ecosystem/blob/main/ecosystem/templates/.pylintrc)
If you have lot of issue, try using [black](https://pypi.org/project/black/) at first, that'll correct lot of them as we are following their practices.
If you need some custom, please add the option in the `styles_check_command` of your `ecosystem.json`.

### tests / coverage <a class="anchor" id="tests"></a>
Your project have to be cover by a minimun of 80% of tests. And should follow our coverage requierements --> [here](https://github.com/qiskit-community/ecosystem/blob/main/ecosystem/templates/.coveragerc)
If you need some custom in your test command or coverage check command, please add the option in the `coverages_check_command or tests_command` of your `ecosystem.json`.

### qiskit <a class="anchor" id="qiskit"></a>
Our final requierement is to be compatible without any warning or breaking change with the latest stable version of Qiskit. Also we ask to be compatible with the beta version of Terra (no breaking change) in order to be ready for futur release and prevent bug.

## [Project template](https://github.com/mickahell/qiskit-ecosystem_template) <a class="anchor" id="template"></a>
A project template as been create with all the minimal requierements and automatisation to checks the tests, coverage, styles and qiskit compatibilities along the life time of your project. You can use it as github repo template when you create your project or copying the config files.  
**Find it --> [here](https://github.com/mickahell/qiskit-ecosystem_template)**
