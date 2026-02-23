from os.path import isfile
from typing import Generic, TypeVar

from pydantic import BaseModel

TBaseModel = TypeVar("TBaseModel", bound=BaseModel)


def load_json_file_to_class(t: type[TBaseModel], file: str) -> TBaseModel:
    """Load json file into a pydantic model class.

    Args:
        t (type[TBaseModel]): type of model to load a file into to.
        file (str): The file to read.

    Returns:
        An instance of type t.
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


class JsonModelLoader(Generic[TBaseModel]):
    """Load a json file into a pre configured pydantic model."""

    def __init__(self, base_model: type[TBaseModel], default_file: str | None = None):
        """Initialise configuration.

        Args:
            base_model (type[TBaseModel]): The configured model type to load json files into.
            default_file (str, optional): Default file to use to load data into base_model.
        """
        self._base_model = base_model
        self.default_file = default_file

    def __repr__(self) -> str:
        """Return a human-readable representation of the JsonModelLoader.

        Returns:
            str: A string describing the configured model type and default file.
        """
        model_name = self._base_model.__name__
        return (
            f"{self.__class__.__name__}("
            f"base_model={model_name}, "
            f"default_file={self.default_file!r})"
        )

    def __call__(self, file: str | None = None) -> TBaseModel:
        """Load a json file and return it is as the configured pydantic model.

        Args:
            file (str, optional): The file to load into a pydantic class. If None
            provided, use the configured default_file.
        """
        if file is None and self.default_file is not None:
            return load_json_file_to_class(self._base_model, self.default_file)
        elif file is not None:
            return load_json_file_to_class(self._base_model, file)
        raise RuntimeError(
            f"{self} has no default file configured and no file was provided when "
            "trying to load in a model. "
        )
