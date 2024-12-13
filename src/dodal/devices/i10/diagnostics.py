import asyncio

from ophyd_async.core import AsyncStatus, Device, StandardReadable, StrictEnum
from ophyd_async.core import StandardReadableFormat as Format
from ophyd_async.epics.adaravis import AravisDriverIO
from ophyd_async.epics.adcore import (
    ImageMode,
)
from ophyd_async.epics.core import (
    epics_signal_r,
    epics_signal_rw,
)
from ophyd_async.epics.motor import Motor


class D3DropDown(StrictEnum):
    NOTHING = "Nothing"
    GRID = "Grid"


class D5DropDown(StrictEnum):
    CELL_IN = "Cell In"
    CELL_OUT = "Cell Out"


class D6DropDown(StrictEnum):
    OUT_OF_THE_BEAM = "Out of the beam"
    DIODE = "Diode"
    BLADE = "Blade"
    LA = "La ref"
    GD = "Gd ref"
    YB = "Yb ref"
    GRID = "Grid"


class D78ropDown(StrictEnum):
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


class I10WebIODataType(StrictEnum):
    UINT8 = "UInt8"
    INT16 = "UInt16"


class DropDownStage(StandardReadable):
    def __init__(
        self,
        prefix: str,
        positioner_enum: type[StrictEnum],
        positioner_suffix: str = "",
        dropdown_pv_suffix=":MP:SELECT",
        name: str = "",
    ) -> None:
        self.stage_motion = Motor(prefix=prefix + positioner_suffix)
        with self.add_children_as_readables(Format.CONFIG_SIGNAL):
            self.stage_drop_down = epics_signal_rw(
                positioner_enum, read_pv=prefix + positioner_suffix + dropdown_pv_suffix
            )
        super().__init__(name=name)


class I10PneumaticStage(StandardReadable):
    def __init__(
        self,
        prefix: str,
        stage_write_enum: type[StrictEnum],
        stage_read_enum: type[StrictEnum],
        stage_read_suffix="STA",
        stage_write_suffix="CON",
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
    def __init__(
        self,
        prefix: str,
        cam_infix: str = "CAM:",
        stat_infix: str = "STAT:",
        name: str = "",
    ) -> None:
        # self.data_type = epics_signal_r(I10WebIODataType, prefix + "DataType_RBV")
        super().__init__(prefix + cam_infix, name)
        self.data_type = epics_signal_r(
            I10WebIODataType, prefix + cam_infix + "DataType_RBV"
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


class I10CentroidDetector(StandardReadable):
    def __init__(
        self,
        prefix: str,
        name="",
    ) -> None:
        self.cam = I10AravisDriverIO(prefix=prefix)

        self.add_readables(
            [self.cam.array_counter, self.cam.centroid_x, self.cam.centroid_y],
            Format.HINTED_UNCACHED_SIGNAL,
        )

        self.add_readables([self.cam.acquire_time], Format.CONFIG_SIGNAL)

        super().__init__(name=name)

    @AsyncStatus.wrap
    async def stage(self) -> None:
        await asyncio.gather(
            self.cam.image_mode.set(ImageMode.SINGLE),
            self.cam.wait_for_plugins.set(True),
        )
        await super().stage()

    @AsyncStatus.wrap
    async def trigger(self) -> None:
        await self.cam.acquire.set(True)


class SceenCam(Device):
    def __init__(
        self,
        prefix: str,
        stage_write_enum: type[StrictEnum] = InOutTable,
        stage_read_enum: type[StrictEnum] = InOutReadBackTable,
        stage_read_suffix="STA",
        stage_write_suffix="CON",
        cam_inffix="DCAM:",
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
            prefix=prefix + cam_inffix,
        )
        super().__init__(name=name)


class FullDiagonostic(SceenCam):
    def __init__(
        self,
        prefix: str,
        positioner_enum: type[StrictEnum],
        positioner_suffix: str = "",
        dropdown_pv_suffix=":MP:SELECT",
        stage_write_enum: type[StrictEnum] = InOutTable,
        stage_read_enum: type[StrictEnum] = InOutReadBackTable,
        stage_read_suffix="STA",
        stage_write_suffix="CON",
        cam_inffix="DCAM:",
        name: str = "",
    ) -> None:
        self.positioner = DropDownStage(
            prefix=prefix,
            positioner_enum=positioner_enum,
            positioner_suffix=positioner_suffix,
            dropdown_pv_suffix=dropdown_pv_suffix,
        )
        super().__init__(
            prefix,
            stage_write_enum,
            stage_read_enum,
            stage_read_suffix,
            stage_write_suffix,
            cam_inffix,
            name,
        )


class Diagnostic(Device):
    def __init__(self, prefix, name: str = "") -> None:
        self.d1 = SceenCam(prefix=prefix + "PHDGN-01:")
        self.d2 = SceenCam(prefix=prefix + "PHDGN-02:")
        self.d3 = FullDiagonostic(
            prefix=prefix + "PHDGN-03:",
            positioner_enum=D3DropDown,
            positioner_suffix="DET:X",
        )
        self.d4 = SceenCam(prefix=prefix + "PHDGN-04:")
        self.d5 = DropDownStage(
            prefix=prefix + "IONC-01:",
            positioner_enum=D5DropDown,
            positioner_suffix="Y",
        )
        self.d6 = FullDiagonostic(
            prefix=prefix + "PHDGN-0",
            positioner_enum=D6DropDown,
            positioner_suffix="6:DET:X",
            stage_read_suffix="5:STA",
            stage_write_suffix="5:CON",
            cam_inffix="5:DCAM:",
        )
        self.d7 = DropDownStage(
            prefix=prefix + "PHDGN-07:",
            positioner_enum=D78ropDown,
            positioner_suffix="Y",
        )
        super().__init__(name)
