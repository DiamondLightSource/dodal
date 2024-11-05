[![CI](https://github.com/DiamondLightSource/dodal/actions/workflows/ci.yml/badge.svg)](https://github.com/DiamondLightSource/dodal/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/DiamondLightSource/dodal/branch/main/graph/badge.svg)](https://codecov.io/gh/DiamondLightSource/dodal)
[![PyPI](https://img.shields.io/pypi/v/dls-dodal.svg)](https://pypi.org/project/dls-dodal)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)

# dodal

Ophyd devices and other utils that could be used across DLS beamlines

Source          | <https://github.com/DiamondLightSource/dodal>
:---:           | :---:
PyPI            | `pip install dls-dodal`
Documentation   | <https://diamondlightsource.github.io/dodal>
Releases        | <https://github.com/DiamondLightSource/dodal/releases>

Testing Connectivity
--------------------

You can test your connection to a beamline if it's PVs are visible to your machine with:


```
    # On any workstation:
    dodal connect <BEAMLINE>

    # On a beamline workstation, this should suffice:
    dodal connect ${BEAMLINE}
```



For more options, including a list of valid beamlines, type

```
    dodal connect --help
```

<!-- README only content. Anything below this line won't be included in index.md -->

See https://diamondlightsource.github.io/dodal for more detailed documentation.
