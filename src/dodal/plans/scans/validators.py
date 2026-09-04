from collections.abc import Callable
from typing import Any

from bluesky.protocols import HasName, Movable


def trajectory_validator(
    *,
    length: int,
    description: str,
    validate: Callable[[str, tuple[Any, ...], str], None] | None = None,
) -> Callable[[Any], Any]:
    def validator(value: Any) -> Any:
        if not isinstance(value, tuple):
            raise ValueError(f"Trajectory must be a tuple of {description}.")

        if not value:
            raise ValueError(f"Trajectory must contain {description}.")

        movable = value[0]

        if not isinstance(movable, Movable):
            raise ValueError(
                f"The first value in a trajectory must be Movable. Got {movable!r}."
            )
        movable_name = movable.name if isinstance(movable, HasName) else repr(movable)

        formatted_value = (movable_name, *value[1:])

        if len(value) != length:
            raise ValueError(
                f"Trajectory for {movable_name} must contain exactly "
                f"{length} values: {description}. "
                f"Got {len(value)} values: {formatted_value!r}"
            )
        if validate is not None:
            validate(movable_name, value, description)

        return value

    return validator


def validate_start_stop_step(
    movable_name: str,
    value: tuple[Any, ...],
    description: str,
) -> None:
    _, start, stop, step = value

    if step == 0:
        raise ValueError(
            f"Step size cannot be 0. "
            f"Received ({movable_name}, {start}, {stop}, {step}) for "
            f"{description}."
        )

    if start == stop:
        raise ValueError(
            f"Start and stop values cannot be the same. "
            f"Received ({movable_name}, {start}, {stop}, {step}) for {description}."
        )
