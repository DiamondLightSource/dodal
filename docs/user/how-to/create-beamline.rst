Creating a new beamline
-----------------------

A beamline is a collection of devices that can be used together to run experiments, they may be read-only or capable of being set.
They include motors in the experiment hutch, optical components in the optics hutch, the synchrotron "machine" and more.

The following example creates a fictitious beamline ``w41``, with a simulated twin ``s41``.
``w41`` needs to monitor the status of the Synchrotron and has an AdAravisDetector.
``s41`` has a simulated clone of the AdAravisDetector, but not of the Synchrotron machine.

.. code-block:: python

    from dodal.common.beamlines.beamline_utils import device_instantiation
    from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
    from dodal.devices.areadetector.adaravis import AdAravisDetector
    from dodal.devices.synchrotron import Synchrotron
    from dodal.log import set_beamline as set_log_beamline
    from dodal.utils import get_beamline_name, skip_device

    BL = get_beamline_name("s41")  # Default used when not on a live beamline
    set_log_beamline(BL)  # Configure logging and util functions
    set_utils_beamline(BL)


    """
    Define device factory functions below this point.
    A device factory function is any function that has a return type which conforms 
    to one or more Bluesky Protocols.
    """


    """
    A valid factory function which is:
    - instantiated only on the live beamline
    - a maximum of once
    - can optionally be faked with ophyd simulated axes
    - can optionally be connected concurrently by not waiting for connect to complete
    - if constructor took a prefix, could optionally exclude the BLIXX prefix
    """"
    @skip_device(lambda: BL == "s41")  # Conditionally do not instantiate this device
    def synchrotron(
        wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
    ) -> Synchrotron:
        """Calls the Synchrotron class's constructor with name="synchrotron", prefix=""
        If this is called when already instantiated, it will return the existing object.
        """
        return device_instantiation(
            Synchrotron,
            "synchrotron",
            "",
            wait_for_connection,
            fake_with_ophyd_sim,
            bl_prefix=False,
        )

    def d11(name: str = "D11") -> AdAravisDetector:
        """
        Also a valid Device factory function, but as multiple calls would instantiate
        multiple copies of a device, discouraged.
        """
        return AdAravisDetector(name=name, prefix=f"{BL}-DI-DCAM-01:")

``w41`` should also be added to the list of ``ALL_BEAMLINES`` in ``tests/beamlines/test_device_instantiation``.
This test checks that the function returns a type that conforms to Bluesky protocols, 
that it always returns the same instance of the device and that the arguments passed 
into the Device class constructor are valid.

