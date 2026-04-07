from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
jwt = JWTManager()
bcrypt = Bcrypt()

def init_extensions(app):
    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
