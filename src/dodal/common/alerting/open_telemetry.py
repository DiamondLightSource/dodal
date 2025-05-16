from dodal.common.alerting import AlertService


class OpenTelemetryAlertService(AlertService):
    """
    An alert service that raises alerts by generating an Open Telemetry call that
    is logged to a backend which dispatches the alert
    """

    pass
