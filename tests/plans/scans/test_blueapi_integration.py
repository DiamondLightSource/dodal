"""Check the scan plans can be registered, described and run by blueapi."""

import json
from collections.abc import Mapping
from typing import Any

import pytest
from blueapi.config import EnvironmentConfig, PlanSource
from blueapi.core import BlueskyContext
from blueapi.service.model import PlanModel
from blueapi.worker.task import Task
from bluesky.run_engine import RunEngine
from ophyd_async.core import StandardDetector

from dodal.devices.motors import Motor
from dodal.plans import scans


@pytest.fixture
def context(
    run_engine: RunEngine, det: StandardDetector, x_axis: Motor, y_axis: Motor
) -> BlueskyContext:
    context = BlueskyContext(run_engine=run_engine)
    context.with_plan_module(scans)
    for device in (det, x_axis, y_axis):
        context.register_device(device)
    return context


def test_all_scan_plans_load_from_blueapi_config(run_engine: RunEngine):
    context = BlueskyContext(run_engine=run_engine)
    # The same as a beamline's blueapi config with a planFunctions source.
    context.with_config(
        EnvironmentConfig(sources=[PlanSource(module="dodal.plans.scans")])
    )
    assert set(context.plans) == set(scans.__all__)


@pytest.mark.parametrize("plan_name", scans.__all__)
def test_plan_schema_is_serialisable_without_callable_parameters(
    context: BlueskyContext, plan_name: str
):
    # This is what blueapi returns to clients from GET /plans.
    plan_model = PlanModel.from_plan(context.plans[plan_name])
    json.dumps(plan_model.model_dump(by_alias=True))
    assert (
        plan_model.parameter_schema["properties"]
        .keys()
        .isdisjoint({"per_step", "per_shot"})
    )
    assert plan_model.description
    assert "per_step" not in plan_model.description
    assert "per_shot" not in plan_model.description


@pytest.mark.parametrize(
    "plan_name, args, params, num_events",
    [
        ("step_scan", [["det"], "x_axis", 0, 1, 0.5, "y_axis", 0, 0.1], {}, 3),
        ("step_rscan", [[], "x_axis", -1, 1, 0.5], {}, 5),
        ("step_grid_scan", [[], "x_axis", 0, 1, 0.5, "y_axis", 0, 1, 1], {}, 6),
        (
            "step_grid_rscan",
            [[], "x_axis", 0, 1, 0.5, "y_axis", 0, 1, 1],
            {"snake_axes": False},
            6,
        ),
        ("count", [["det"]], {"num": 2}, 2),
        ("scan", [[], "x_axis", 0, 1, "y_axis", 0, 2], {"num": 3}, 3),
        ("rel_scan", [[], "x_axis", 0, 1], {"num": 3}, 3),
        ("log_scan", [[], "x_axis", 1, 10, 3], {}, 3),
        ("rel_log_scan", [[], "x_axis", 1, 10, 3], {}, 3),
        ("list_scan", [[], "x_axis", [0, 1, 2]], {}, 3),
        ("rel_list_scan", [[], "x_axis", [0, 1, 2]], {}, 3),
        ("grid_scan", [[], "x_axis", 0, 1, 2, "y_axis", 0, 1, 3], {}, 6),
        ("rel_grid_scan", [[], "x_axis", 0, 1, 2, "y_axis", 0, 1, 3], {}, 6),
        ("list_grid_scan", [[], "x_axis", [0, 1], "y_axis", [0, 1, 2]], {}, 6),
        ("rel_list_grid_scan", [[], "x_axis", [0, 1], "y_axis", [0, 1, 2]], {}, 6),
        (
            "spec_scan",
            [],
            {
                "detectors": ["det"],
                "spec": {
                    "type": "Linspace",
                    "axis": "x_axis",
                    "start": 0,
                    "stop": 1,
                    "num": 3,
                },
            },
            3,
        ),
    ],
)
def test_plan_runs_as_blueapi_task(
    context: BlueskyContext,
    run_engine_documents: Mapping[str, list[dict]],
    plan_name: str,
    args: list[Any],
    params: dict[str, Any],
    num_events: int,
):
    # Arguments are given as a client would send them, with devices as names.
    Task(name=plan_name, args=args, params=params).do_task(context)
    assert run_engine_documents["start"][0]["plan_name"] == plan_name
    assert len(run_engine_documents["event"]) == num_events


def test_task_resolves_device_names_in_step_scan_args(
    context: BlueskyContext, det: StandardDetector, x_axis: Motor
):
    task = Task(name="step_scan", args=[["det"], "x_axis", 0, 1, 0.5])
    args, _ = task.prepare_params(context)

    assert args == [[det], x_axis, 0, 1, 0.5]
    assert [type(arg) for arg in args[2:]] == [int, int, float]
