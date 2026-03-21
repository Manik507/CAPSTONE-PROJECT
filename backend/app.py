from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from database.db import jwt
from database.db import init_extensions
from services.errors import ApiError


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Make config accessible without importing config everywhere.
    app.config["ALLOW_ADMIN_REGISTRATION"] = Config.ALLOW_ADMIN_REGISTRATION

    # Extensions
    init_extensions(app)

    # CORS (configure allowed origins via CORS_ORIGINS env var)
    cors_origins = app.config.get("CORS_ORIGINS", "*")
    CORS(app, resources={r"/*": {"origins": cors_origins}})

    # Register routes (Blueprints)
    from routes.auth_routes import auth_bp
    from routes.booking_routes import bookings_bp
    from routes.category_routes import categories_bp
    from routes.event_routes import events_bp
    from routes.notification_routes import notifications_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(bookings_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(notifications_bp)

    # JWT error responses (consistent JSON)
    @jwt.unauthorized_loader
    def jwt_missing_token(reason):
        return jsonify({"error": "unauthorized", "message": reason}), 401

    @jwt.invalid_token_loader
    def jwt_invalid_token(reason):
        return jsonify({"error": "unauthorized", "message": reason}), 401

    @jwt.expired_token_loader
    def jwt_expired_token(_jwt_header, _jwt_payload):
        return jsonify({"error": "unauthorized", "message": "Token has expired"}), 401

    @jwt.revoked_token_loader
    def jwt_revoked_token(_jwt_header, _jwt_payload):
        return jsonify({"error": "unauthorized", "message": "Token has been revoked"}), 401

    # Health check
    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    # Error handling
    @app.errorhandler(ApiError)
    def handle_api_error(err: ApiError):
        return jsonify(err.to_dict()), err.status_code

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": "not_found", "message": "Route not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(_):
        return jsonify({"error": "method_not_allowed", "message": "Method not allowed"}), 405

    @app.errorhandler(Exception)
    def unhandled(err):
        # In production, you would log this and return a generic message.
        message = "Internal server error"
        if app.config.get("DEBUG"):
            message = str(err)
        return jsonify({"error": "internal_error", "message": message}), 500

    # CLI command to initialize the database tables
    @app.cli.command("init-db")
    def init_db_command():
        from database.db import db
        import models  # noqa: F401

        db.create_all()
        print("Database tables created.")

    # DANGEROUS: drops all tables then recreates them.
    @app.cli.command("reset-db")
    def reset_db_command():
        from database.db import db
        import models  # noqa: F401

        db.drop_all()
        db.create_all()
        print("Database tables dropped and recreated.")

    return app


if __name__ == "__main__":
    # Run with: python app.py
    # Recommended: set env vars via a .env file in ./backend
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=app.config.get("DEBUG", True))
