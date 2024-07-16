# Project Overview

The Ecosystem consists of projects, tools, utilities, libraries and tutorials from a broad community of developers and researchers.
The goal of the Ecosystem is to recognize, support and accelerate development of quantum technologies using Qiskit.

## Contents

- [Background](#background)
- [Solution explanation](#solution-explanation)
  - [Adding project to the ecosystem](#adding-project-to-the-ecosystem)
  - [Storage](#storage)

## Background

As number of projects in Qiskit ecosystem is growing, we found it useful to create 
a curated list of libraries, open source repos, guides, games, demos, and other resources in order to
accelerate development of quantum technologies and provide more visibility for community projects.

## Solution Explanation

As entire repository is designed to be run through GitHub Actions,
we implemented ecosystem python package as runner of CLI commands
to be executed from steps in Actions. 

Entrypoint is ``manager.py`` file in the root of repository.

```shell
python manager.py <CMD> <NAME_OF_FUNCTION_IN_MANAGER_FILE> <POSITIONAL_ARGUMENT> [FLAGS]
```

### Adding project to the ecosystem

Anyone can add their project for review to be included in the ecosystem by
[submitting issue](https://github.com/qiskit-community/ecosystem/issues/new?assignees=octocat&labels=&template=submission.yml&title=%5BSubmission%5D%3A+).

### Storage

We store each member of the ecosystem as a TOML file under
[`ecosystem/resources/members`](https://github.com/qiskit-community/ecosystem/blob/main/ecosystem/resources/members);
these are the files you should edit when adding / updating members to the
ecosystem. Access to these files is handled programmatically through the
[`DAO`](https://github.com/qiskit-community/ecosystem/blob/main/ecosystem/daos/dao.py)
class.

### Webpage

To generate the ecosystem data from the TOML files, run:

```sh
tox -e website
```

Then open `website/ecosystem.json`. A GitHub action publishes the result of this command on every push to main.
This command also generates `website/index.html`, which is HTML file that redirects to the ecosystem page. This is needed because we used to host the ecosystem page on GitHub pages.
