import inspect
from collections.abc import Iterable
from types import ModuleType
from typing import Any, get_type_hints

from bluesky.utils import MsgGenerator

from dodal import plan_stubs, plans
from dodal.common.types import PlanGenerator

"""
Bluesky distinguishes between `plans`: complete experimental proceedures, which open and
close data collection runs, and which may be part of a larger plan that collect data
multiple times, but may also be run alone to collect data, and `plan_stubs`: which
do not create & complete data collection runs and are either isolated behaviours or
building blocks for plans.

In order to make it clearer when a MsgGenerator can be safely used without considering
the enclosing run (as opening a run whilst in a run without explicitly passing a RunID
is likely to cause both runs to fail), when it is required to manage a run and when
running a procedure will create data documents, we have adopted this standard.

We further impose other requirements on both plans and stubs exported from these modules
to enable them to be exposed in UIs in a consistent way:
- They must have a docstring
- They must not use variadic arguments (*args, **kwargs)
- Plans must and Stubs may have an optional argument for metadata, named "metadata"
- The metadata argument, where present, must be optional with a default of None
"""


def is_bluesky_plan_generator(func: Any) -> bool:
    try:
        return callable(func) and get_type_hints(func).get("return") == MsgGenerator
    except TypeError:
        # get_type_hints fails on some objects (such as Union or Optional)
        return False


def get_all_available_generators(mod: ModuleType) -> Iterable[PlanGenerator]:
    for value in mod.__dict__.values():
        if is_bluesky_plan_generator(value):
            yield value


def assert_hard_requirements(plan: PlanGenerator, signature: inspect.Signature):
    assert plan.__doc__ is not None, f"'{plan.__name__}' has no docstring"
    for parameter in signature.parameters.values():
        assert (
            parameter.kind is not parameter.VAR_POSITIONAL
            and parameter.kind is not parameter.VAR_KEYWORD
        ), f"'{plan.__name__}' has variadic arguments"


def assert_metadata_requirements(plan: PlanGenerator, signature: inspect.Signature):
    assert "metadata" in signature.parameters, (
        f"'{plan.__name__}' does not allow metadata"
    )
    metadata = signature.parameters["metadata"]
    assert metadata.annotation == dict[str, Any] | None and metadata.default is None, (
        f"'{plan.__name__}' metadata is not optional"
    )
    assert metadata.default is None, f"'{plan.__name__}' metadata default is mutable"


def test_plans_comply():
    for plan in get_all_available_generators(plans):
        signature = inspect.Signature.from_callable(plan)
        assert_hard_requirements(plan, signature)
        assert_metadata_requirements(plan, signature)


def test_stubs_comply():
    for stub in get_all_available_generators(plan_stubs):
        signature = inspect.Signature.from_callable(stub)
        assert_hard_requirements(stub, signature)
        if "metadata" in signature.parameters:
            assert_metadata_requirements(stub, signature)
