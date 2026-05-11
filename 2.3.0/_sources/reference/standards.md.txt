# Standards

This document defines the code and documentation standards used in this
repository.

## Code Standards

The code in this repository conforms to standards set by the following tools:

- [ruff](https://docs.astral.sh/ruff/) for code formatting
- [flake8](https://flake8.pycqa.org/en/latest/) for style checks
- [isort](https://pycqa.github.io/isort/) for import ordering
- [pyright](https://github.com/microsoft/pyright) for static type checking

:::{seealso}
How-to guides [how-to/lint](../how-to/lint) and [how-to/statis-analysis](../how-to/static-analysis)
:::

## Supported Python Versions

As a standard for the python versions to support, we should be matching the deprecation policy at
https://numpy.org/neps/nep-0029-deprecation_policy.html.

Currently supported versions are: 3.11, 3.12, 3.13. (As of the last edit of this document.)


## Documentation Standards

Docstrings are pre-processed using the Sphinx Napoleon extension. As such,
[google-style](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/index.html#google-vs-numpy) is considered as standard for this repository. Please use type
hints in the function signature for types. For example:

```python

    def func(arg1: str, arg2: int) -> bool:
        """Summary line.

        Extended description of function.

        Args:
            arg1: Description of arg1
            arg2: Description of arg2

        Returns:
            Description of return value
        """
        return True
```

Documentation is contained in the ``docs`` directory and extracted from
docstrings of the API.

Docs follow the underlining convention:

```
    Headling 1 (page title)
    =======================

    Heading 2
    ---------

    Heading 3
    ~~~~~~~~~
```

:::{seealso}
How-to guide [how-to/build-docs](../how-to/build-docs)
:::
