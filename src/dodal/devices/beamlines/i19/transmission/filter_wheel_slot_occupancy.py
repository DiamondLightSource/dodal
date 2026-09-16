
from typing import Annotated, final

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PositiveInt,
    PrivateAttr,
    StrictFloat,
    model_validator,
)

from dodal.common.general_maths.absorbers import FixedDepth
from dodal.common.general_maths.transmission_interconversion import (
    CANONICAL_NON_ABSORPTION,
)


@final
class _CanonicalEmptySlot(FixedDepth):
    """Canonical absorption calculator answering doamin logic questions on behalf of a reserved empty slot."""

    def is_eligible_for_energy(self, *, xray_energy_kev: float) -> bool:
        return True

    def calculate_absorption_bn(self, *, xray_energy_kev: StrictFloat) -> float:
        return CANONICAL_NON_ABSORPTION


class FilterWheelSlotOccupancy(BaseModel):
    """The reservation of an empty slot and occupation details of slots by absorbing filters.

    Attributes:
        wheel_name:
            An identifying string useful in logger messages and raised errors.
        wheel_capacity:
            The number of slots in the wheel - typically six on i19.
        reserved_slot:
            The reserved slot intentially left empty, ( counted as always permitted )
            for the retraction of absorbers in the "OUT" state.
        permitted_slots:
            A set of slot indices where filters are, that the system has permission to use.
        occupied_slots:
            The slot indices mapped against FixedDepth calculations for any mounted filters.

    Notes:
        1: There is no over-restriction that permitted slots lie within the wheel,
        this facilitates wheels being swapped without any need to edit permission settings.

        2: The filters should be listed in the occupied attribute,
        even if excluded from usage permissions,
        this allows permission changes to be a one-stop shop op.
    """
    wheel_name: str = Field(strict=True, min_length=1)

    wheel_capacity: int = Field(strict=True, gt=0)

    reserved_slot: int = Field(strict=True, gt=0)

    permitted_slots: frozenset[Annotated[int, Field(strict=True, gt=0)]] = Field(default_factory=frozenset)  # Permissions not restricted by wheel capacity

    occupied_slots: dict[Annotated[int, Field(strict=True, gt=0)], FixedDepth] = Field(default_factory=dict)

    _empty_slot: FixedDepth = PrivateAttr(default=_CanonicalEmptySlot())

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True,)


    @model_validator(mode='after')
    def _internal_consistency_check(self) -> "FilterWheelSlotOccupancy":
        """Model validity restrictions.

         - The wheel must have a name: A single letter will do.
         - The (empty) reserved slot must be specified within the wheel.
         - The reserved slot must not be mentioned in the occupied slots.
         - The number of occupied slots specified must be less than the wheel capacity.
         - Each occupied slot index must lie within the wheel.

        ( See also attribute notes - especially with respect to looser restrictions on permissions. )
        """
        if not self.wheel_name:
            raise ValueError("Holding filter wheel must be identifiable")

        if self._is_beyond_wheel_capacity(slot=self.reserved_slot):
            raise ValueError(f"Filter wheel {self.wheel_name} reserved slot must be within the wheel's capacity.")

        if self.reserved_slot in self.occupied_slots:
            raise ValueError(f"Filter wheel {self.wheel_name} reserved slot cannot be occupied")

        _filter_count = len(self.occupied_slots)
        if _filter_count >= self.wheel_capacity:
            filter_noun:str = "filters" if 1 != _filter_count else "filter"
            raise ValueError(f"Filter wheel {self.wheel_name} cannot hold {_filter_count} {filter_noun}")

        for occupied in self.occupied_slots:
            if self._is_beyond_wheel_capacity(slot=occupied):
                _msg = (
                    f"Filter wheel {self.wheel_name} with {self.wheel_capacity} slots, cannot populate slot at index {occupied}"
                )
                raise ValueError(_msg)
        return self


    def _is_beyond_wheel_capacity(self, *, slot: int) -> bool:
        return slot > self.wheel_capacity


    def _is_validly_occupied_and_used(self, *, index: int, strict:bool=True):
        return (
            index in self.occupied_slots
            and (
                not strict or index in self.permitted_slots
            )
        )


    def absorption_calculator_of(self, *, index: int, strict:bool=True) -> FixedDepth:
        """Returns the absorption calculator associated with occupied / reserved wheel slots.

        Args:
            index: The slot to check.
            strict: If False, permission relaxed, so any occupied slots acceptable.

        Raises exceptions if the index is outside the wheel or not in use, per strictness.
        """
        if self._is_beyond_wheel_capacity(slot=index):
            raise ValueError(f"Filter wheel {self.wheel_name} has no slot at index {index}.")
        elif self.is_retracted_at(index=index):
            return self._empty_slot
        elif not self._is_validly_occupied_and_used(index=index, strict=strict):
            raise ValueError(f"Filter wheel {self.wheel_name} has no accessible slot at index {index}")
        return self.occupied_slots[index]


    def active_slots_attenuation_calculators(self, *, strict:bool=True) -> dict[PositiveInt, FixedDepth]:
        """De facto reserved empty slot calculator plus those for filters in place.

        Args:
            strict: When True, the filters lacking permission are excluded.

        Note:
            Permission to use is granted by beamline scientists in configuration,
            and enters this immutable model class at construction time.
        """
        preliminary = { self.reserved_slot: self._empty_slot } | self.occupied_slots
        return {
            index_of_slot: fixed_depth_attenuation_calculator
            for index_of_slot, fixed_depth_attenuation_calculator in preliminary.items()
            if self.is_index_in_use(index=index_of_slot, strict=strict)
        }


    def is_index_in_use(self, *, index: int, strict:bool=True):
        """Is slot index reserved or occupied?

        If strict, occupied slots must also have permission to be in use.
        """
        return (
            self.is_retracted_at(index=index)
            or self._is_validly_occupied_and_used(index=index, strict=strict)
        )


    def is_retracted_at(self, *, index: int):
        """Is the slot index the reserved empty slot?"""
        return index == self.reserved_slot


