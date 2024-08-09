Decision Flowchart for Creating a New ophyd_async Device
========================================================

This document contains decision flowcharts designed to guide developers through the process of creating a new device in the Dodal library. 
That is done using `ophyd-async`_ framework, the standard hardware abstraction library at Diamond. These flowcharts help in determining the appropriate class inheritance, methods to override, and testing procedures for optimal device functionality and integration into the system.

High-Level Development Flowchart
--------------------------------

The **objective** is to get it into main and then test it on the beamline! Ensuring fast iteration. You write the device, you assume you know how it works, you write tests against those assumptions, you merge. Then and only then do you test your assumptions on the beamline. If they were wrong, that's more issues.

See if you can find a similar device that someone has already made. If one seems to exist but has different PV names, those can and should be changed. Advise consulting with controls. If the device is urgently needed, two copies can coexist but there must be an issue to reconcile.

You might find the dodal CLI useful to verify the PV values.

There's some of this already but more general advice not to do this task alone. Consult before starting, seek feedback early (e.g. draft PR) and merge with other people's devices where possible. The test suite should provide the confidence to do so without breaking anything.

.. mermaid::

  flowchart TD
    highLevelStart([Start]) --> createIssue[Create Issue for New Device]
    createIssue --> scoutUsers[Scout current and potential users of the device, tag them in the issue]
    scoutUsers --> checkExistingDevices[Check if a similar device exists]
    checkExistingDevices -- "Exists but with different PV names" --> adviseConsultControls[Advise consulting with controls to change PV names]
    adviseConsultControls --> testPVs[Test PVs to get the right values]
    checkExistingDevices -- "No similar device" --> testPVs
    testPVs --> decideStateEnums[Decide on State Enums: extend str, Enum]
    decideStateEnums --> chooseMethods[Choose which superclass methods to override]
    chooseMethods --> finalizeDevice[Finalize Device Implementation]
    finalizeDevice --> requestFeedback[Request feedback from tagged users]
    requestFeedback --> rebaseOnMain[Rebase on main -> make sure tests pass still]
    rebaseOnMain --> coordinateMerges[Coordinate merges with other codebase updates]
    coordinateMerges --> markPRReady[Mark PR as ready]
    adviseConsultControls -- "Urgent need for device" --> createIssueForReconciliation[Create an issue to reconcile two versions later]
    createIssueForReconciliation --> testPVs

Interface Selection Flowchart
-----------------------------

See the chart in `ophyd-async`_.

Testing Flowchart
-----------------

This flowchart outlines the testing procedure for the new ophyd_async device, from creating fixtures to testing state transitions and hardware integration.

.. mermaid::

  flowchart TD
    testStart([Start Testing]) --> checkExistingFixtures[Check for existing fixtures]
    checkExistingFixtures --> createFixtures[Create or update fixtures for various states of the device]
    createFixtures --> createMockReactions[Create mock reactions to signals]
    createMockReactions --> testStateTransitions[Test each device state transition]
    testStateTransitions --> testPVValues[Check PV values to ensure accuracy]
    testPVValues --> testAgainstHardware[Test against hardware]
    testAgainstHardware --> decision{Check if all tests pass}
    decision -- "Yes" --> testingComplete[Testing Complete]
    decision -- "No" --> modifyCode[Modify code and update tests]
    modifyCode --> createFixtures

Additional Notes
----------------

- ``with self.add_children_as_readables():`` Ensure this context manager is used appropriately in the device implementation to add child components as readable properties, but not Movables.


.. _ophyd-async: https://blueskyproject.io/ophyd-async/main/how-to/choose-interfaces-for-devices.html
