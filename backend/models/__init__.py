"""
Import models so SQLAlchemy knows about them before create_all().
"""

from models.user import User  # noqa: F401
from models.institute import Institute  # noqa: F401
from models.event import Event  # noqa: F401
from models.participant import Participant  # noqa: F401

from models.leaderboard import Leaderboard  # noqa: F401
from models.booking import Booking, Ticket  # noqa: F401
from models.notification import Notification  # noqa: F401
from models.event_update import EventUpdate  # noqa: F401
from models.event_result import EventResult  # noqa: F401
from models.reward_history import RewardHistory  # noqa: F401
from models.follow import Follow  # noqa: F401
from models.activity_log import ActivityLog  # noqa: F401
from models.volunteer import Volunteer  # noqa: F401
