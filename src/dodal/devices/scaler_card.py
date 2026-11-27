from collections.abc import MutableMapping
from typing import Generic, TypeVar

from bluesky.protocols import Movable, Triggerable
from ophyd_async.core import (
    DEFAULT_TIMEOUT,
    AsyncStatus,
    Device,
    Reference,
    StandardReadable,
    StandardReadableFormat,
    StrictEnum,
    default_mock_class,
    wait_for_value,
)
from ophyd_async.epics.core import epics_signal_rw

from dodal.devices.util.mock_behaviour import reset_signal_on_update_mock_factory

CountModeT = TypeVar("CountModeT", bound=StrictEnum)


@default_mock_class(reset_signal_on_update_mock_factory("start_count", True, False))
class ScalerCardController(
    StandardReadable, Triggerable, Movable[float], Generic[CountModeT]
):
    """Control a scaler card and its readable channels.

    The scaler card is configured with an integration time and can be
    triggered to start a counting period. The counting period is complete
    when the start-count signal returns to ``False``.

    All scaler cards have a count mode, but its options depend on the model, so the
    mode enum is given by the subclass. The count mode can optionally be changed
    when the card is staged and unstaged, e.g. to only acquire triggered counts
    while staged.
    """

    def __init__(
        self,
        prefix: str,
        start_count_suffix: str,
        count_suffix: str,
        count_mode_suffix: str,
        count_mode_type: type[CountModeT],
        stage_mode: CountModeT | None = None,
        unstage_mode: CountModeT | None = None,
        name: str = "",
    ):
        """Configure the scaler card controller.

        Args:
            prefix: PV prefix of the scaler card.
            start_count_suffix: PV suffix to start a count.
            count_suffix: PV suffix of the integration time.
            count_mode_suffix: PV suffix of the count mode.
            count_mode_type: Enum of the count mode options for this card model.
            stage_mode: Count mode to set on stage. If None, the mode is not changed.
            unstage_mode: Count mode to set on unstage. If None, the mode is not
                changed.
            name: Name of the device.
        """
        self._stage_mode = stage_mode
        self._unstage_mode = unstage_mode
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.integration_time = epics_signal_rw(float, prefix + count_suffix)
            self.count_mode = epics_signal_rw(
                count_mode_type, prefix + count_mode_suffix
            )

        self.start_count = epics_signal_rw(bool, prefix + start_count_suffix)
        super().__init__(name)

    @AsyncStatus.wrap
    async def stage(self) -> None:
        """Set the configured stage count mode, if any."""
        if self._stage_mode is not None:
            await self.count_mode.set(self._stage_mode)
        await super().stage()

    @AsyncStatus.wrap
    async def unstage(self) -> None:
        """Set the configured unstage count mode, if any."""
        if self._unstage_mode is not None:
            await self.count_mode.set(self._unstage_mode)
        await super().unstage()

    @AsyncStatus.wrap
    async def set(self, value: float):
        """Set the scaler integration time."""
        await self.integration_time.set(value)

    @AsyncStatus.wrap
    async def trigger(self):
        """Start a scaler count and wait for it to complete."""
        await self.start_count.set(True)
        timeout = await self.integration_time.get_value() + DEFAULT_TIMEOUT
        await wait_for_value(self.start_count, False, timeout)


class CountMode(StrictEnum):
    """Count mode options of a Struck scaler card ("Count Mode" on the screen)."""

    AUTO = "AutoCount"
    ONE_SHOT = "OneShot"


