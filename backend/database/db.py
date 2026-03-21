from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
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

