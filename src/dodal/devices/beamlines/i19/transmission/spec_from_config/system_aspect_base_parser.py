from abc import abstractmethod
from typing import Any, Generic, Self, TypeVar, cast

from pydantic import (
    RootModel,
    model_validator,
)

from dodal.devices.beamlines.i19.transmission.spec_from_config.system_configuration import (
    SystemConfiguration,
)

# 1. Define a local TypeVar for generic aspect specs
TxSubSpecT = TypeVar("TxSubSpecT")


class SystemAspectBaseParser(RootModel[dict[str, TxSubSpecT]], Generic[TxSubSpecT]):
    """Generic Base Model handling dict validation and extraction from the (JSON) configuration highest level dict."""

    @abstractmethod
    def validate_key_name(self, *, key_name: str) -> None: ...

    @model_validator(mode="after")
    def _ensure_all_keys_have_been_validly_named(self) -> Self:
        """Validates all names for keys_present.

        Raises:
            ValueError - if any aspect's sub-dict key names are not compliant.
        """
        for key in self.keys():
            self.validate_key_name(key_name=key)
        return self

    def keys(self):
        """Returns the configuration sub-dict internal keys."""
        return self.root.keys()

    @classmethod
    def name_all_specified(
        cls, *, system_configuration: SystemConfiguration
    ) -> list[str]:
        """Names all the aspect instances found in the validated config, in a neat list of names."""
        _aspect_instance = cls._extract_system_aspect(
            system_configuration=system_configuration
        )
        _all_specified_elements = _aspect_instance.keys()
        return list(_all_specified_elements)

    @classmethod
    def get_aspect_specifications(
        cls, *, system_configuration: SystemConfiguration
    ) -> dict[str, TxSubSpecT]:
        """Wraps all validated aspect instances, from config, in a dict against each instance's name.

        Args:
            system_configuration:
                The configuration JSON packaged with its structural template.

        Returns:
            A subclass-dependent dict[ str, < aspect > ] of - for example - all:
                - wedge driving motor specs against the name tag of each motor x,y etc.
                - absorber material absorption spectrum specifications against the name of each material.
        """
        _aspect_instance = cls._extract_system_aspect(
            system_configuration=system_configuration
        )
        return _aspect_instance.root

    @classmethod
    def _extract_raw_sub_dict(
        cls, *, system_configuration: SystemConfiguration
    ) -> dict[str, Any]:
        _aspect_key: str = system_configuration.get_sub_dict_key(target_type=cls)
        return system_configuration.hardware_parameters[_aspect_key]

    @classmethod
    def _extract_system_aspect(
        cls,
        *,
        system_configuration: SystemConfiguration,
    ) -> Self:
        """Extracts specification and validates configuration for one aspect of the transmission system."""
        _sub_dict = cls._extract_raw_sub_dict(system_configuration=system_configuration)
        _raw = cls.model_validate(_sub_dict)
        return cast(Self, _raw)
