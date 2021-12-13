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
<code> python manager.py stable_compatibility_tests <url_of_the github_repository> --tox_python=py39 </code>
2. To run tests against the dev version of qiskit  <br/>
<code> python manager.py  dev_compatibility_tests  <url_of_the github_repository> --tox_python=py39 </code>
3. To run tests within repository  <br/>
<code> python manager.py standard_tests <url_of_the github_repository> --tox_python=py39 </code>

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
 - Fork the below github repository  <br/>
      <code> https://github.com/qiskit-community/ecosystem </code>
 - After the Fork and Clone the github repository in your local system  <br />
      <code> git clone git@github.com:<your_user_name>/ecosystem.git </code>
 - Keep your fork up-to-date  <br/>
      <code> git remote add upstream https://github.com/qiskit-community/ecosystem.git </code>
 - Checkout the Master branch and merge the up-stream   <br/>
      <code> git checkout master </code>   <br/>
      <code> git merge upstream/master </code>
 - Create a new branch in your clone to store your changes  <br/>
      <code> git checkout master </code>  <br/>
      <code> git branch new-branch </code>  <br/>
  - Switch to the created branch  <br/>
      <code> git checkout my-branch </code>
  - Do the necessary changes required for the PR, save your changes and add the files using git add  <br/>
      <code> git add <files_you_changed> </code>
  - Add the desired message to your commit using  <br/>
      <code> git commit -m "message" </code>
  - Push the changes to github  <br/>
      <code> git push --set-upstream origin new-branch </code>
  - Checkout the branch you're merging to in the target repo  <br/>
      <code> git checkout master </code>
  - Pull the development branch from the fork repo where the pull request development was done  <br/>
      <code> git pull https://github.com/forkuser/forkedrepo.git my-branch </code> 
  - Merge the development branch  <br/>
      <code> git merge newfeature </code>
  - Push master with the new feature merged into it  <br/>
      <code> git push origin master  </code> 
        
# Contributing

First read the overall project contributing guidelines. These are all
included in the qiskit documentation:

https://qiskit.org/documentation/contributing_to_qiskit.html

## Joining the Ecosystem
To join ecosystem you need to create 
[submission issue](https://github.com/qiskit-community/ecosystem/issues/new?labels=&template=submission.yml&title=%5BSubmission%5D%3A+) 
and fill in all required details. That's it!

## Dev contributions
[Refer to dev docs](./docs/dev/dev-doc.md)
