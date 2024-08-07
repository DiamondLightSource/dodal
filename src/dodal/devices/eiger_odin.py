# type: ignore # Eiger will soon be ophyd-async https://github.com/DiamondLightSource/dodal/issues/700
from ophyd import Component, Device, EpicsSignal, EpicsSignalRO, EpicsSignalWithRBV
from ophyd.areadetector.plugins import HDF5Plugin_V22
from ophyd.sim import NullStatus
from ophyd.status import StatusBase

from dodal.devices.status import await_value


class EigerFan(Device):
    on = Component(EpicsSignalRO, "ProcessConnected_RBV")
    consumers_connected = Component(EpicsSignalRO, "AllConsumersConnected_RBV")
    ready = Component(EpicsSignalRO, "StateReady_RBV")
    zmq_addr = Component(EpicsSignalRO, "EigerAddress_RBV")
    zmq_port = Component(EpicsSignalRO, "EigerPort_RBV")
    state = Component(EpicsSignalRO, "State_RBV")
    frames_sent = Component(EpicsSignalRO, "FramesSent_RBV")
    series = Component(EpicsSignalRO, "CurrentSeries_RBV")
    offset = Component(EpicsSignalRO, "CurrentOffset_RBV")
    forward_stream = Component(EpicsSignalWithRBV, "ForwardStream")
    dev_shm_enable = Component(EpicsSignalWithRBV, "DevShmCache")


class OdinMetaListener(Device):
    initialised = Component(EpicsSignalRO, "ProcessConnected_RBV")
    ready = Component(EpicsSignalRO, "Writing_RBV")
    # file_name should not be set. Set the filewriter file_name and this will be updated in EPICS
    file_name = Component(EpicsSignalRO, "FileName", string=True)
    stop_writing = Component(EpicsSignal, "Stop")
    active = Component(EpicsSignalRO, "AcquisitionActive_RBV")


class OdinFileWriter(HDF5Plugin_V22):
    start_timeout = Component(EpicsSignal, "StartTimeout")
    # id should not be set. Set the filewriter file_name and this will be updated in EPICS
    id = Component(EpicsSignalRO, "AcquisitionID_RBV", string=True)
    image_height = Component(EpicsSignalWithRBV, "ImageHeight")
    image_width = Component(EpicsSignalWithRBV, "ImageWidth")
    plugin_type = None


class OdinNode(Device):
    writing = Component(EpicsSignalRO, "Writing_RBV")
    frames_dropped = Component(EpicsSignalRO, "FramesDropped_RBV")
    frames_timed_out = Component(EpicsSignalRO, "FramesTimedOut_RBV")
    error_status = Component(EpicsSignalRO, "FPErrorState_RBV")
    fp_initialised = Component(EpicsSignalRO, "FPProcessConnected_RBV")
    fr_initialised = Component(EpicsSignalRO, "FRProcessConnected_RBV")
    clear_errors = Component(EpicsSignal, "FPClearErrors")
    num_captured = Component(EpicsSignalRO, "NumCaptured_RBV")
    error_message = Component(EpicsSignalRO, "FPErrorMessage_RBV", string=True)


class OdinNodesStatus(Device):
    node_0 = Component(OdinNode, "OD1:")
    node_1 = Component(OdinNode, "OD2:")
    node_2 = Component(OdinNode, "OD3:")
    node_3 = Component(OdinNode, "OD4:")

    @property
    def nodes(self) -> list[OdinNode]:
        return [self.node_0, self.node_1, self.node_2, self.node_3]

    def check_node_frames_from_attr(
        self, node_get_func, error_message_verb: str
    ) -> tuple[bool, str]:
        nodes_frames_values = [0] * len(self.nodes)
        frames_details = []
        for node_number, node_pv in enumerate(self.nodes):
            nodes_frames_values[node_number] = node_get_func(node_pv)
            error_message = f"Filewriter {node_number} {error_message_verb} \
                    {nodes_frames_values[node_number]} frames"
            frames_details.append(error_message)
        bad_frames = any(v != 0 for v in nodes_frames_values)
        return bad_frames, "\n".join(frames_details)

    def check_frames_timed_out(self) -> tuple[bool, str]:
        return self.check_node_frames_from_attr(
            lambda node: node.frames_timed_out.get(), "timed out"
        )

    def check_frames_dropped(self) -> tuple[bool, str]:
        return self.check_node_frames_from_attr(
            lambda node: node.frames_dropped.get(), "dropped"
        )

    def get_error_state(self) -> tuple[bool, str]:
        is_error = []
        error_messages = []
        for node_number, node_pv in enumerate(self.nodes):
            is_error.append(node_pv.error_status.get())
            if is_error[node_number]:
                error_messages.append(
                    f"Filewriter {node_number} is in an error state with error message\
                     - {node_pv.error_message.get()}"
                )
        return any(is_error), "\n".join(error_messages)

    def get_init_state(self) -> bool:
        is_initialised = []
        for node_pv in self.nodes:
            is_initialised.append(node_pv.fr_initialised.get())
            is_initialised.append(node_pv.fp_initialised.get())
        return all(is_initialised)

    def clear_odin_errors(self):
        clearing_status = NullStatus()
        for node_number, node_pv in enumerate(self.nodes):
            error_message = node_pv.error_message.get()
            if len(error_message) != 0:
                self.log.info(f"Clearing odin errors from node {node_number}")
                clearing_status &= node_pv.clear_errors.set(1)
        clearing_status.wait(10)


class EigerOdin(Device):
    fan = Component(EigerFan, "OD:FAN:")
    file_writer = Component(OdinFileWriter, "OD:")
    meta = Component(OdinMetaListener, "OD:META:")
    nodes = Component(OdinNodesStatus, "")

    def create_finished_status(self) -> StatusBase:
        writing_finished = await_value(self.meta.ready, 0)
        for node_pv in self.nodes.nodes:
            writing_finished &= await_value(node_pv.writing, 0)
        return writing_finished

    def check_odin_state(self) -> bool:
        is_initialised, error_message = self.check_odin_initialised()
        frames_dropped, frames_dropped_details = self.nodes.check_frames_dropped()
        frames_timed_out, frames_timed_out_details = self.nodes.check_frames_timed_out()

        if not is_initialised:
            raise RuntimeError(error_message)
        if frames_dropped:
            self.log.error(f"Frames dropped: {frames_dropped_details}")
        if frames_timed_out:
            self.log.error(f"Frames timed out: {frames_timed_out_details}")

        return is_initialised and not frames_dropped and not frames_timed_out

    def check_odin_initialised(self) -> tuple[bool, str]:
        is_error_state, error_messages = self.nodes.get_error_state()
        to_check = [
            (not self.fan.consumers_connected.get(), "EigerFan is not connected"),
            (not self.fan.on.get(), "EigerFan is not initialised"),
            (not self.meta.initialised.get(), "MetaListener is not initialised"),
            (is_error_state, error_messages),
            (
                not self.nodes.get_init_state(),
                "One or more filewriters is not initialised",
            ),
        ]

        errors = [message for check_result, message in to_check if check_result]

        return not errors, "\n".join(errors)

    def stop(self) -> StatusBase:
        """Stop odin manually"""
        status = self.file_writer.capture.set(0)
        status &= self.meta.stop_writing.set(1)
        return status
