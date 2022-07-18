
## creating a pull requests:

Steps on how to create a Pull Request are written below.
Click here for a <a href="https://www.youtube.com/watch?v=c6b6B9oN4Vg">video</a> explaining steps below please.

 - Fork the below github repository  <br/>
      <code> https://github.com/qiskit-community/ecosystem </code>
 - After the Fork and Clone the github repository in your local system  <br />
      <code> git clone git@github.com:<your_user_name>/ecosystem.git </code>
 - Keep your fork up-to-date  <br/>
      <code> git remote add upstream https://github.com/qiskit-community/ecosystem.git </code>
 - Checkout the Main branch and merge the up-stream   <br/>
      <code> git checkout main </code>   <br/>
      <code> git merge upstream/main </code>
 - Create a new branch in your clone to store your changes  <br/>
      <code> git checkout main </code>  <br/>
      <code> git branch new-branch </code>  <br/>
  - Switch to the created branch  <br/>
      <code> git checkout my-branch </code>
  - Do the necessary changes required for the PR, save your changes and add the files using git add  <br/>
      <code> git add <files_you_changed> </code>
  - Add the desired message to your commit using  <br/>
      <code> git commit -m "message" </code>
  - Push the changes to github  <br/>
      <code> git push --set-upstream origin new-branch </code>
  -create the pull request
    Go back to the browser and go to your fork of the project.
    At top of the repo, there should now be a button called "compare & pull request".
    Click that, enter your commit message and a comment, and then click "create new pull request"


  ## merging a pull request

   - Checkout the branch you're merging to in the target repo  <br/>

      <code> git checkout main </code>
  - Pull the development branch from the fork repo where the pull request development was done  <br/>
      <code> git pull https://github.com/forkuser/forkedrepo.git my-branch </code> 
  - Merge the development branch  <br/>
      <code> git merge newfeature </code>
  - Push master with the new feature merged into it  <br/>
      <code> git push origin main  </code> 
