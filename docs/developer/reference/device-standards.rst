Ophyd vs Ophyd-async
====================
Some devices have been written in ``ophyd`` for historic reasons. However, all new devices should be written in 
``ophyd-async`` and if old ``ophyd`` devices are undergoing a large re-write they should also be considered for 
conversion to ``ophyd-async``. 

Where to put devices
====================

Dodal is written with the philosophy that Ophyd devices should be assumed to be as generic as possible. I.e. you 
should think about where to place them in the following order:

#. A device that could be used at any facility, e.g. a generic ``EpicsMotor`` or a commercial product with a 
   standard IOC, should go in https://github.com/bluesky/ophyd-epics-devices
#. A device that may be on any beamline should go in the top level of the ``devices`` folder. If it is a quite 
   complex device (e.g. multiple files) it should have a folder of it's own i.e. ``oav``
#. A device that is very specific to a particular beamline should go in the ``devices/ixx`` folder

This is in an effort to avoid duplication across facilities/beamlines. 

PV Suffixes
===========

In general devices should contain only the PV suffixes that are generic for any instance of the device e.g.

.. code-block:: python

    class MyDevice(Device):
        bragg: EpicsMotor = Cpt(EpicsMotor, "BRAGG")
    
    device_instantiation(DCM, "dcm", "-MO-DCM-01:")


is preferred over

.. code-block:: python

    class MyDevice(Device):
        bragg: EpicsMotor = Cpt(EpicsMotor, "-MO-DCM-01:BRAGG")

    device_instantiation(DCM, "dcm", "")

This is so that a new device on say ``-MO-DCM-02`` can be easily created.

Use of signals
==============

Anything in a device that is expected to be set externally e.g. by a plan should be a signal, even if it does not 
connect to EPICS. If it does not connect to EPICS it should be a soft signal. 

Whilst it would be possible to do:

.. code-block:: python

    class MyDevice(Device):
        def __init__(self):
             self.param = "blah"

    my_device = MyDevice()
    def my_plan():
        my_device.param = "new_value"

this has potential negative side effects:

* When the plan is simulated it will still set the parameter on the device
* There may be external things attached to the RE that are tracking messages e.g. metrics. A set like this would be
  lost

Instead you should make a sort signal:

.. code-block:: python
    
    class MyDevice(Device):
        def __init__(self):
             self.param = create_soft_signal(str, "", self.name)
    
    my_device = MyDevice()
    def my_plan():
        yield from bps.mv(my_device.param, "new_value")

Ophyd Devices best practices
============================

Ophyd-async directory contains a flowchart_ for a simplified decision tree about what interfaces
should a given device implement.

.. _flowchart: https://blueskyproject.io/ophyd-async/main/how-to/choose-interfaces-for-devices.html