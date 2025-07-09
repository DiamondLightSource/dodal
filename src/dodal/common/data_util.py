import os
from typing import Any, TypeVar

from pydantic import BaseModel, TypeAdapter

TBaseModel = TypeVar("TBaseModel", bound=BaseModel)


def load_json_file_to_class(
    t: Any,
    file: str,
) -> Any:
    if not os.path.isfile(file):
        raise FileNotFoundError(f"Cannot find file {file}")

    with open(file) as f:
        json_obj = f.read()
    adapter = TypeAdapter(t)
    result = adapter.validate_json(json_obj)

    # Safely cast result back to the expected generic type
    return result  # type: ignore[return-value]


def save_class_to_json_file(model: BaseModel, file: str) -> None:
    with open(file, "w") as f:
        f.write(model.model_dump_json())
