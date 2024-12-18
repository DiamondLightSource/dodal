import asyncio

from bluesky.protocols import Triggerable
from ophyd_async.core import AsyncStatus, Device, StandardReadable, StrictEnum
from ophyd_async.core import StandardReadableFormat as Format
from ophyd_async.core._device import DeviceConnector
from ophyd_async.epics.adaravis import AravisDriverIO
from ophyd_async.epics.adcore import (
    ImageMode,
)
from ophyd_async.epics.core import (
    epics_signal_r,
    epics_signal_rw,
)
from ophyd_async.epics.motor import Motor

from dodal.devices.current_amplifiers import (
    CurrentAmpDet,
    Femto3xxGainTable,
    Femto3xxGainToCurrentTable,
    Femto3xxRaiseTime,
    FemtoDDPCA,
    StruckScaler,
)


class D3DropDown(StrictEnum):
    NOTHING = "Nothing"
    GRID = "Grid"


class D5DropDown(StrictEnum):
    CELL_IN = "Cell In"
    CELL_OUT = "Cell Out"


class D5ADropDown(StrictEnum):
    OUT_OF_THE_BEAM = "Out of the beam"
    DIODE = "Diode"
    BLADE = "Blade"
    LA = "La ref"
    GD = "Gd ref"
    YB = "Yb ref"
    GRID = "Grid"


class D6DropDown(StrictEnum):
    DIODE_OUT = "Diode Out"
    DIODE_IN = "Diode In"
    AU_MESH = "Au Mesh"


class D7DropDown(StrictEnum):
    OUT = "Out"
    SHUTTER = "Shutter"


class InOutTable(StrictEnum):
    MOVE_IN = "Move In"
    MOVE_OUT = "Move Out"
    RESET = "Reset"


class InOutReadBackTable(StrictEnum):
    MOVE_IN = "Moving In"
    MOVE_OUT = "Moving Out"
    IN_BEAM = "In Beam"
    FAULT = "Fault"
    OUT_OF_BEAM = "Out of Beam"


class I10WebCamIODataType(StrictEnum):
    UINT8 = "UInt8"
    INT16 = "UInt16"


class DropDownStage(StandardReadable):
    """1D stage with a enum table to select positions."""

    def __init__(
        self,
        prefix: str,
        positioner_enum: type[StrictEnum],
        positioner_suffix: str = "",
        dropdown_pv_suffix: str = ":MP:SELECT",
        name: str = "",
    ) -> None:
        self.stage_motion = Motor(prefix=prefix + positioner_suffix)
        with self.add_children_as_readables(Format.CONFIG_SIGNAL):
            self.stage_drop_down = epics_signal_rw(
                positioner_enum, read_pv=prefix + positioner_suffix + dropdown_pv_suffix
            )
        super().__init__(name=name)


class I10PneumaticStage(StandardReadable):
    """Pneumatic stage only has two real positions in or out.
    Use for fluorescent screen which can be insert into the x-ray beam,
    Most often use in conjunction with a webcam to locate the x-ray beam."""

    def __init__(
        self,
        prefix: str,
        stage_write_enum: type[StrictEnum],
        stage_read_enum: type[StrictEnum],
        stage_read_suffix: str = "STA",
        stage_write_suffix: str = "CON",
        name: str = "",
    ) -> None:
        with self.add_children_as_readables(Format.HINTED_SIGNAL):
            self.stage_drop_down_set = epics_signal_rw(
                stage_write_enum,
                read_pv=prefix + stage_write_suffix,
            )
            self.stage_drop_down_readback = epics_signal_r(
                stage_read_enum,
                read_pv=prefix + stage_read_suffix,
            )
        super().__init__(name=name)


class I10AravisDriverIO(AravisDriverIO):
    """This is the standard webcam that can be found in ophyd_async
    with four extra centroid signal. There is also a change in data_type due to it being
    a older/different model"""

    def __init__(
        self,
        prefix: str,
        cam_infix: str = "CAM:",
        stat_infix: str = "STAT:",
        name: str = "",
    ) -> None:
        super().__init__(prefix + cam_infix, name)

        # data type correction for i10 model.
        self.data_type = epics_signal_r(
            I10WebCamIODataType, prefix + cam_infix + "DataType_RBV"
        )
        # centroid x-y position
        self.centroid_x = epics_signal_r(float, prefix + stat_infix + "CentroidX_RBV")
        self.centroid_x_sigma = epics_signal_r(
            float, prefix + stat_infix + "CentroidX_RBV"
        )
        self.centroid_y = epics_signal_r(float, prefix + stat_infix + "CentroidX_RBV")
        self.centroid_x_sigma = epics_signal_r(
            float, prefix + stat_infix + "CentroidY_RBV"
        )


