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
| [DLS](https://www.diamond.ac.uk/Home.html) | Diamond Light Source |
| dodal | Diamond Ophyd Device Abstraction Layer |
| [EPICS](https://epics-controls.org/) | A set of software tools and applications which provide a software infrastructure for use in building distributed control systems to operate devices such as Particle Accelerators, Large Experiments and major Telescopes ("Experimental Physics and Industrial Control System") |
| GDA | Java/RCP acquisition platform developed at Diamond ("Generic Data Acquisition") |
| ID | Insertion Device |
| IDE | Integrated Development Environment |
| IO | Input / Output |
| IOC | Input / Output Controller |
| PR | Pull Request |
| PV | Process Variable |

## Terms

| Term | Definition |
| ----------- | -----------|
| [blueapi](https://diamondlightsource.github.io/blueapi/main/index.html) | Lightweight bluesky-as-a-service wrapper application. Also usable as a library. |
| [bluesky](https://blueskyproject.io/bluesky/main/index.html) | Bluesky is a library for experiment control and collection of scientific data and metadata. |
| beamline | A beamline is a collection of all devices used to run experiments. A beamline's devices include all components from an insertion device which produces synchrotron light (beam) to detectors which collect experimental data, which may be read-only or capable of being set. |
| beamline workstation | A linux workstation which is present on the beamline-local network. |
| device | Hardware defined via [ophyd protocols](https://blueskyproject.io/ophyd/index.html), although [ophyd-async](https://blueskyproject.io/ophyd-async/main/index.html) is the standard implementation at Diamond. |
| endstation | An endstation is a collection of devices which can be used together to run experiments, usually distinct from optical devices on a beamline. Beamlines may have one or more endstations which can be used for data collection either in parallel or exclusively. |
| [graylog](https://graylog.diamond.ac.uk/) | A log management platform, which all container stdout/stderr logs are sent to at DLS. | 
| [ISPyB](https://ispyb.diamond.ac.uk/) | A managed experimental information service for keeping track of your experiments at some Diamond beamlines. The front end for this is called synchweb. |
| the machine | The synchrotron. |
| [ophyd](https://blueskyproject.io/ophyd/) | Ophyd is a Python library for interfacing with hardware. Ophyd is the older style of writing devices that is in use at NSLS-II, all new DLS devices should be ophyd-async. |
| [ophyd-async](https://blueskyproject.io/ophyd-async/main/index.html) | Ophyd-async is a Python library for asynchronously interfacing with hardware. All DLS devices will be written in ophyd-async, though it is common for people to refer to devices as ophyd devices as a shorthand even if they are actually written in ophyd-async. |
| [plan](https://blueskyproject.io/bluesky/main/plans.html) | Bluesky’s concept of an experimental procedure. |
| [plan stub](https://blueskyproject.io/bluesky/main/plans.html#stub-plans) | An instruction or ingredient which can be used to to write a bluesky plan. |
| [run_engine](https://blueskyproject.io/bluesky/main/tutorial.html#the-runengine) | The executor of bluesky plans. |
| signal | Anything in a device that is expected to be set or read externally (e.g. by a plan) should be a signal, even if it does not connect to EPICS. |
| [sphinx](https://www.sphinx-doc.org/en/master/index.html) | A documentation generator. |
| training-rig | A prototyped beamline, with a small number of devices. |
| [zocalo](https://zocalo.readthedocs.io/en/latest/) | An automated data processing system used at some Diamond beamlines. |
