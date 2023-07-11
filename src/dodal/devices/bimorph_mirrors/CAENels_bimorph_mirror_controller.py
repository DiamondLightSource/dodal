from ophyd import Component, Device, EpicsSignal, EpicsSignalRO


class CAENelsBimorphMirrorController(Device):
    connected: EpicsSignalRO = Component(EpicsSignalRO, "ASYN.CNCT")
    busy: EpicsSignalRO = Component(EpicsSignalRO, "BUSY")
    groups_list: EpicsSignalRO = Component(EpicsSignalRO, "GROUPSLIST")
