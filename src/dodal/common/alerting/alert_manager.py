import uuid

import requests
from requests.auth import HTTPBasicAuth

from dodal.common.alerting import AlertService
from dodal.log import LOGGER


class AlertManagerAlertService(AlertService):
    """
    Raises an alert by calling the Alert Manager API.
    """

    def __init__(self, username: str, password: str, helmchart_url: str):
        self._username = username
        self._password = password
        self._endpoint = f"{helmchart_url}/api/v2"

    def raise_alert(self, summary: str, content: str):
        """
        Raise an alertmanager alert
        Args:
            summary: This will be used as the alert_summary annotation in the alert
            content: This will be used as the alert_content annotation in the alert
        """
        # start = datetime.now()
        # now = start.isoformat(timespec="milliseconds")
        # expiry = (start + timedelta(hours=24)).isoformat(timespec="milliseconds")
        id = str(uuid.uuid4())
        payload = [
            {
                "annotations": {"alert_summary": summary, "alert_content": content},
                "labels": {
                    "alertname": "email-beamline-staff",
                    "alert_id": id,
                },
                "generatorURL": self._generatorUrl(),
            }
        ]
        LOGGER.info(f"Raised alert id {id}")
        with self._session() as session:
            response = session.post(f"{self._endpoint}/alerts", json=payload)
            response.raise_for_status()

    def get_alerts(self):
        with self._session() as session:
            response = session.get(f"{self._endpoint}/alerts")
            response.raise_for_status()
            print(response.content)

    def _session(self) -> requests.Session:
        session = requests.Session()
        session.auth = HTTPBasicAuth(self._username, self._password)
        session.headers["Accept"] = "application/json"
        return session

    def _generatorUrl(self):
        """TODO Obtain the generator url"""
        return "http://172.23.169.36:9093/#/alerts"
