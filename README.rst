Moving code from another repo
=============================

In the process of writing code in other DLS repos you may come to realise that it makes more sense to be in ``dodal``. It is a good idea to keep the history for this code, you can do this by doing the following (we will be using moving devices from https://github.com/DiamondLightSource/python-artemis as an example):

1. Clone the codebase you are copying from::

    git clone git@github.com:DiamondLightSource/python-artemis.git clone_for_history
    cd clone_for_history/

1. Remove the remote to avoid any mistaken pushes::

    git remote rm origin

1. Filter out only the directory you want to move::

    git filter-branch --subdirectory-filter src/artemis/devices/ -- --all

1. Clean everything up::

    git reset --hard
    git gc --aggressive
    git prune
    git clean -fd

1. Add a note to every commit message to mention it's been moved::

    git filter-branch --msg-filter -f 'sed "$ a\
    NOTE: Commit originally came from https://github.com/DiamondLightSource/python-artemis"' -- --all

1. If you have been using Github `issue references`_ in the old repository modify these to point to be more explicit (Note that this assumes the old repo uses ``#123`` notation and only ever references issues from it's own repo)::

    git filter-branch -f --msg-filter 'sed "s|#[0-9]\+|DiamondLightSource/python-artemis&|g"' -- --all

1. Prepare the code to be in the correct structure for dodal

    mkdir -p src/dodal/devices
    mv * src/dodal/devices/

1. At this point it's a good idea to check the log ``git log`` and the general directory structure to ensure it looks mostly correct

1. Add and commit this (locally)::

    git add .
    git commit -m "Prepare for import into dodal"

1. In a different folder clone ``dodal``, remove the origin (for now) to be safe and create a branch::

    git clone git@github.com:DiamondLightSource/python-dodal.git
    cd dodal
    git remote rm origin
    git checkout -b add_code_from_artemis

1. Add the source repo as a remote for ``dodal``

    git remote add source /path/to/source/folder

1. Pull from the source repo

    git pull --rebase source main --allow-unrelated-histories

1. This is another point where it's a good idea to check the log ``git log`` and the general directory structure to ensure it looks mostly correct

1. Remove the source remote and re-add origin::

    git remote rm source
    git remote add origin https://github.com/DiamondLightSource/python-dodal

1. Tidy up the code so that it fits into the ``dodal`` repo e.g. in the Artemis case we had to change the tests to import from ``artemis`` to import from ``dodal`` and add some more dependencies.

.. _issue references: https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/autolinked-references-and-urls#issues-and-pull-requests
