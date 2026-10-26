from functools import cached_property
from typing import Any

from pydantic import BaseModel, ConfigDict


class SystemConfiguration(BaseModel):
    """Combination of configuration blob (typically JSON dict) and templating dict model for anticipated system config structure.

    Attributes:
        structural_template: A specification class extending pydantic BaseModel (or RootModel) which has fields that map to dict elements.
        hardware_parameters: A top level dict, typically extracted from JSON, which specifies the system hardware set up.
    """

    structural_template: type[BaseModel]
    hardware_parameters: dict[str, dict[str, Any]]

    @cached_property
    def field_mapping(self) -> dict[Any, str]:
        """Maps transmission system highest level configuration annotations (types) to their corresponding names."""
        return {
            info.annotation: field_name
            for field_name, info in self.structural_template.model_fields.items()
        }

    # Base Model internal setting to make this class immutable
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
        frozen=True,
    )

    def get_sub_dict_key(self, *, target_type: type) -> str:
        return self.field_mapping[target_type]
