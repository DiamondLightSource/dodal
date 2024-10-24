import inspect
from types import ModuleType
from typing import Any, get_type_hints

from bluesky.utils import MsgGenerator

from dodal import plan_stubs, plans
from dodal.common.types import PlanGenerator


def is_bluesky_plan_generator(func: Any) -> bool:
    try:
        return callable(func) and get_type_hints(func).get("return") == MsgGenerator
    except TypeError:
        # get_type_hints fails on some objects (such as Union or Optional)
        return False


def get_all_available_generators(mod: ModuleType):
    def get_named_subset(names: list[str]):
        for name in names:
            yield getattr(mod, name)

    if explicit_exports := mod.__dict__.get("__export__"):
        yield from get_named_subset(explicit_exports)
    elif implicit_exports := mod.__dict__.get("__all__"):
        yield from get_named_subset(implicit_exports)
    else:
        for name, value in mod.__dict__.items():
            if not name.startswith("_"):
                yield value


def assert_hard_requirements(plan: PlanGenerator, signature: inspect.Signature):
    assert plan.__doc__ is not None, f"'{plan.__name__}' has no docstring"
    for parameter in signature.parameters.values():
        assert (
            parameter.kind is not parameter.VAR_POSITIONAL
            and parameter.kind is not parameter.VAR_KEYWORD
        ), f"'{plan.__name__}' has variadic arguments"


def assert_metadata_requirements(plan: PlanGenerator, signature: inspect.Signature):
    assert (
        "metadata" in signature.parameters
    ), f"'{plan.__name__}' does not allow metadata"
    metadata = signature.parameters["metadata"]
    assert (
        metadata.annotation == dict[str, Any] | None
        and metadata.default is not inspect.Parameter.empty
    ), f"'{plan.__name__}' metadata is not optional"
    assert metadata.default is None, f"'{plan.__name__}' metadata default is mutable"


def test_plans_comply():
    for plan in get_all_available_generators(plans):
        if is_bluesky_plan_generator(plan):
            signature = inspect.Signature.from_callable(plan)
            assert_hard_requirements(plan, signature)
            assert_metadata_requirements(plan, signature)


def test_stubs_comply():
    for stub in get_all_available_generators(plan_stubs):
        if is_bluesky_plan_generator(stub):
            signature = inspect.Signature.from_callable(stub)
            assert_hard_requirements(stub, signature)
            if "metadata" in signature.parameters:
                assert_metadata_requirements(stub, signature)
