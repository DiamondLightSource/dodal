from collections.abc import Callable
from typing import Any

from bluesky.protocols import Movable
from pydantic import TypeAdapter, ValidationError

from dodal.plans.scans.utils import get_bluesky_obj_name


def trajectory_validator(
    length: int,
    template: str,
    expected_type: Any,
) -> Callable[[Any], Any]:
    def validator(value: Any) -> Any:
        if not isinstance(value, tuple):
            raise ValueError(f"Trajectory must be a tuple of {template}.")

        if not value:
            raise ValueError(f"Trajectory must contain {template}.")

        movable = value[0]

        if not isinstance(movable, Movable):
            raise ValueError(
                f"The first value in a trajectory must be Movable. Got {get_bluesky_obj_name(movable)!r}."
            )
        formatted_values = (get_bluesky_obj_name(movable), *value[1:])

        if len(value) != length:
            raise ValueError(
                f"Trajectory must contain exactly {length} values. "
                f"Expected {template}. Got {len(value)} values: {formatted_values!r}"
            )
        try:
            TypeAdapter(
                expected_type, config={"arbitrary_types_allowed": True}
            ).validate_python(value, strict=False)
        except ValidationError as exc:
            raise ValueError(
                f"Trajectory  has invalid types. Expected {template}. "
                f"Received {formatted_values!r}."
            ) from exc

        return value

    return validator
