from ophyd_async.core import StrictEnum
from ophyd_async.epics import adcore

# from ophyd_async.epics.adcore import NDFileHDFIO
from ophyd_async.epics.core import epics_signal_rw_rbv


class MerlinImageMode(StrictEnum):
    SINGLE = "Single"
    MULTIPLE = "Multiple"
    CONTINUOUS = "Continuous"
    THRESHOLD = "Threshold"
    BACKGROUND = "Background"


# Not needed with ADCore 3-12 version:
# class MerlinDataType(StrictEnum):
#     INT8 = "Int8"
#     UINT8 = "UInt8"
#     INT16 = "Int16"
#     UINT16 = "UInt16"
#     INT32 = "Int32"
#     UINT32 = "UInt32"
#     FLOAT32 = "Float32"
#     FLOAT64 = "Float64"

# Not needed with ADCore 3-12 version:
# class MerlinCompression(StrictEnum):
#     NONE = "None"
#     NBIT = "N-bit"
#     SZIP = "szip"
#     ZLIB = "zlib"
#     BLOSC = "blosc"


class MerlinDriverIO(adcore.ADBaseIO):
    def __init__(self, prefix: str, name: str = "") -> None:
        super().__init__(prefix, name)
        self.image_mode = epics_signal_rw_rbv(MerlinImageMode, prefix + "ImageMode")
        # self.data_type = epics_signal_rw_rbv(MerlinDataType, prefix + "DataType")


# Not needed with ADCore 3-12 version:
# class MerlinNDFileHDFIO(NDFileHDFIO):
#     def __init__(self, prefix: str, name: str = "") -> None:
#         super().__init__(prefix, name)
# self.data_type = epics_signal_rw_rbv(MerlinDataType, prefix + "DataType")
# self.compression = epics_signal_rw_rbv(
#     MerlinCompression, prefix + "Compression"
# )
