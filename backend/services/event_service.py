from datetime import datetime, timezone

from sqlalchemy import func

from database.db import db
from models.category import Category
from models.event import Event
from models.user import User
from services.errors import ApiError


def _parse_iso_datetime(value):
    try:
        # Accept RFC3339-ish strings, e.g. "2026-03-15T18:30:00+05:30"
        if isinstance(value, str) and value.endswith("Z"):
            value = value[:-1] + "+00:00"
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except Exception:
        raise ApiError("Invalid date format. Use ISO 8601.", status_code=400, details={"field": "date"})


def list_events(q=None, category=None):
    query = Event.query
    if q:
        query = query.filter(func.lower(Event.title).like(f"%{q.strip().lower()}%"))
    if category:
        query = query.join(Category).filter(func.lower(Category.name) == category.strip().lower())
    return query.order_by(Event.event_date.asc()).all()


def get_event_or_404(event_id):
    event = Event.query.get(event_id)
    if not event:
        raise ApiError("Event not found", status_code=404, error="not_found")
    return event


def create_event(db, organizer_user, payload):
    if organizer_user.role not in ("ORGANIZER", "ADMIN"):
        raise ApiError("Only organizers can create events", status_code=403, error="forbidden")

    title = (payload.get("title") or "").strip()
    if not title:
        raise ApiError("Title is required", status_code=400, details={"field": "title"})

    date_str = payload.get("date")
    if not date_str:
        raise ApiError("Date is required", status_code=400, details={"field": "date"})
    event_date = _parse_iso_datetime(date_str)

    venue = (payload.get("venue") or payload.get("location") or "").strip()
    if not venue:
        raise ApiError("Venue is required", status_code=400, details={"field": "venue"})

    max_capacity = payload.get("max_capacity")
    try:
        max_capacity = int(max_capacity)
    except Exception:
        raise ApiError("max_capacity must be an integer", status_code=400, details={"field": "max_capacity"})
    if max_capacity <= 0:
        raise ApiError("max_capacity must be > 0", status_code=400, details={"field": "max_capacity"})

    category_name = (payload.get("category") or "").strip()
    category_id = payload.get("category_id")
    category = None
    if category_id:
        category = Category.query.get(int(category_id))
    elif category_name:
        category = Category.query.filter(func.lower(Category.name) == category_name.lower()).first()
        if not category:
            category = Category(name=category_name)
            db.session.add(category)
            db.session.flush()

    event = Event(
        title=title,
        description=payload.get("description"),
        category_id=category.category_id if category else None,
        event_date=event_date,
        location=venue,
        max_capacity=max_capacity,
        organizer_id=organizer_user.user_id,
        image_url=payload.get("image_url"),
    )
    db.session.add(event)
    db.session.commit()
    return event


def update_event(db, event, actor_user, payload):
    if actor_user.role != "ADMIN" and event.organizer_id != actor_user.user_id:
        raise ApiError("You can only update your own events", status_code=403, error="forbidden")

    if "title" in payload:
        title = (payload.get("title") or "").strip()
        if not title:
            raise ApiError("Title cannot be empty", status_code=400, details={"field": "title"})
        event.title = title
    if "description" in payload:
        event.description = payload.get("description")
    if "category" in payload or "category_id" in payload:
        category_name = (payload.get("category") or "").strip()
        category_id = payload.get("category_id")
        category = None
        if category_id:
            category = Category.query.get(int(category_id))
        elif category_name:
            category = Category.query.filter(func.lower(Category.name) == category_name.lower()).first()
            if not category:
                category = Category(name=category_name)
                db.session.add(category)
                db.session.flush()
        event.category_id = category.category_id if category else None
    if "date" in payload:
        event.event_date = _parse_iso_datetime(payload.get("date"))
    if "venue" in payload or "location" in payload:
        venue = (payload.get("venue") or payload.get("location") or "").strip()
        if not venue:
            raise ApiError("Venue cannot be empty", status_code=400, details={"field": "venue"})
        event.location = venue
    if "max_capacity" in payload:
        try:
            new_capacity = int(payload.get("max_capacity"))
        except Exception:
            raise ApiError("max_capacity must be an integer", status_code=400, details={"field": "max_capacity"})
        if new_capacity <= 0:
            raise ApiError("max_capacity must be > 0", status_code=400, details={"field": "max_capacity"})
        # Don't allow shrinking below active bookings.
        from models.booking import Booking

        active = (
            Booking.query.filter_by(event_id=event.event_id, status="ACTIVE")
            .with_entities(func.count(Booking.booking_id))
            .scalar()
        )
        if active and new_capacity < int(active):
            raise ApiError(
                "max_capacity cannot be less than current active bookings",
                status_code=409,
                error="conflict",
                details={"active_bookings": int(active)},
            )
        event.max_capacity = new_capacity
    if "image_url" in payload:
        event.image_url = payload.get("image_url")

    db.session.commit()
    return event


def delete_event(db, event, actor_user):
    if actor_user.role != "ADMIN" and event.organizer_id != actor_user.user_id:
        raise ApiError("You can only delete your own events", status_code=403, error="forbidden")
    db.session.delete(event)
    db.session.commit()


def organizer_events(organizer_id):
    return Event.query.filter_by(organizer_id=organizer_id).order_by(Event.event_date.asc()).all()


def event_attendees(event):
    """
    Return a list of attendees for an event.
    Only ACTIVE bookings are considered.
    """
    from models.booking import Booking

    rows = (
        db.session.query(User, Booking)
        .join(Booking, Booking.user_id == User.user_id)
        .filter(Booking.event_id == event.event_id, Booking.status == "ACTIVE")
        .order_by(Booking.booking_date.asc())
        .all()
    )
    attendees = []
    for user, booking in rows:
        attendees.append(
            {
                "user": user.to_public_dict(),
                "booking": booking.to_dict(include_event=False),
            }
        )
    return attendees
