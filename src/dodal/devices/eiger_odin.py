# type: ignore # Eiger will soon be ophyd-async https://github.com/DiamondLightSource/dodal/issues/700
from functools import partial, reduce

from ophyd import Component, Device, EpicsSignal, EpicsSignalRO, EpicsSignalWithRBV
from ophyd.areadetector.plugins import HDF5Plugin_V22
from ophyd.sim import NullStatus
from ophyd.status import StatusBase, SubscriptionStatus

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

    def _check_node_frames_from_attr(
        self, node_get_func, error_message_verb: str
    ) -> tuple[bool, str]:
        nodes_frames_values = [0] * len(self.nodes)
        frames_details = []
        for node_number, node_pv in enumerate(self.nodes):
            node_state = node_get_func(node_pv)
            nodes_frames_values[node_number] = node_state
            if node_state != 0:
                error_message = f"Filewriter {node_number} {error_message_verb} \
                        {nodes_frames_values[node_number]} frames"
                frames_details.append(error_message)
        bad_frames = any(v != 0 for v in nodes_frames_values)
        return bad_frames, "\n".join(frames_details)

    def check_frames_timed_out(self) -> tuple[bool, str]:
        return self._check_node_frames_from_attr(
            lambda node: node.frames_timed_out.get(), "timed out"
        )

    def check_frames_dropped(self) -> tuple[bool, str]:
        return self._check_node_frames_from_attr(
            lambda node: node.frames_dropped.get(), "dropped"
        )

    def wait_for_no_errors(self, timeout) -> dict[SubscriptionStatus, str]:
        errors = {}
        for node_number, node_pv in enumerate(self.nodes):
            errors[await_value(node_pv.error_status, False, timeout)] = (
                f"Filewriter {node_number} is in an error state with error message\
                     - {node_pv.error_message.get()}"
            )

        return errors

    def get_init_state(self, timeout) -> SubscriptionStatus:
        is_initialised = []
        for node_pv in self.nodes:
            is_initialised.append(await_value(node_pv.fr_initialised, True, timeout))
            is_initialised.append(await_value(node_pv.fp_initialised, True, timeout))
        return reduce(lambda x, y: x & y, is_initialised)

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

    def check_and_wait_for_odin_state(self, timeout) -> bool:
        is_initialised, error_message = self.wait_for_odin_initialised(timeout)
        frames_dropped, frames_dropped_details = self.nodes.check_frames_dropped()
        frames_timed_out, frames_timed_out_details = self.nodes.check_frames_timed_out()

        if not is_initialised:
            raise RuntimeError(error_message)
        if frames_dropped:
            self.log.error(f"Frames dropped: {frames_dropped_details}")
        if frames_timed_out:
            self.log.error(f"Frames timed out: {frames_timed_out_details}")

        return is_initialised and not frames_dropped and not frames_timed_out

    def wait_for_odin_initialised(self, timeout) -> tuple[bool, str]:
        errors = self.nodes.wait_for_no_errors(timeout)
        await_true = partial(await_value, expected_value=True, timeout=timeout)
        errors[
            await_value(
                self.fan.consumers_connected, expected_value=True, timeout=timeout
            )
        ] = "EigerFan is not connected"
        errors[await_true(self.fan.on)] = "EigerFan is not initialised"
        errors[await_true(self.meta.initialised)] = "MetaListener is not initialised"
        errors[self.nodes.get_init_state(timeout)] = (
            "One or more filewriters is not initialised"
        )

        error_strings = []

        for error_status, string in errors.items():
            try:
                error_status.wait(timeout=timeout)
            except Exception:
                error_strings.append(string)

        return not error_strings, "\n".join(error_strings)

    def stop(self) -> StatusBase:
        """Stop odin manually"""
        status = self.file_writer.capture.set(0)
        status &= self.meta.stop_writing.set(1)
        return status
