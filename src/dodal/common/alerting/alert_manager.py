import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import requests
from requests.auth import HTTPBasicAuth

from dodal.common.alerting import AlertService, Metadata
from dodal.log import LOGGER


class AlertManagerAlertService(AlertService):
    """
    Raises an alert by calling the Alert Manager API.
    """

    def __init__(
        self,
        alertmanager_url: str,
        graylog_stream: str = "66264f5519ccca6d1c9e4e03",
        username: str = None,
        password: str = None,
    ):
        self._username = username
        self._password = password
        self._graylog_stream = graylog_stream
        self._endpoint = f"{alertmanager_url}/api/v2"

    def raise_alert(self, summary: str, content: str, metadata: dict[str, str]):
        """
        Raise an alertmanager alert
        Args:
            summary: This will be used as the alert_summary annotation in the alert
            content: This will be used as the alert_content annotation in the alert
            metadata: This will be included as additional labels in the alert
        """
        # start = datetime.now()
        # now = start.isoformat(timespec="milliseconds")
        # expiry = (start + timedelta(hours=24)).isoformat(timespec="milliseconds")
        id = str(uuid.uuid4())
        payload = [
            {
                "annotations": {
                    "alert_summary": summary,
                    "alert_content": content,
                },
                "labels": {
                    "alertname": "email-beamline-staff",
                    "alert_id": id,
                }
                | metadata,
                "generatorURL": self._generator_url(),
            }
        ]
        if sample_id := metadata.get(Metadata.SAMPLE_ID):
            payload[0]["annotations"]["ispyb_url"] = self._ispybUrl(sample_id)

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
        if self._username:
            session.auth = HTTPBasicAuth(self._username, self._password)
        session.headers["Accept"] = "application/json"
        return session

    def _ispybUrl(self, sample_id: str):
        return f"https://ispyb.diamond.ac.uk/samples/sid/{quote(sample_id)}"

    def _generator_url(self):
        to_time = datetime.now(timezone.utc)
        from_time = to_time - timedelta(minutes=15)
        return (
            f"https://graylog.diamond.ac.uk/streams/{quote(self._graylog_stream)}/search?q=&rangetype=absolute&"
            f"from={quote(from_time.isoformat(timespec='milliseconds'))}&to="
            f"{quote(to_time.isoformat(timespec='milliseconds'))}"
        )
