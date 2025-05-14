"""
Contains functionality for notifying beamline staff of events needing their attention
"""
from dodal.common.alerting._service import AlertService, get_alerting_service, set_alerting_service

__all__ = ["AlertService", "get_alerting_service", "set_alerting_service"]
