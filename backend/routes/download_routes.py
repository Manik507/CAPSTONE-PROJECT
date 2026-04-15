"""
Download / Export Module

Provides CSV download endpoints for event data:
- All participants
- Round-wise participants
- Winners
- Full event report (all-in-one)

Access: INSTITUTE (own events), VOLUNTEER (assigned events), ADMIN (all events)
"""
import csv
import io

from flask import Blueprint, Response, jsonify
from flask_jwt_extended import jwt_required

from database.db import db
from models.event import Event
from models.event_result import EventResult
from models.institute import Institute
from models.participant import Participant
from models.round_lock import RoundLock
from services.errors import ApiError
from utils.decorators import role_required
from utils.jwt_handler import current_user_id


download_bp = Blueprint("download", __name__, url_prefix="/download")


def _make_csv_response(rows, headers, filename):
    """Build a CSV file response from rows and headers."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


def _check_event_access(event, uid):
    """Verify the requesting user is authorized to download this event's data."""
    from models.user import User
    from models.volunteer import Volunteer

    user = User.query.get(uid)
    if user.role == "ADMIN":
        return
    if user.role == "INSTITUTE":
        institute = Institute.query.filter_by(user_id=uid).first()
        if not institute or event.institute_id != institute.id:
            raise ApiError("Not authorized to download this event's data", status_code=403)
    elif user.role == "VOLUNTEER":
        v = Volunteer.query.filter_by(user_id=uid, event_id=event.id).first()
        if not v:
            raise ApiError("Not authorized for this event", status_code=403)
    else:
        raise ApiError("Not authorized", status_code=403)


@download_bp.get("/event/<int:event_id>/participants")
@jwt_required()
@role_required("INSTITUTE", "ADMIN", "VOLUNTEER")
def download_participants(event_id):
    """Download all participants as CSV."""
    uid = int(current_user_id())
    event = Event.query.get(event_id)
    if not event:
        raise ApiError("Event not found", status_code=404)
    _check_event_access(event, uid)

    participants = Participant.query.filter_by(event_id=event_id).order_by(Participant.created_at.asc()).all()

    headers = [
        "Reg ID", "Name", "Username", "Email", "Phone",
        "Payment Type", "Payment Status", "Transaction ID",
        "Qualified Round", "Registered At"
    ]
    rows = []
    for p in participants:
        rows.append([
            p.registration_id or "",
            p.user.full_name if p.user else "",
            p.user.username if p.user else "",
            p.user.email if p.user else "",
            p.user.phone_number if p.user else "",
            p.payment_type,
            p.payment_status,
            p.transaction_id or "",
            p.qualified_round,
            p.created_at.isoformat() if p.created_at else "",
        ])

    return _make_csv_response(rows, headers, f"event_{event_id}_participants.csv")


@download_bp.get("/event/<int:event_id>/round/<int:round_number>")
@jwt_required()
@role_required("INSTITUTE", "ADMIN", "VOLUNTEER")
def download_round(event_id, round_number):
    """Download participants for a specific round as CSV."""
    uid = int(current_user_id())
    event = Event.query.get(event_id)
    if not event:
        raise ApiError("Event not found", status_code=404)
    _check_event_access(event, uid)

    if round_number < 1 or round_number > event.num_rounds:
        raise ApiError(f"Round must be between 1 and {event.num_rounds}", status_code=400)

    if round_number == 1:
        participants = Participant.query.filter_by(
            event_id=event_id, payment_status="PAID"
        ).all()
    else:
        participants = Participant.query.filter_by(
            event_id=event_id, payment_status="PAID"
        ).filter(Participant.qualified_round >= round_number).all()

    headers = ["Reg ID", "Name", "Username", "Email", "Phone", "Qualified Round"]
    rows = []
    for p in participants:
        rows.append([
            p.registration_id or "",
            p.user.full_name if p.user else "",
            p.user.username if p.user else "",
            p.user.email if p.user else "",
            p.user.phone_number if p.user else "",
            p.qualified_round,
        ])

    return _make_csv_response(rows, headers, f"event_{event_id}_round_{round_number}.csv")


