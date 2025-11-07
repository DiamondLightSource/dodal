(using-pytest)=

# Running tests

Tests can be ran locally via command line or VSCode IDE.

## With VSCode

When using the VSCode IDE, it should automatically detect all of your tests and display one of the following icons next to each of them:
- Grey circle (not run yet)
- Green circle with a tick (test passed)
- Red circle with a cross (test failed)

You can also check code coverage by right-clicking on the test icon and selecting `Run with coverage`. This will re-run the test and highlight line numbers in your file:
- Green = covered by tests
- Red = not covered (and ideally should be tested)

To view all tests inside dodal, use the `Test Explorer` panel (flask icon) in VSCode. It displays all of your tests in a hierarchy, which you can run individually or in groups. It also shows the pass/fail icons mentioned above. Clicking on an item will run all tests beneath it in the hierarchy.

If you find that your tests are being skipped or not recognised by `pytest`, check for any syntax errors as this will block the tests being found. You can also check to see if there is an error output at the very bottom of the `Test Explorer` panel. This is usually caused by invalid syntax in your test file, or by circular dependencies in the code you are testing.

## Command line

### Unit tests

`pytest` will find functions in the project that [look like tests][look like tests], and run them to check for errors. 

When you have some fully working tests then you can run it with coverage:

```
$ tox -e tests
```

It will also report coverage to the command line and to `cov.xml`.

[look like tests]: https://docs.pytest.org/explanation/goodpractices.html#test-discovery
[pytest]: https://pytest.org/

### System tests locally

The system tests require the ``example-services`` project:

```commandline
git clone git@github.com:epics-containers/example-services.git
```

Then you need to launch some of the example ioc containers. Please note, this requires docker-compose not 
podman-compose:

```commandline
module load docker-compose
cd example-services
. ./environment.sh
podman compose up -d bl01t-di-cam-01 bl01t-mo-sim-01 ca-gateway
```

Once this is done, then the system tests can be run:

```commandline
tox -e system-report
```
