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
<code> python manager.py python_stable_tests <url_of_the github_repository> --python_version=py39 --run_name="stable"</code>
2. To run tests against the dev version of qiskit  <br/>
<code> python manager.py  python_dev_tests  <url_of_the github_repository> --python_version=py39 --run_name="dev"</code>
3. To run tests within repository  <br/>
<code> python manager.py python_standard_tests <url_of_the github_repository> --python_version=py39 --run_name="standard"</code>

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

# Create a preview of the website from your fork

When you contribute to the ecosystem website, you can provide a preview of your changes in your pull request to make the review process more visual. To create a preview, once you have your changes in a branch on your fork, you need to:
- Go to your Fork
- Click `Settings`
- Go to `Environments`
- Click `github-pages`
- Go to the `Deployment branches and tags` section
- Select `No restriction` in the `Deployment branches` dropdown or add a new branch/tag rule to enable the deployment from your branch

Once we have the environment ready, we need to configure the deployment using GitHub Actions:

- Go to your Fork
- Click `Settings`
- Go to `Pages`
- Select `GitHub Actions` in the `source` dropdown on `Build and deployment`

Finally, we need to trigger the deployment from GitHub Actions:
- Go to your Fork
- Go to `Actions`
- Click `Deploy Website` on the left menu
- Use the `Run workflow` dropdown on the top right corner
- Select the branch with your changes and click `Run workflow` to start the deployment

When the deployment finishes, your preview will be ready at https://username.github.io/ecosystem/ if you don't change the default link.

# Guidance on git
Please follow [this link](./docs/git-guidance.md) if this is your first time contributing to open source and/or you would like some guidance on how to create and/or merge
pull requests.
        

## Dev contributions
[Internals overview](./docs/project_overview.md)
