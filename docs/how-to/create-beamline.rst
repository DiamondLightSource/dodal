Creating a new beamline
=======================

A beamline is a collection of devices that can be used together to run experiments, they may be read-only or capable of being set.
They include motors and detectors in the experiment hutch, optical components in the optics hutch, the synchrotron "machine" and more.

Beamline Modules
----------------

Each beamline should have its own file in the ``dodal.beamlines`` folder, in which the particular devices for the 
beamline are instantiated. The file should be named after the colloquial name for the beamline. For example:

* ``i03.py``
* ``i04_1.py``
* ``vmxi.py``

Beamline modules (in ``dodal.beamlines``) are code-as-configuration. They define the set of devices and common device
settings needed for a particular beamline or group of similar beamlines (e.g. a beamline and its digital twin). Some
of our tooling depends on the convention of *only* beamline modules going in this package. Common utilities should 
go somewhere else e.g. ``dodal.utils`` or ``dodal.beamlines.common``.

The following example creates a fictitious beamline ``w41``, with a simulated twin ``s41``.
``w41`` needs to monitor the status of the Synchrotron and drives an Aravis AreaDetector through a PandA.
``s41`` has a simulated clone of the AravisDetector, but does not have access to read the Synchrotron machine, and cannot simulate the hardware behaviours of a PandA.

.. code-block:: python
    from ophyd_async.epics.adaravis import AravisDetector
    from ophyd_async.fastcs.panda import HDFPanda

    from dodal.common.beamlines.beamline_utils import (
        device_factory,
        device_instantiation,
        get_path_provider,
    )
    from dodal.common.beamlines.beamline_utils import set_beamline as set_utils_beamline
    from dodal.devices.synchrotron import Synchrotron
    from dodal.log import set_beamline as set_log_beamline
    from dodal.utils import BeamlinePrefix, get_beamline_name, skip_device

    BL = get_beamline_name("s41")  # Default used when not on a live beamline
    PREFIX = BeamlinePrefix(BL)  # Useful for passing into device functions
    set_log_beamline(BL)  # Configure logging and util functions
    set_utils_beamline(BL)


    """
    Define device factory functions below this point.
    A device factory function is any function that has a return type which conforms to one
    or more Bluesky Protocols.
    """


    # Only compatible with ophyd_async devices
    @device_factory(mock=BL == "s41")  # When connect is called default to a mock backend
    def synchrotron() -> Synchrotron:
        """
        A valid factory function which:
        - always returns a singleton instance of the device
        - optionally (re)connects when called
        - may be reconnected concurrently with other devices
        - optionally when first connecting may connect to mocked signal backends
        - optionally may be named or renamed when called, setting the name after connecting
        and propagating the name to all child devices
        - optionally may be skipped when make_all_devices(this_beamline) called
        """
        return Synchrotron()


    @skip_device(
        BL == "s41"
    )  # skip this device when calling make_all_devices(this_beamline)
    def panda1(
        wait_for_connection: bool = True, fake_with_ophyd_sim: bool = False
    ) -> HDFPanda:
        """
        A valid factory function which:
        - always returns a singleton instance of the device
        - optionally connects concurrently when multiple devices created simultaneously
        - optionally when connecting may connect to mocked signal backends
        - constructor must take prefix which may optionally exclude the BLIXX prefix
        - constructor must take name which is set when the device is constructed
        - optionally may be skipped when make_all_devices(this_beamline) called
        """
        return device_instantiation(
            HDFPanda,
            "panda1",
            "-EA-PANDA-01:",
            wait_for_connection,
            fake_with_ophyd_sim,
        )


    def d11(name: str = "D11") -> AravisDetector:
        """
        Also a valid Device factory function, but as multiple calls would instantiate and
        connect multiple copies of a device, discouraged.
        Incompatible with calls to make_all_devices(this_beamline)
        """
        return AravisDetector(
            name=name,
            prefix=f"{PREFIX.beamline_prefix}-DI-DCAM-01:",
            path_provider=get_path_provider(),
        )
