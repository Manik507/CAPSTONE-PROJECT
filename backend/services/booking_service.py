from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from models.booking import Booking, Ticket
from models.event import Event
from services.errors import ApiError


def _active_booking_count(event_id):
    return (
        Booking.query.filter_by(event_id=event_id, status="ACTIVE")
        .with_entities(func.count(Booking.booking_id))
        .scalar()
    )


def create_booking(db, user, event_id):
    """
    Create a booking and ticket for the user for a given event.

    Capacity enforcement:
      - Lock the event row while checking capacity to reduce race conditions.
      - Re-check active bookings within the same transaction.
    """
    if user.role not in ("ATTENDEE", "ADMIN"):
        raise ApiError("Only attendees can book events", status_code=403, error="forbidden")

    event = Event.query.filter_by(event_id=event_id).with_for_update().first()
    if not event:
        raise ApiError("Event not found", status_code=404, error="not_found")

    # Disallow duplicate active bookings.
    existing = Booking.query.filter_by(user_id=user.user_id, event_id=event.event_id, status="ACTIVE").first()
    if existing:
        raise ApiError("You already have an active booking for this event", status_code=409, error="conflict")

    active_count = _active_booking_count(event.event_id)
    if active_count >= event.max_capacity:
        raise ApiError("Event is fully booked", status_code=409, error="conflict")

    booking = Booking(user_id=user.user_id, event_id=event.event_id)
    db.session.add(booking)
    db.session.flush()

    ticket = Ticket(
        user_id=user.user_id,
        event_id=event.event_id,
        booking_id=booking.booking_id,
        booking_time=booking.booking_date,
    )
    db.session.add(ticket)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ApiError("Duplicate booking", status_code=409, error="conflict")

    return booking, ticket


def list_user_bookings(user_id):
    return (
        Booking.query.filter_by(user_id=user_id)
        .order_by(Booking.booking_date.desc())
        .all()
    )


def cancel_booking(db, booking_id, actor_user):
    booking = Booking.query.get(booking_id)
    if not booking:
        raise ApiError("Booking not found", status_code=404, error="not_found")

    if actor_user.role != "ADMIN" and booking.user_id != actor_user.user_id:
        raise ApiError("You can only cancel your own bookings", status_code=403, error="forbidden")

    if booking.status == "CANCELLED":
        return booking

    booking.status = "CANCELLED"
    db.session.commit()
    return booking
