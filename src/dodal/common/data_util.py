from os.path import isfile
from typing import Protocol, TypeVar

from pydantic import BaseModel

TBaseModel = TypeVar("TBaseModel", bound=BaseModel, covariant=True)


def load_json_file_to_class(t: type[TBaseModel], file: str) -> TBaseModel:
    """Load json file into a pydantic model class.

    Args:
        t (type[TBaseModel]): type of model to load a file into to.
        file (str): The file to read.

    Returns:
        An instance of pydantic BaseModel.
    """
    if not isfile(file):
        raise FileNotFoundError(f"Cannot find file {file}")

    with open(file) as f:
        json_obj = f.read()
    cls = t.model_validate_json(json_obj)
    return cls


def save_class_to_json_file(model: BaseModel, file: str) -> None:
    """Save a pydantic model as a json file.

    Args:
        model (BaseModel): The pydantic model to save to json file.
        file (str): The file path to save the model to.
    """
    with open(file, "w") as f:
        f.write(model.model_dump_json())


class JsonModelLoader(Protocol[TBaseModel]):
    def __call__(self, file: str | None = None) -> TBaseModel: ...


def json_model_loader(
    model: type[TBaseModel], default_file: str | None = None
) -> JsonModelLoader[TBaseModel]:
    """Factory to create a function that loads a json file into a configured pydantic
    model and with an optional default file to use.
    """

    def load_json(file: str | None = default_file) -> TBaseModel:
        """Load a json file and return it is as the configured pydantic model.

        Args:
            file (str, optional): The file to load into a pydantic class. If None
            provided, use the configured default_file.

        Returns:
            An instance of the configurated pydantic base_model type.
        """
        if file is None:
            raise RuntimeError(
                f"{model.__name__} loader has no default file configured and no file was "
                "provided when trying to load in a model. "
            )
        return load_json_file_to_class(model, file)

    return load_json
