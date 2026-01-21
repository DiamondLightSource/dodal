# Style Guide

This project is based on the [python-copier-template](https://diamondlightsource.github.io/python-copier-template/main/index.html), which integrates a number of tools which assist in usability and enforce style decisions. It is recommended that developers use a [vscode devcontainer](https://code.visualstudio.com/docs/devcontainers/containers) to easily take advantage of the tools available to them. You will need complete a short set of [instructions](https://diamondlightsource.github.io/python-copier-template/main/how-to/dev-install.html#install-dependencies) to enable use of vscode devcontainers. 

For this project, we follow the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) with a notable set of exceptions:

## 

1. [PEP 8](https://peps.python.org/pep-0008/) should take precedence over [the google style guide](https://google.github.io/styleguide/pyguide.html#316-naming) on any naming disputes to ensure continuity throughout the project.

2. If a ruff rule enforced by the [python-copier-template](https://diamondlightsource.github.io/python-copier-template/main/index.html) contradicts Google, the ruff rule takes precedence. If you disagree with the applied ruff rule, please open an issue on the [python-copier-template](https://diamondlightsource.github.io/python-copier-template/main/index.html).

3. Use absolute import statements for types, classes, or functions, rather than for packages and modules only. We should follow the [PEP 8](https://peps.python.org/pep-0008/#imports) guideline here rather than the decision in [the google style guide](https://google.github.io/styleguide/pyguide.html#224-decision), as 'absolute imports are recommended, as they are usually more readable and tend to be better behaved'.

4. Prefer making github issues over [TODO comments](https://google.github.io/styleguide/pyguide.html#312-todo-comments) for code that is temporary, a short-term solution, or good-enough but not perfect. An issue allows for context and follow-up comments. 

5. Prefer using explicit true/false evaluation over [implicit false evaluations](https://google.github.io/styleguide/pyguide.html#214-truefalse-evaluations). Explicit false evaluation is more predictable when handling different data types (i.e. integers), as `0` is falsy.

6. setters and getters

7. Prefer utility functions over staticmethod

8. Prefer `args` over `params`

9. Avoid global mutable state, as is the decision in [the google style guide](https://google.github.io/styleguide/pyguide.html#25-mutable-global-state). 
