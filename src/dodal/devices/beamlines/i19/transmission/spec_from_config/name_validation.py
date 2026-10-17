import re
from functools import cached_property
from re import Pattern
from typing import Final


class NameValidator:
    def __init__(
        self, *, regexp_pattern: str, thing_being_named: str, error_message: str
    ) -> None:
        self.regexp_pattern = regexp_pattern
        self.thing_being_named = thing_being_named
        self.error_message = error_message

    @cached_property
    def lazy_matcher(self) -> Pattern[str]:
        return re.compile(self.regexp_pattern)

    def validate_name(self, *, name_to_check: str) -> None:
        if self.lazy_matcher.match(name_to_check) is None:
            formatted_message = self.error_message.format(
                **{self.thing_being_named: name_to_check}
            )
            raise ValueError(formatted_message)


class AxisNameValidation:
    """Lateral wedge motor axis naming validation regular expression.

    Either permits (at start of name):
    - leading underscore followed immediately by a letter,
    or,
    - leading letter,
    then up to eight more optional alphanumeric characters.
    """

    _VALIDATOR: Final = NameValidator(
        regexp_pattern=r"^(_[A-Za-z][A-Za-z0-9]{0,7}|[A-Za-z][A-Za-z0-9]{0,8})$",
        thing_being_named="axis",
        error_message="Axis name '{axis}' must start with a letter, or an underscore followed by a letter, later characters must alphanumeric: Max. length 9 characters.",
    )

    @classmethod
    def validate_axis_name(cls, *, axis_name: str) -> None:
        """Ensures motor axis names follow axis naming rules.

        Note:
            The axis name must start either with a letter, or an underscore followed by a letter,
            and subsequently optional characters can only be numbers or letters:  Total length up to nine characters.
        """
        cls._VALIDATOR.validate_name(name_to_check=axis_name)


class MaterialNameValidation:
    """Absorber materials naming validation regular expression.

    Either permits (at start of name):
    - leading underscore followed immediately by a letter,
    or,
    - leading letter,
    then any number of alphanumerics or underscores or hyphens.
    """

    _VALIDATOR: Final = NameValidator(
        regexp_pattern=r"^([A-Za-z]|_[A-Za-z])[A-Za-z0-9_-]*$",
        thing_being_named="material",
        error_message=(
            "Material name '{material}' must start with a letter, or an underscore followed by any number of alphanumerics or underscores or hyphens."
        ),
    )

    @classmethod
    def validate_material_name(cls, *, material_name: str) -> None:
        """Ensures material names follow the rules.

        Note:
            The material name must start either with a letter, or an underscore followed by a letter,
            and subsequent characters can only be alphanumerics, underscores or hyphens.
        """
        cls._VALIDATOR.validate_name(name_to_check=material_name)


class WheelNameValidation:
    """Wheel naming validation regular expression.

    Either permits (at start of name):
    - leading underscore followed immediately by a letter,
    or,
    - leading letter,
    then up to eleven more optional alphanumeric characters.
    """

    _VALIDATOR: Final = NameValidator(
        regexp_pattern=r"^(_[A-Za-z][A-Za-z0-9]{0,10}|[A-Za-z][A-Za-z0-9]{0,11})$",
        thing_being_named="wheel",
        error_message=(
            "Wheel name '{wheel}' must start with a letter, or an underscore followed by a letter, later optional characters must alphanumeric: Max. length 12 characters."
        ),
    )

    @classmethod
    def validate_wheel_name(cls, *, wheel_name: str) -> None:
        """Ensures wheel names follow naming rules.

        Note:
            The wheel name must start either with a letter, or an underscore followed by a letter,
            and subsequently characters can only be numbers or letters:  Total length up to 12 characters.
        """
        cls._VALIDATOR.validate_name(name_to_check=wheel_name)
