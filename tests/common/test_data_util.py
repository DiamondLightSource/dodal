from os.path import split

import pytest
from pydantic import BaseModel

from dodal.common.data_util import (
    JsonLoaderConfig,
    JsonModelLoader,
    json_model_loader,
    save_class_to_json_file,
)


class MyModel(BaseModel):
    value: str
    number: float


def assert_model(result: MyModel, expected: MyModel) -> None:
    assert result.value == expected.value
    assert result.number == expected.number


@pytest.fixture
def default_model() -> MyModel:
    return MyModel(value="test1", number=0)


@pytest.fixture
def other_model() -> MyModel:
    return MyModel(value="test2", number=3)


@pytest.fixture
def default_tmp_file(tmp_path, default_model: MyModel) -> str:
    path = tmp_path / "json_loader_default_file.json"
    # Setup tmp file for this test by saving the data.
    save_class_to_json_file(default_model, path)
    return str(path)


@pytest.fixture
def tmp_file(tmp_path, other_model: MyModel) -> str:
    path = tmp_path / "json_loader_file.json"
    # Setup tmp file for this test by saving the data.
    save_class_to_json_file(other_model, path)
    return str(path)


@pytest.fixture
def load_json_model_with_default_file_only(
    default_tmp_file: str,
) -> JsonModelLoader[MyModel]:
    return json_model_loader(
        MyModel, JsonLoaderConfig.from_default_file(default_tmp_file)
    )


def test_json_model_loader_with_configured_default_file_only(
    load_json_model_with_default_file_only: JsonModelLoader[MyModel],
    tmp_file: str,
    other_model: MyModel,
    default_model: MyModel,
) -> None:
    model_result = load_json_model_with_default_file_only()
    assert_model(model_result, default_model)

    # Test we can use relative file path
    path, file = split(tmp_file)
    model_result = load_json_model_with_default_file_only(file)
    assert_model(model_result, other_model)

    # Test we can override with absolute path.
    model_result = load_json_model_with_default_file_only(tmp_file)
    assert_model(model_result, other_model)


@pytest.fixture
def load_json_model_with_default_path_only(
    default_tmp_file: str,
) -> JsonModelLoader[MyModel]:
    path, file = split(default_tmp_file)
    return json_model_loader(MyModel, JsonLoaderConfig.from_default_path(path))


def test_load_json_model_with_configued_path_only(
    load_json_model_with_default_path_only: JsonModelLoader[MyModel],
    tmp_file: str,
    other_model: MyModel,
) -> None:
    # Test we can use relative file path
    path, file = split(tmp_file)
    model_result = load_json_model_with_default_path_only(file)
    assert_model(model_result, other_model)

    # Test we can still use absolute file path
    model_result = load_json_model_with_default_path_only(tmp_file)
    assert_model(model_result, other_model)

    with pytest.raises(
        RuntimeError,
        match="MyModel loader has no default file configured and no file was provided.",
    ):
        load_json_model_with_default_path_only()


@pytest.fixture
def load_json_model_with_default_path_and_file(
    default_tmp_file: str,
) -> JsonModelLoader[MyModel]:
    path, file = split(default_tmp_file)
    return json_model_loader(
        MyModel, JsonLoaderConfig(default_path=path, default_file=file)
    )


def test_load_json_model_with_configued_path_and_file(
    load_json_model_with_default_path_and_file: JsonModelLoader[MyModel],
    tmp_file: str,
    other_model: MyModel,
    default_model: MyModel,
) -> None:
    # Test uses default file
    model_result = load_json_model_with_default_path_and_file()
    assert_model(model_result, default_model)

    # Test we can use relative file path
    path, file = split(tmp_file)
    model_result = load_json_model_with_default_path_and_file(file)
    assert_model(model_result, other_model)

    # Test we can still use absolute file path
    model_result = load_json_model_with_default_path_and_file(tmp_file)
    assert_model(model_result, other_model)


@pytest.fixture
def load_json_model_no_config() -> JsonModelLoader[MyModel]:
    return json_model_loader(MyModel)


def test_json_model_loader_with_no_config(
    load_json_model_no_config: JsonModelLoader[MyModel],
    tmp_file: str,
    other_model: MyModel,
) -> None:
    with pytest.raises(
        RuntimeError,
        match="MyModel loader has no default file configured and no file was provided.",
    ):
        load_json_model_no_config()

    with pytest.raises(FileNotFoundError):
        # Test using a relative path fails
        path, file = split(tmp_file)
        load_json_model_no_config(file)

    # Test we can still use absolute file path
    model_result = load_json_model_no_config(tmp_file)
    assert_model(model_result, other_model)


def test_updating_config_updates_factory_function(
    default_tmp_file: str, tmp_file: str, default_model: MyModel, other_model: MyModel
) -> None:
    config = JsonLoaderConfig.from_default_file(default_tmp_file)
    model_loader = json_model_loader(MyModel, config)

    # Test uses default file
    model_result = model_loader()
    assert_model(model_result, default_model)

    # Test uses new default file
    config.update_config_from_file(tmp_file)
    model_result = model_loader()
    assert_model(model_result, other_model)


@pytest.fixture
def all_json_model_loaders(
    load_json_model_with_default_file_only: JsonModelLoader[MyModel],
    load_json_model_with_default_path_only: JsonModelLoader[MyModel],
    load_json_model_with_default_path_and_file: JsonModelLoader[MyModel],
    load_json_model_no_config: JsonModelLoader[MyModel],
) -> list[JsonModelLoader[MyModel]]:
    return [
        load_json_model_with_default_file_only,
        load_json_model_with_default_path_only,
        load_json_model_with_default_path_and_file,
        load_json_model_no_config,
    ]


@pytest.mark.parametrize("loader_position", range(4))
def test_all_json_model_loader_raise_error_if_invalid_file(
    all_json_model_loaders: list[JsonModelLoader[MyModel]],
    loader_position: int,
) -> None:
    json_loader = all_json_model_loaders[loader_position]
    with pytest.raises(FileNotFoundError):
        json_loader("sdkgsk")
