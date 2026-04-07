import os

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from config import Config
from database.db import jwt
from database.db import init_extensions
from services.errors import ApiError


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["ALLOW_ADMIN_REGISTRATION"] = Config.ALLOW_ADMIN_REGISTRATION
    
    # Uploads
    upload_dir = os.path.join(app.root_path, "uploads")
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    app.config["UPLOAD_FOLDER"] = upload_dir

    # Extensions
    init_extensions(app)

    # CORS
    cors_origins = app.config.get("CORS_ORIGINS", "*")
    CORS(app, resources={r"/*": {"origins": cors_origins}})

    # Register blueprints
    from routes.auth_routes import auth_bp
    from routes.institute_routes import institute_bp
    from routes.admin_routes import admin_bp
    from routes.event_routes import events_bp
    from routes.participant_routes import participant_bp

    from routes.leaderboard_routes import leaderboard_bp
    from routes.result_routes import results_bp
    from routes.social_routes import social_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(institute_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(participant_bp)

    app.register_blueprint(leaderboard_bp)
    app.register_blueprint(results_bp)
    app.register_blueprint(social_bp)

    # Serve frontend static files
    frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

    @app.route("/")
    def serve_index():
        return send_from_directory(frontend_dir, "index.html")

    @app.route("/<path:filename>")
    def serve_frontend(filename):
        file_path = os.path.join(frontend_dir, filename)
        if os.path.isfile(file_path):
            return send_from_directory(frontend_dir, filename)
        return send_from_directory(frontend_dir, "index.html")

    @app.route("/uploads/<path:filename>")
    def serve_upload(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    # JWT error handlers
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

    # Error handlers
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
        message = "Internal server error"
        if app.config.get("DEBUG"):
            message = str(err)
        return jsonify({"error": "internal_error", "message": message}), 500

    # CLI commands
    @app.cli.command("init-db")
    def init_db_command():
        from database.db import db
        import models  # noqa: F401
        db.create_all()
        print("Database tables created.")

    @app.cli.command("reset-db")
    def reset_db_command():
        from database.db import db
        import models  # noqa: F401
        db.drop_all()
        db.create_all()
        print("Database tables dropped and recreated.")

    @app.cli.command("seed-admin")
    def seed_admin():
        from database.db import db
        from models.user import User
        admin = User.query.filter_by(email="baradmanik@gmail.com").first()
        if not admin:
            admin = User(email="baradmanik@gmail.com", username="admin", full_name="Platform Admin", role="ADMIN")
            admin.set_password("Manik1092")
            db.session.add(admin)
            db.session.commit()
            print("Admin user created: baradmanik@gmail.com / Manik1092")
        else:
            print("Admin user already exists.")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=app.config.get("DEBUG", True))
