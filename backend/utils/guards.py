"""
Shared guard functions for enforcing business rules across routes.
"""
from datetime import datetime, timezone

from services.errors import ApiError


def check_event_not_completed(event):
    """
    Raise ApiError if the event's end_date has passed.
    Used to enforce read-only mode on completed events.
    """
    now = datetime.now(timezone.utc)
    end_date = event.end_date
    if end_date:
        # Ensure timezone-aware comparison
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        if end_date < now:
            raise ApiError(
                "This event has already completed. No modifications allowed.",
                status_code=403
            )
