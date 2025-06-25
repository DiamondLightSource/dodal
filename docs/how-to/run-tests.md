(using-pytest)=

# Run the tests using pytest

Testing is done with [pytest]. It will find functions in the project that [look like tests][look like tests], and run them to check for errors. You can run it with:

```
$ pytest
```

When you have some fully working tests then you can run it with coverage:

```
$ tox -e tests
```

It will also report coverage to the commandline and to `cov.xml`.

[look like tests]: https://docs.pytest.org/explanation/goodpractices.html#test-discovery
[pytest]: https://pytest.org/

# Run the system tests locally

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
