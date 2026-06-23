# Add run_engine and mock_config_client to be used in system tests
pytest_plugins = [
    "dodal.testing.fixtures.run_engine",
    "dodal.testing.fixtures.config_client",
]
