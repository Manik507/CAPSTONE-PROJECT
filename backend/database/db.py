import os

from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager

# SQLAlchemy's optional C extensions trigger a Windows WMI lookup on some
# Python 3.14 installs, which can hang during import. Use the pure-Python path.
os.environ.setdefault("DISABLE_SQLALCHEMY_CEXT_RUNTIME", "1")

from flask_sqlalchemy import SQLAlchemy


# Extensions are created once and initialized in the app factory.
db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()


def init_extensions(app):
    """Initialize Flask extensions."""
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
