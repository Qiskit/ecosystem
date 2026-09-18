# Contributing

## Joining the Ecosystem
To join ecosystem you need to create 
[submission issue](https://qisk.it/add-to-ecosystem/) 
and fill in all required details. That's it!


# Installation and environment setup 
1. Create new environment:
```
conda create --name ecosystem python=3.13
```
2. Activate the environment:
```
conda activate ecosystem
```
3. Install dependencies:
```
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

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

# Create a preview of the website
1. Build the website: `tox -ewebsite`
2. Go to the `website/` folder in the root of your project and open up `index.html` in a browser

## Live preview with `mkdocs serve`
For a faster loop while editing the docs you can run MkDocs directly, but first
install the package and generate the docs assets:
1. Install the `ecosystem` package (needed by the `gen-files` plugin):
```
pip install -e .
```
2. Generate the files in `docs/assets/`:
```
python manager.py members update_docs_assets
```
3. Serve the docs with live reload:
```
mkdocs serve
```

The fragments in `docs/assets/` (the tables injected into `status.md`,
`summary.md`, `categories.md`, etc. by the `table-reader` plugin) are generated
and not tracked in git. Step 2 is what `tox -ewebsite` does for you, so if you
skip it `mkdocs serve` fails with an error like `[table-reader-plugin]: Cannot
find table file 'docs/assets/unmaintained.md'`. Re-run it whenever you change
member data under `resources/`.

# Guidance on git
Please follow [this link](./docs/git-guidance.md) if this is your first time contributing to open source and/or you would like some guidance on how to create and/or merge
pull requests.
        

## Dev contributions
[Internals overview](./docs/project_overview.md)
