import os
import sys

# Ensure manager directory is on sys.path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from flask import Flask, jsonify, request
from config import Config
from models import db
from flask_migrate import Migrate
from flask_socketio import SocketIO
from api.agent_routes import agent_bp
from api.script_routes import script_bp
from api.result_routes import result_bp
from api.health_routes import health_bp
from api.auth_routes import auth_bp
from api.finding_routes import finding_bp
from api.report_routes import report_bp
from api.job_routes import job_bp
from api.investigation_routes import investigation_bp

# Initialize Migrate after db
migrate = Migrate()
socketio = SocketIO(cors_allowed_origins="*")

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)   # <-- This enables 'flask db' commands
    socketio.init_app(app)
    with app.app_context():
        db.create_all()
        # Ensure schema additions for existing SQLite database
        try:
            with db.engine.connect() as conn:
                inspector = db.inspect(db.engine)
                if "agents" in inspector.get_table_names():
                    cols = [c["name"] for c in inspector.get_columns("agents")]
                    for col_name, col_type in [
                        ("version", "VARCHAR(32) DEFAULT '1.0.0'"),
                        ("capabilities", "TEXT DEFAULT '[]'"),
                        ("registered_at", "DATETIME"),
                        ("current_job", "VARCHAR(64)"),
                    ]:
                        if col_name not in cols:
                            conn.execute(db.text(f"ALTER TABLE agents ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
        except Exception:
            pass

    @app.before_request
    def handle_api_options():
        if request.method == "OPTIONS" and request.path.startswith("/api/"):
            return "", 204
        return None

    @app.after_request
    def add_api_cors_headers(response):
        if request.path.startswith("/api/"):
            origin = request.headers.get("Origin")
            allowed = app.config.get("CORS_ALLOWED_ORIGINS", ())
            if origin:
                if "*" in allowed or origin in allowed or origin.endswith(".vercel.app") or origin.startswith("http://localhost"):
                    response.headers["Access-Control-Allow-Origin"] = origin
                    response.headers["Vary"] = "Origin"
                    response.headers["Access-Control-Allow-Headers"] = (
                        "Content-Type, Authorization, Accept"
                    )
                    response.headers["Access-Control-Allow-Methods"] = (
                        "GET, POST, PUT, PATCH, DELETE, OPTIONS"
                    )
                    response.headers["Access-Control-Allow-Credentials"] = "true"
        return response

    @app.errorhandler(404)
    def handle_not_found(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Not found"}), 404
        return error

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Method not allowed"}), 405
        return error

    @app.errorhandler(500)
    def handle_internal_server_error(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Internal server error"}), 500
        return error

    @app.route("/api/v1", strict_slashes=False)
    def api_root():
        return jsonify({
            "service": "Proteus manager API",
            "version": "v1",
            "health": "/health",
        })

    # The API blueprints already define their complete url_prefix values.
    app.register_blueprint(agent_bp)
    app.register_blueprint(agent_bp, url_prefix="/api/v1/agents", name="agents")
    app.register_blueprint(script_bp)
    app.register_blueprint(result_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(finding_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(job_bp)
    app.register_blueprint(investigation_bp)

    @app.route("/")
    @app.route("/dashboard")
    def index():
        return jsonify({
            "service": "Proteus manager API",
            "api": "/api/v1",
            "health": "/health",
        })

    return app

# Create application instance for WSGI servers such as Gunicorn.
app = create_app()

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port, debug=True)