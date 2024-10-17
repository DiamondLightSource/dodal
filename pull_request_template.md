Fixes #ISSUE

### Instructions to reviewer on how to test:
1. Do thing x
2. Confirm thing y happens

### Checks for reviewer
- [ ] Would the PR title make sense to a scientist on a set of release notes
- [ ] If a new device has been added does it follow the [standards](https://diamondlightsource.github.io/dodal/main/reference/device-standards.html)
- [ ] If changing the API for a pre-existing device, ensure that any beamlines using this device have updated their Bluesky plans accordingly
- [ ] Have the connection tests for the relevant beamline(s) been run via `dodal connect ${BEAMLINE}`
