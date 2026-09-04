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
    """Create a validator for a scan trajectory.

    The returned validator checks that the trajectory is a tuple with the
    expected number of values, that its first value is a ``Movable``, and
    that the complete tuple matches the supplied Pydantic type.

    Pydantic validation is performed with arbitrary types allowed so that
    ``Movable`` protocol types can be validated as part of the trajectory.
    Type validation is performed after the structural checks so that malformed
    trajectories produce more useful error messages.

    Args:
        length: Expected number of values in the trajectory tuple.
        template: Human-readable description of the expected trajectory
            structure, for example ``"(movable, start, stop, step)"``.
        expected_type: Pydantic-compatible type describing the expected
            trajectory, used to validate the types of the tuple elements.

    Returns:
        A Pydantic-compatible validator function that validates a trajectory.

    Raises:
        ValueError: If the value is not a tuple, is empty, contains an invalid
            movable, has the wrong number of values, or contains values of
            invalid types.
    """

    def validator(value: Any) -> Any:
        """Validate a single trajectory value."""
        if not isinstance(value, tuple):
            raise ValueError(f"Trajectory must be a tuple of {template}.")

        if not value:
            raise ValueError(f"Trajectory must contain {template}.")

        movable = value[0]

        if not isinstance(movable, Movable):
            raise ValueError(
                "The first value in a trajectory must be Movable. "
                f"Received {get_bluesky_obj_name(movable)!r}."
            )
        formatted_values = (get_bluesky_obj_name(movable), *value[1:])

        if len(value) != length:
            raise ValueError(
                f"Trajectory must contain exactly {length} values. "
                f"Expected {template}. Received {len(value)} values: {formatted_values!r}"
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
