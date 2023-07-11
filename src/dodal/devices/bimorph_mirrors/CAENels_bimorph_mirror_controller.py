from ophyd import Component, Device, EpicsSignal, EpicsSignalRO


class CAENelsBimorphMirrorController(Device):
    busy: EpicsSignalRO = Component(EpicsSignalRO, "BUSY")
    groups_list: EpicsSignalRO = Component(EpicsSignalRO, "GROUPSLIST")
