# Contributing

First read the overall project contributing guidelines. These are all
included in the qiskit documentation:

https://qiskit.org/documentation/contributing_to_qiskit.html

## Joining the Ecosystem
To join ecosystem you need to create 
[submission issue](https://github.com/qiskit-community/ecosystem/issues/new?labels=&template=submission.yml&title=%5BSubmission%5D%3A+) 
and fill in all required details. That's it!


# Installation and environment setup 
1.Create new environment   <br/>
<code> conda create --name ecosystem python=3.9  </code> <br/> 
2. Activate the environment  <br/>
<code> conda activate ecosystem  </code> <br/> 
3. install dependencies  <br/>
<code>
pip install -r requirements.txt
pip install -r requirements-dev.txt
</code> 


# Running the tests
1. To run tests against the stable version of qiskit  <br/>
<code> python manager.py stable_compatibility_tests <url_of_the github_repository></code>
2. To run tests against the dev version of qiskit  <br/>
<code> python manager.py  dev_compatibility_tests  <url_of_the github_repository></code>
3. To run tests within repository  <br/>
<code> python manager.py python_standard_tests <url_of_the github_repository></code>

# Performing style checks
- Run for style checks 
  <code> tox -elint </code>
- Run for tests 
  <code> tox -epy39 </code>
- Run coverage 
  <code> tox -ecoverage </code>
- Run black 
   <code> tox -eblack </code>
- To Fix the black violation  <code> black <PATH_FILE_YOU_WANT_TO_FIX> </code>

# Guidance on git
Please follow <a>this link</a> if this is your first time contributing to open source and/or you would like some guidance on how to create and/or merge
pull requests.
        

## Dev contributions
[Refer to dev docs](./docs/dev/dev-doc.md)
