# Style Guide

This project is based on the [python-copier-template](https://diamondlightsource.github.io/python-copier-template/main/index.html), which integrates a number of tools which assist in usability and enforce style decisions. It is recommended that developers use a [vscode devcontainer](https://code.visualstudio.com/docs/devcontainers/containers) to easily take advantage of the tools available to them. You will need follow a short set of [instructions](https://diamondlightsource.github.io/python-copier-template/main/how-to/dev-install.html#install-dependencies) to enable use of vscode devcontainers. 

For this project, we follow [the Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) with a notable set of exceptions.

## dodal Specific Guidance

Specific guidelines for use within this project which are not outlined in [the Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) or [PEP 8](https://peps.python.org/pep-0008/). 

1. Prefer the use of `params` over `args` when a group of parameters is used (i.e. in [GDABeamlineParameters](https://github.com/DiamondLightSource/dodal/blob/e23e028ff46e0e75aad0248d0ba06fa5382eff1e/src/dodal/common/beamlines/beamline_parameters.py#L15) or [EigerDetector](https://github.com/DiamondLightSource/dodal/blob/e23e028ff46e0e75aad0248d0ba06fa5382eff1e/src/dodal/devices/eiger.py#L91)).

2. Handle shared devices as outlined in [handle devices shared between multiple endstations](../explanations/decisions/0006-devices-shared-between-endstations.md)

## Guidance Against [the Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)

Specific guidelines for use within this project which directly oppose decisions in [the Google Python Style Guide](https://google.github.io/styleguide/pyguide.html). 

1. [PEP 8](https://peps.python.org/pep-0008/) should take precedence over [the google style guide](https://google.github.io/styleguide/pyguide.html#316-naming) on any naming disputes to ensure continuity throughout the project.

2. If a ruff rule enforced by the [python-copier-template](https://diamondlightsource.github.io/python-copier-template/main/index.html) contradicts the Google Python Style Guide, the ruff rule takes precedence. If you disagree with the applied ruff rule, please open an issue on the [python-copier-template](https://diamondlightsource.github.io/python-copier-template/main/index.html).

3. Use absolute import statements for types, classes, or functions, rather than for packages and modules only. We should follow the [PEP 8](https://peps.python.org/pep-0008/#imports) guideline here rather than the decision in [the google style guide](https://google.github.io/styleguide/pyguide.html#224-decision), as 'absolute imports are recommended, as they are usually more readable and tend to be better behaved'.

4. Prefer making github issues over [TODO comments](https://google.github.io/styleguide/pyguide.html#312-todo-comments) for code that is temporary, a short-term solution, or good-enough but not perfect. An issue allows for context and follow-up comments. 

5. Prefer using explicit true/false evaluation over [implicit false evaluations](https://google.github.io/styleguide/pyguide.html#214-truefalse-evaluations). Explicit false evaluation is more predictable when handling different data types (i.e. integers), as `0` is falsy.

## Guidance Which Agrees with [the Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)

Specific guidelines for use within this project which agree with decisions in [the Google Python Style Guide](https://google.github.io/styleguide/pyguide.html), but may be uncommon practice for those unfamiliar with Python. These tend to be guidelines which cannot be enforced by enabling a ruff rule.

1. [Use decorators judiciously](https://google.github.io/styleguide/pyguide.html#2174-decision) when there is a clear advantage. Avoid `staticmethod` and limit use of `classmethod`.

2. [Use of properties](https://google.github.io/styleguide/pyguide.html#213-properties) over [getters and setters](https://google.github.io/styleguide/pyguide.html#315-getters-and-setters) is encouraged, unless getting or setting the variable is complex or the cost is significant, either currently or in a reasonable future.

3. [Avoid global mutable state](https://google.github.io/styleguide/pyguide.html#25-mutable-global-state) where possible. 
