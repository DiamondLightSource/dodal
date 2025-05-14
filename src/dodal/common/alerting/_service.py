from typing import Protocol

from dodal.common.alerting.log_based_service import LoggingAlertService

_alert_service = LoggingAlertService()


class AlertService(Protocol):
    """
    Implemented by any backend that provides the ability to dispatch alerts to some
    service that is capable of disseminating them via any of a variety of media such
    as email, SMS, instant messaging, etc etc.
    """
    def raise_alert(self,
                    summary: str,
                    content: str):
        """
        Raise an alert that will be forwarded to beamline support staff, which might
        for example be used as the basis for an incident in an incident reporting system.
        Args:
            summary: One line summary of the alert, that might for instance be used
                in an email subject line.
            content: Plain text content detailing the nature of the incident.
        """
        pass


def get_alerting_service() -> AlertService:
    """Get the alert service for this instance."""
    return _alert_service


def set_alerting_service(service: AlertService):
    """Set the alert service for this instance, call when the beamline is initialised."""
    global _alert_service
    _alert_service = service
