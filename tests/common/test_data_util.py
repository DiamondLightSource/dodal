import pytest
from pydantic import BaseModel

from dodal.common.data_util import JsonModelLoader, save_class_to_json_file


class MyModel(BaseModel):
    value: str
    number: float


@pytest.fixture
def raw_data() -> dict:
    return {
        "value": "test",
        "number": 3,
    }


@pytest.fixture
def tmp_file(tmp_path, raw_data: dict) -> str:
    path = tmp_path / "json_loader_test.json"
    test_model = MyModel.model_validate(raw_data)
    save_class_to_json_file(test_model, path)
    return path


@pytest.fixture
def load_model(tmp_file: str) -> JsonModelLoader[MyModel]:
    return JsonModelLoader[MyModel](MyModel, default_file=tmp_file)


def test_json_loader_with_default_file(
    load_model: JsonModelLoader[MyModel],
) -> None:
    model = load_model()
    assert model.value == "test"
    assert model.number == 3


def test_json_loader_with_no_file(
    load_model: JsonModelLoader[MyModel], tmp_file: str
) -> None:
    load_model.default_file = None
    model = load_model(tmp_file)
    assert model.value == "test"
    assert model.number == 3


def test_json_loader_with_no_file_or_default_file(
    load_model: JsonModelLoader[MyModel],
) -> None:
    load_model.default_file = None
    with pytest.raises(TypeError):
        load_model()
