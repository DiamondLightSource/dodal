from unittest import TestCase

import pytest

from dodal.devices.i19.shutter import (
    HutchConditionalShutter,
    HutchInvalidError,
    HutchState,
)


async def unit_test_shutter_created_without_raising_errors(hutch_controlling_shutter: HutchState):
    fake_prefix = "I74"
    shutter_name = "GrandOldShutter"
    hcs = HutchConditionalShutter(fake_prefix, hutch_controlling_shutter, shutter_name)
    test_case = TestCase()
    test_case.assertIsInstance(hcs, HutchConditionalShutter)


async def test_shutter_created_for_eh_one_without_raising_errors():
    hutch_from_which_shutter_is_controlled = HutchState.EH1
    await unit_test_shutter_created_without_raising_errors(hutch_from_which_shutter_is_controlled)


async def test_shutter_created_for_eh_two_without_raising_errors():
    hutch_from_which_shutter_is_controlled = HutchState.EH2
    await unit_test_shutter_created_without_raising_errors(hutch_from_which_shutter_is_controlled)


async def test_shutter_not_created_for_invalid_hutch():
    not_a_hutch = HutchState.INVALID
    with pytest.raises(HutchInvalidError):
        await unit_test_shutter_created_without_raising_errors(not_a_hutch)