@download_bp.get("/event/<int:event_id>/winners")
@jwt_required()
@role_required("INSTITUTE", "ADMIN", "VOLUNTEER")
def download_winners(event_id):
    """Download event winners/results as CSV."""
    uid = int(current_user_id())
    event = Event.query.get(event_id)
    if not event:
        raise ApiError("Event not found", status_code=404)
    _check_event_access(event, uid)

    results = EventResult.query.filter_by(event_id=event_id).order_by(EventResult.rank.asc()).all()

    headers = ["Rank", "Name", "Email", "Prize", "Description"]
    rows = []
    for r in results:
        rows.append([
            r.rank,
            r.user.full_name if r.user else "",
            r.user.email if r.user else "",
            r.prize_name,
            r.prize_description or "",
        ])

    return _make_csv_response(rows, headers, f"event_{event_id}_winners.csv")


@download_bp.get("/event/<int:event_id>/full")
@jwt_required()
@role_required("INSTITUTE", "ADMIN")
def download_full_report(event_id):
    """Download comprehensive event report (all sections) as CSV."""
    uid = int(current_user_id())
    event = Event.query.get(event_id)
    if not event:
        raise ApiError("Event not found", status_code=404)
    _check_event_access(event, uid)

    output = io.StringIO()
    writer = csv.writer(output)

    # --- Section 1: Event Details ---
    writer.writerow(["=== EVENT DETAILS ==="])
    writer.writerow(["Title", event.title])
    writer.writerow(["Description", event.description or ""])
    writer.writerow(["Location", event.location])
    writer.writerow(["Start Date", event.date.isoformat() if event.date else ""])
    writer.writerow(["End Date", event.end_date.isoformat() if event.end_date else ""])
    writer.writerow(["Rounds", event.num_rounds])
    writer.writerow(["Fees", event.fees])
    writer.writerow(["Institute", event.institute.name if event.institute else ""])
    writer.writerow(["Results Locked", event.results_locked])
    writer.writerow([])

    # --- Section 2: All Participants ---
    writer.writerow(["=== ALL PARTICIPANTS ==="])
    writer.writerow([
        "Reg ID", "Name", "Username", "Email", "Phone",
        "Payment Type", "Payment Status", "Transaction ID", "Qualified Round"
    ])

    participants = Participant.query.filter_by(event_id=event_id).order_by(Participant.created_at.asc()).all()
    for p in participants:
        writer.writerow([
            p.registration_id or "",
            p.user.full_name if p.user else "",
            p.user.username if p.user else "",
            p.user.email if p.user else "",
            p.user.phone_number if p.user else "",
            p.payment_type,
            p.payment_status,
            p.transaction_id or "",
            p.qualified_round,
        ])
    writer.writerow([])

    # --- Section 3: Round-wise Breakdown ---
    writer.writerow(["=== ROUND-WISE QUALIFIERS ==="])
    for r in range(1, event.num_rounds + 1):
        if r == 1:
            rp = Participant.query.filter_by(event_id=event_id, payment_status="PAID").all()
        else:
            rp = Participant.query.filter_by(
                event_id=event_id, payment_status="PAID"
            ).filter(Participant.qualified_round >= r).all()

        lock = RoundLock.query.filter_by(event_id=event_id, round_number=r).first()
        writer.writerow([
            f"--- Round {r} ---",
            f"Participants: {len(rp)}",
            f"Locked: {'Yes' if lock else 'No'}"
        ])
        for p in rp:
            writer.writerow([
                "",
                p.user.full_name if p.user else "",
                p.user.email if p.user else "",
                p.registration_id or ""
            ])
    writer.writerow([])

    # --- Section 4: Winners ---
    writer.writerow(["=== WINNERS ==="])
    results = EventResult.query.filter_by(event_id=event_id).order_by(EventResult.rank.asc()).all()
    if results:
        writer.writerow(["Rank", "Name", "Email", "Prize", "Description"])
        for res in results:
            writer.writerow([
                res.rank,
                res.user.full_name if res.user else "",
                res.user.email if res.user else "",
                res.prize_name,
                res.prize_description or "",
            ])
    else:
        writer.writerow(["No winners declared yet"])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=event_{event_id}_full_report.csv"}
    )