class I10CentroidDetector(StandardReadable, Triggerable):
    """Detector to read out the centroid position,
    this is base off the SingleTriggerDetector in ophyd_async with added
    readable default"""

    def __init__(
        self,
        prefix: str,
        name: str = "",
    ) -> None:
        self.drv = I10AravisDriverIO(prefix=prefix)
        self.add_readables(
            [self.drv.array_counter, self.drv.centroid_x, self.drv.centroid_y],
            Format.HINTED_UNCACHED_SIGNAL,
        )

        self.add_readables([self.drv.acquire_time], Format.CONFIG_SIGNAL)

        super().__init__(name=name)

    @AsyncStatus.wrap
    async def stage(self) -> None:
        await asyncio.gather(
            self.drv.image_mode.set(ImageMode.SINGLE),
            self.drv.wait_for_plugins.set(True),
        )
        await super().stage()

    @AsyncStatus.wrap
    async def trigger(self) -> None:
        await self.drv.acquire.set(True)


class ScreenCam(Device):
    """Compound device of pneumatic stage(fluorescent screen) and webcam"""

    def __init__(
        self,
        prefix: str,
        stage_write_enum: type[StrictEnum] = InOutTable,
        stage_read_enum: type[StrictEnum] = InOutReadBackTable,
        stage_read_suffix: str = "STA",
        stage_write_suffix: str = "CON",
        cam_infix="DCAM:",
        name: str = "",
    ) -> None:
        self.screen_stage = I10PneumaticStage(
            prefix=prefix,
            stage_read_enum=stage_read_enum,
            stage_write_enum=stage_write_enum,
            stage_read_suffix=stage_read_suffix,
            stage_write_suffix=stage_write_suffix,
        )
        self.single_trigger_centroid = I10CentroidDetector(
            prefix=prefix + cam_infix,
        )
        super().__init__(name=name)


class FullDiagnostic(Device):
    """Compound device of a diagnostic with screen, webcam and dropdown stage."""

    def __init__(
        self,
        prefix: str,
        positioner_enum: type[StrictEnum],
        positioner_suffix: str = "",
        dropdown_pv_suffix: str = ":MP:SELECT",
        stage_write_enum: type[StrictEnum] = InOutTable,
        stage_read_enum: type[StrictEnum] = InOutReadBackTable,
        stage_read_suffix: str = "STA",
        stage_write_suffix: str = "CON",
        cam_infix: str = "DCAM:",
        name: str = "",
    ) -> None:
        self.positioner = DropDownStage(
            prefix=prefix,
            positioner_enum=positioner_enum,
            positioner_suffix=positioner_suffix,
            dropdown_pv_suffix=dropdown_pv_suffix,
        )
        self.screen = ScreenCam(
            prefix,
            stage_write_enum,
            stage_read_enum,
            stage_read_suffix,
            stage_write_suffix,
            cam_infix,
            name,
        )
        super().__init__(name)


class I10Diagnostic(Device):
    """Collection of all the diagnostic stage on i10."""

    def __init__(self, prefix, name: str = "") -> None:
        self.d1 = ScreenCam(prefix=prefix + "PHDGN-01:")
        self.d2 = ScreenCam(prefix=prefix + "PHDGN-02:")
        self.d3 = FullDiagnostic(
            prefix=prefix + "PHDGN-03:",
            positioner_enum=D3DropDown,
            positioner_suffix="DET:X",
        )
        self.d4 = ScreenCam(prefix=prefix + "PHDGN-04:")
        self.d5 = DropDownStage(
            prefix=prefix + "IONC-01:",
            positioner_enum=D5DropDown,
            positioner_suffix="Y",
        )

        self.d5A = DropDownStage(
            prefix=prefix + "PHDGN-06:",
            positioner_enum=D5ADropDown,
            positioner_suffix="DET:X",
        )

        self.d6 = FullDiagnostic(
            prefix=prefix + "PHDGN-05:",
            positioner_enum=D6DropDown,
            positioner_suffix="DET:X",
        )
        self.d7 = DropDownStage(
            prefix=prefix + "PHDGN-07:",
            positioner_enum=D7DropDown,
            positioner_suffix="Y",
        )
        super().__init__(name)


class I10Diagnotic5ADet(Device):
    """Diagnotic 5a detection with drain current and photo diode"""

    def __init__(
        self, prefix: str, name: str = "", connector: DeviceConnector | None = None
    ) -> None:
        self.drain_current = CurrentAmpDet(
            current_amp=FemtoDDPCA(
                prefix=prefix + "IAMP-06:",
                suffix="GAIN",
                gain_table=Femto3xxGainTable,
                gain_to_current_table=Femto3xxGainToCurrentTable,
                raise_timetable=Femto3xxRaiseTime,
            ),
            counter=StruckScaler(prefix=prefix + "SCLR-02:SCALER2", suffix=".S17"),
        )
        self.diode = CurrentAmpDet(
            FemtoDDPCA(
                prefix=prefix + "IAMP-05:",
                suffix="GAIN",
                gain_table=Femto3xxGainTable,
                gain_to_current_table=Femto3xxGainToCurrentTable,
                raise_timetable=Femto3xxRaiseTime,
            ),
            counter=StruckScaler(prefix=prefix + "SCLR-02:SCALER2", suffix=".S18"),
        )
        super().__init__(name, connector)