class Struck32ChannelScaler(ScalerCardController[CountMode]):
    """Controller for a Struck 32 channel scaler card (SIS3820), using the EPICS scaler
    record.

    There should be one instance per physical card. It owns the card level controls
    (integration time, delay time, starting a count and count mode). Channels can be
    grouped with :class:`ScalerCard`, or exposed individually for current amplifiers
    with :class:`dodal.devices.current_amplifiers.StruckScalerChannel`.

    Attributes:
        prefix (str): PV prefix of the card, used to build channel PVs.
        count_mode (SignalRW[CountMode]): Counting card setting.
        integration_time (SignalRW[float]): Count time.
        delay_time (SignalRW[float]): Delay before counting starts.
        start_count (SignalRW[bool]): Start a count, returns to False when done.
    """

    def __init__(
        self,
        prefix: str,
        stage_mode: CountMode | None = None,
        unstage_mode: CountMode | None = None,
        name: str = "",
    ):
        """Configure the Struck scaler card controller.

        Args:
            prefix: PV prefix of the scaler card.
            stage_mode: Count mode to set on stage. If None, the mode is not changed.
            unstage_mode: Count mode to set on unstage. If None, the mode is not
                changed.
            name: Name of the device.
        """
        self.prefix = prefix
        with self.add_children_as_readables(StandardReadableFormat.CONFIG_SIGNAL):
            self.delay_time = epics_signal_rw(float, prefix + ".DLY")
        super().__init__(
            prefix=prefix,
            start_count_suffix=".CNT",
            count_suffix=".TP",
            count_mode_suffix=":AutoCount",
            count_mode_type=CountMode,
            stage_mode=stage_mode,
            unstage_mode=unstage_mode,
            name=name,
        )


class ScanMode(StrictEnum):
    """Scan mode options of a Hytec 8512 scaler card ("SCAN MODE" on the screen)."""

    FAST = "Fast"
    NORMAL = "Normal"


class Hytec8512Scaler(ScalerCardController[ScanMode]):
    """Controller for a Hytec 8512 scaler card.

    Unlike the Struck card, it does not use the EPICS scaler record field names and
    has no delay time.

    Attributes:
        count_mode (SignalRW[ScanMode]): Scan mode of the card.
        integration_time (SignalRW[float]): Count time.
        start_count (SignalRW[bool]): Start a count, returns to False when done.
    """

    def __init__(
        self,
        prefix: str,
        stage_mode: ScanMode | None = None,
        unstage_mode: ScanMode | None = None,
        name: str = "",
    ):
        """Configure the Hytec 8512 scaler card controller.

        Args:
            prefix: PV prefix of the scaler card.
            stage_mode: Scan mode to set on stage. If None, the mode is not changed.
            unstage_mode: Scan mode to set on unstage. If None, the mode is not
                changed.
            name: Name of the device.
        """
        super().__init__(
            prefix=prefix,
            start_count_suffix="STARTCOUNT",
            count_suffix="PRESET",
            count_mode_suffix="Mode",
            count_mode_type=ScanMode,
            stage_mode=stage_mode,
            unstage_mode=unstage_mode,
            name=name,
        )


DeviceT = TypeVar("DeviceT", bound=Device)


class ScalerCard(StandardReadable, Triggerable, Movable[float], Generic[DeviceT]):
    """Expose a logical group of channels from a scaler card.

    The channels are exposed as a readable device and are associated with a
    :class:`ScalerCardController` that controls the underlying scaler card. Multiple
    instances of this class can share the same controller, allowing different groups of
    scaler channels to be exposed as separate logical devices while being acquired by
    the same physical scaler card. The channels are also added as readables with the
    controller, so the controller exposes all channels associated with the scaler card.
    This allows the controller to represent the complete set of scaler channels, while
    each  :class:`ScalerCard` instance provides access to only its associated
    group. Calling :meth:`set` sets the scaler integration time via the controller,
    while :meth:`trigger` starts the controller count and waits for it to complete.
    """

    def __init__(
        self, channels: DeviceT, controller: ScalerCardController, name: str = ""
    ):
        with self.add_children_as_readables():
            self.channel = channels

        # ophyd-async DeviceVector/DeviceMap case
        if isinstance(channels, MutableMapping):
            controller.add_readables(list(channels.values()))
        else:
            controller.add_readables([channels])

        self.add_readables(
            [controller.integration_time], StandardReadableFormat.CONFIG_SIGNAL
        )
        self.controller_ref = Reference(controller)
        super().__init__(name)

    @AsyncStatus.wrap
    async def set(self, value: float):
        """Set the scaler integration time on the controller."""
        await self.controller_ref().set(value)

    @AsyncStatus.wrap
    async def trigger(self):
        """Start a scaler count on the controller and wait for it to complete."""
        await self.controller_ref().trigger()
