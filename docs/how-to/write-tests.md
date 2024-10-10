# Writing Tests in This Python Project

Testing is essential to maintain the integrity and reliability of the codebase. Follow the guidelines below to write tests for this project effectively.

## Test Organization

- **Unit Tests**: Place unit tests for individual components in the `tests` directory, but take care to mirror the file structure of the `src` folder with the corresponding code files. Use the `test_*.py` naming convention for test files.
- **System Tests**: Tests that interact with DLS infrastructure, network, and filesystem should be placed in the top-level `systems_test` folder. This separation ensures that these tests are easily identifiable and can be run independently from unit tests.
