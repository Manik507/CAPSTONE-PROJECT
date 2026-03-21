"""
Import models so SQLAlchemy knows about them before create_all().
"""

from models.user import User  # noqa: F401
from models.event import Event  # noqa: F401
from models.booking import Booking, Ticket  # noqa: F401
from models.category import Category  # noqa: F401
from models.notification import Notification  # noqa: F401
