# Glossary

This is a glossary of abbreviations, acronyms and terms used throughout this project.

## Abbreviations

| Abbreviation | Full Term |
| ----------- | -----------|
| repo | repository |
| async | asynchronous |

## Acronyms

| Acronym | Full Term |
| ----------- | -----------|
| CI | Continuous Integration |
| CD | Continuous Deployment |
| DLS | Diamond Light Source |
| dodal | Diamond Ophyd Device Abstraction Layer |
| EPICS | Experimental Physics and Industrial Control System |
| GDA | Generic Data Acquisition |
| IDE | Integrated Development Environment |
| IO | Input / Output |
| PR | Pull Request |
| PV | Process Variable |

## Terms

| Term | Definition |
| ----------- | -----------|
| blueapi | Lightweight bluesky-as-a-service wrapper application. Also usable as a library. |
| bluesky | Bluesky is a library for experiment control and collection of scientific data and metadata. |
| beamline | A beamline is a collection of all devices used to run experiments. A beamline's devices include all components from an insertion device which produces synchrotron light (beam) to detectors which collect experimental data, which may be read-only or capable of being set. |
| beamline workstation | A linux workstation which is present on the beamline-local network. |
| device | Hardware defined via ophyd protocols, although ophyd-async is the standard implementation at Diamond. |
| endstation | An endstation is a collection of devices which can be used together to run experiments, usually distinct from optical devices on a beamline. Beamlines may have one or more endstations which can be used for data collection either in parallel or exclusively. |
| graylog | A log management platform, which all container stdout/stderr logs are sent to at DLS. | 
| ISPyB | A managed experimental information service for keeping track of your experiments at some Diamond beamlines. |
| the machine | The synchrotron. |
| ophyd | Ophyd is a Python library for interfacing with hardware. |
| ophyd-async | Ophyd-async is a Python library for asynchronously interfacing with hardware. |
| plan | Bluesky’s concept of an experimental procedure. |
| plan stub | An instruction or ingredient which can be used to to write a bluesky plan. |
| run_engine | The executor of bluesky plans. |
| signal | Anything in a device that is expected to be set externally e.g. by a plan should be a signal, even if it does not connect to EPICS. |
| sphinx | A documentation generator. |
| training-rig | A prototyped beamline, with a small number of devices. |
| zocalo | An automated data processing system used at some Diamond beamlines. |
