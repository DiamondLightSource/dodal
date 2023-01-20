=======
python-dodal
===========================

|code_ci| |docs_ci| |coverage| |pypi_version| |license|


Ophyd devices and other utils that could be used across DLS beamlines

============== ==============================================================
PyPI           ``pip install python-dodal``
Source code    https://github.com/DiamondLightSource/python-dodal
Documentation  https://DiamondLightSource.github.io/python-dodal
Releases       https://github.com/DiamondLightSource/python-dodal/releases
============== ==============================================================


.. |code_ci| image:: https://github.com/DiamondLightSource/python-dodal/actions/workflows/code.yml/badge.svg?branch=main
    :target: https://github.com/DiamondLightSource/python-dodal/actions/workflows/code.yml
    :alt: Code CI

.. |docs_ci| image:: https://github.com/DiamondLightSource/python-dodal/actions/workflows/docs.yml/badge.svg?branch=main
    :target: https://github.com/DiamondLightSource/python-dodal/actions/workflows/docs.yml
    :alt: Docs CI

.. |coverage| image:: https://codecov.io/gh/DiamondLightSource/python-dodal/branch/main/graph/badge.svg
    :target: https://codecov.io/gh/DiamondLightSource/python-dodal
    :alt: Test Coverage

.. |pypi_version| image:: https://img.shields.io/pypi/v/python-dodal.svg
    :target: https://pypi.org/project/python-dodal
    :alt: Latest PyPI version

.. |license| image:: https://img.shields.io/badge/License-Apache%202.0-blue.svg
    :target: https://opensource.org/licenses/Apache-2.0
    :alt: Apache License

..
    Anything below this line is used when viewing README.rst and will be replaced
    when included in index.rst

See https://DiamondLightSource.github.io/python-dodal for more detailed documentation.


Moving code from another repo
=============================

In the process of writing code in other DLS repos you may come to realise that it makes more sense to be in ``dodal``. It is a good idea to keep the history for this code, you can do this by doing the following (we will be using moving devices from https://github.com/DiamondLightSource/python-artemis as an example):

#. Clone the codebase you are copying from::

    git clone git@github.com:DiamondLightSource/python-artemis.git clone_for_history
    cd clone_for_history/

#. Remove the remote to avoid any mistaken pushes::

    git remote rm origin

#. Filter out only the directory/file you want to move::

    pip install git-filter-repo
    git-filter-repo --path file/to/move --path /other/file/to/move -f

#. Clean everything up::

    git reset --hard
    git gc --aggressive
    git prune
    git clean -fd

#. Add a note to every commit message to mention it's been moved::

    git filter-branch --msg-filter 'sed "$ a \
    NOTE: Commit originally came from https://github.com/DiamondLightSource/python-artemis"' -f -- --all

#. If you have been using Github `issue references`_ in the old repository modify these to point to be more explicit (Note that this assumes the old repo uses ``#123`` notation and only ever references issues from it's own repo)::

    git filter-branch -f --msg-filter 'sed "s|#[0-9]\+|DiamondLightSource/python-artemis&|g"' -- --all

#. Prepare the code to be in the correct structure for dodal::

    mkdir -p src/dodal/devices
    mv path/to/device src/dodal/devices/

#. At this point it's a good idea to check the log ``git log`` and the general directory structure to ensure it looks mostly correct

#. Add and commit this (locally)::

    git add .
    git commit -m "Prepare for import into dodal"

#. In a different folder clone ``dodal``, remove the origin (for now) to be safe and create a branch::

    git clone git@github.com:DiamondLightSource/python-dodal.git
    cd dodal
    git remote rm origin
    git checkout -b add_code_from_artemis

#. Add the source repo as a remote for ``dodal``::

    git remote add source /path/to/source/old_repo/.git

#. Pull from the source repo::

    git pull --no-rebase source main --allow-unrelated-histories

#. This is another point where it's a good idea to check the log ``git log`` and the general directory structure to ensure it looks mostly correct

#. Remove the source remote and re-add origin::

    git remote rm source
    git remote add origin git@github.com:DiamondLightSource/python-dodal.git

#. Tidy up the code so that it fits into the ``dodal`` repo e.g. in the Artemis case we had to change the tests to import from ``artemis`` to import from ``dodal`` and add some more dependencies.

.. _issue references: https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/autolinked-references-and-urls#issues-and-pull-requests
