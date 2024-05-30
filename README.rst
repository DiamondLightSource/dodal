dodal
============

|code_ci| |docs_ci| |coverage| |pypi_version| |license|


Ophyd devices and other utils that could be used across DLS beamlines

============== ==============================================================
PyPI           ``pip install dls-dodal``
Source code    https://github.com/DiamondLightSource/dodal
Documentation  https://DiamondLightSource.github.io/dodal
Releases       https://github.com/DiamondLightSource/dodal/releases
============== ==============================================================

Testing Connectivity
--------------------

You can test your connection to a beamline if it's PVs are visible to your machine with:

.. code:: shell

    # On any workstation:
    dodal connect <BEAMLINE>

    # On a beamline workstation, this should suffice:
    dodal connect ${BEAMLINE}


For more options, including a list of valid beamlines, type

.. code:: shell

    dodal connect --help


.. |code_ci| image:: https://github.com/DiamondLightSource/dodal/actions/workflows/code.yml/badge.svg?branch=main
    :target: https://github.com/DiamondLightSource/dodal/actions/workflows/code.yml
    :alt: Code CI

.. |docs_ci| image:: https://github.com/DiamondLightSource/dodal/actions/workflows/docs.yml/badge.svg?branch=main
    :target: https://github.com/DiamondLightSource/dodal/actions/workflows/docs.yml
    :alt: Docs CI

.. |coverage| image:: https://codecov.io/gh/DiamondLightSource/dodal/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/DiamondLightSource/dodal
    :alt: Test Coverage

.. |pypi_version| image:: https://img.shields.io/pypi/v/dls-dodal.svg
    :target: https://pypi.org/project/dls-dodal
    :alt: Latest PyPI version

.. |license| image:: https://img.shields.io/badge/License-Apache%202.0-blue.svg
    :target: https://opensource.org/licenses/Apache-2.0
    :alt: Apache License

..
    Anything below this line is used when viewing README.rst and will be replaced
    when included in index.rst

See https://DiamondLightSource.github.io/dodal for more detailed documentation.
