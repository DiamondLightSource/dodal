from abc import ABC, abstractmethod
from collections.abc import Generator
from typing import Any

from bluesky import Msg
from pydantic import BaseModel


class AbstractExperimentParameterBase(BaseModel, ABC):
    def validate_against_hardware(self, composite) -> Generator[Msg, Any, Any]:
        """
        Return a bluesky plan stub that can be called to validate the parameters against
        beamline hardware (e.g. against motor limits).
        Subclasses should override this if they need to perform such parameter validation.
        In the event of the parameters being invalid, the plan should raise a ValueError

        Args:
            composite: A composite supplying devices required for validation.

        Returns:
            The plan stub generator
        """
        yield from iter([])


class AbstractExperimentWithBeamParams(AbstractExperimentParameterBase):
    transmission_fraction: float

    @abstractmethod
    def get_num_images(self) -> int:
        pass
