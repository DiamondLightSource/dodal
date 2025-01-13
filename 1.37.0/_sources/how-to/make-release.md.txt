# Make a release

Releases are created through the Github release interface.

To make a new release, please follow this checklist:

- Ensure that you have previously followed [](./pypi)
- Choose a new PEP440 compliant release number (see <https://peps.python.org/pep-0440/>) (The release version should 
  look like `{major}.{minor}.{patch}`). See [Deciding release numbers](#Deciding release numbers) if you're unsure on 
  what the release version should be.
- Go to the GitHub [release] page
- Choose `Draft New Release`
- Click `Choose Tag` and supply the new tag you chose (click create new tag)
- Click `Generate release notes`, review and edit these notes. Confirm they do not omit anything important and make sense (to a user, not just a developer).
- Choose a title and click `Publish Release`. This will create a release on `pypi` automatically and post to the 
  `bluesky` slack channel.
- Manually confirm that the `pypi` version has been updated (after all tests have run) and that slack is notified.

Note that tagging and pushing to the main branch has the same effect except that
you will not get the option to edit the release notes.

A new release will be made and the wheel and sdist uploaded to PyPI.

[release]: https://github.com/DiamondLightSource/python-copier-template/releases

## Deciding release numbers

Releases should obviously be versioned higher than the previous latest release. Otherwise you should follow this guide:

* **Major** - Changes that have the potential to break plans
* **Minor** - New features
* **Patch** - Bug fixes
