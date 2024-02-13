Getting Started
===============

The Purpose of Dodal
--------------------

``dodal`` provides set of ophyd_ devices and bluesky_ plans that are commonly useful across many beamlines at DLS.

If you have some code that you think would be useful to be added please do so!


Creating a new beamline
-----------------------

A beamline is a collection of devices that can be used together to run experiments, they may be read-only or capable of being set.
They include motors in the experiment hutch, optical components in the optics hutch, the synchrotron "machine" and more.

The following example creates a fictitious beamline `w41`, with a simulated twin `s41`. 
`w41` wishes to monitor the status of the Synchrotron and has a AdAravisDetector
`s41` has a simulated clone of the AdAravisDetector, but not of the Synchrotron machine

```python
from dodal.beamlines.beamline_utils import device_instantiation
from dodal.beamlines.beamline_utils import set_beamline as set_utils_beamline
from dodal.devices.areadetector.adaravis import AdAravisDetector
from dodal.devices.synchrotron import Synchrotron
from dodal.log import set_beamline as set_log_beamline
from dodal.utils import get_beamline_name, skip_device

BL = get_beamline_name("s41")  # Default used when not on a live beamline
set_log_beamline(BL)  # Configure logging and util functions
set_utils_beamline(BL)


"""
Define device factory functions below this point.
A device factory function is any function that has a return type of a Device
A Device must conform to one or more Ophyd Protocols, e.g. Readable.
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

# Also a valid device factory function
def d11(name: str = "D11") -> AdAravisDetector:
    return AdAravisDetector(name=name, prefix=f"{BL}-DI-DCAM-01:")

```

Using Devices
-------------

``dodal`` contains devices to cover anything you would like to do using a beamline's hardware.

To use these devices you can do the following::

    from dodal.beamlines import i03
    dcm = i03.dcm()
    # You can now use the DCM as you would any other device in Bluesky plans

If you are on a beamline workstation this will give you immediate access to the real hardware. If you are not on a 
beamline workstation it will default to connecting to a simulated instrument.

Adding Logging
--------------

``dodal`` provides some helper functions to help you log what's going on.

You can set these up using::
    
    from dodal.beamlines import i03
    from dodal.log import set_up_logging_handlers, LOGGER

    set_up_logging_handlers()
    
Some logging will now occur when you are using devices/plans, you can increase the amount of logs by 
instead using ``set_up_logging_handlers("DEBUG")``. You can also log more explicitly using::

    LOGGER.info("I am a log message")


If you are on a beamline workstation this will save any logs to ``dls_sw/BEAMLINE/logs/bluesky/`` and will
push them to graylog_. If you are not on a beamline workstation logs will be saved next to your working directory
and pushed to a local graylog instance.

If you would like to only log to graylog/file exlusively there are helper functions in ``dodal.log`` that you can use. 


.. _ophyd: https://nsls-ii.github.io/ophyd/
.. _bluesky: https://blueskyproject.io/bluesky/
.. _graylog: https://graylog2.diamond.ac.uk/search