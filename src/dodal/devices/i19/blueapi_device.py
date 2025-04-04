import json
from enum import Enum
from typing import TypeVar

from aiohttp import ClientSession
from bluesky.protocols import Movable
from ophyd_async.core import AsyncStatus, StandardReadable

from dodal.log import LOGGER

OPTICS_BLUEAPI_URL = "https://i19-blueapi.diamond.ac.uk"
HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}

D = TypeVar("D")


class HutchState(str, Enum):
    EH1 = "EH1"
    EH2 = "EH2"


class OpticsBlueAPIDevice(StandardReadable, Movable[D]):
    """General device that a REST call to the blueapi instance controlling the optics \
    hutch running on the I19 cluster, which will evaluate the current hutch in use vs \
    the hutch sending the request and decide if the plan will be run or not.

    For details see the architecture described in \
    https://github.com/DiamondLightSource/i19-bluesky/issues/30.
    """

    def __init__(self, name: str = "") -> None:
        self.url = OPTICS_BLUEAPI_URL
        self.headers = HEADERS
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: D):
        """ On set send a POST request to the optics blueapi with the name and \
        parameters, gets the generated task_id and then sends a PUT request that runs \
        the plan.

        Args:
            value (dict): The value passed here should be the parameters for the POST \
                request, taking the form:
                {
                    "name": "plan_name",
                    "params": {
                        "experiment_hutch": f"{hutch_name}",
                        "access_device": "access_control",
                        "other_params": "...",
                        ...
                    }
                }
        """
        # Value here vould be request params dictionary.
        request_params = json.dumps(value)

        async with ClientSession(base_url=self.url, raise_for_status=True) as session:
            # First submit the plan to the worker
            async with session.post(
                "/tasks", data=request_params, headers=HEADERS
            ) as response:
                LOGGER.info(
                    f"Task submitted to the worker, response status: {response.status}"
                )

                try:
                    data = await response.json()
                    task_id = data["task_id"]
                except Exception as e:
                    LOGGER.error(
                        f"Failed to get task_id from {self.url}/tasks POST. ({e})"
                    )
                    raise
            # Then set the task as active and run asap
            async with session.put(
                "/worker/task", data=json.dumps({"task_id": task_id}), headers=HEADERS
            ) as response:
                if not response.ok:
                    LOGGER.error(
                        f"""Session PUT responded with {response.status}: {response.reason}.
                        Unable to run plan {value["name"]}."""  # type: ignore
                    )
                    return
                LOGGER.debug(f"Running plan: {value['name']}, task_id: {task_id}")  # type: ignore
