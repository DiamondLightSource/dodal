Zocalo Interaction
==================

.. image:: ../../assets/zocalo.png
  :alt: Diagram of zocalo

Zocalo jobs are triggered based on their ISPyB DCID using the ``ZocaloTrigger`` class in a callback subscribed to the 
Bluesky plan or ``RunEngine``. These can trigger processing for any kind of job, as zocalo infers the necessary 
processing from data in ISPyB.

Results are received using the ``ZocaloResults`` device, so that they can be read into a plan and used for 
decision-making. Currently the ``ZocaloResults`` device is only made to handle X-ray centring results. It subscribes to 
a given zocalo RabbitMQ channel the first time that it is triggered.