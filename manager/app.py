from flask import Flask, jsonify, request
from config import Config
from models import db
from flask_migrate import Migrate
from api.agent_routes import agent_bp
from api.script_routes import script_bp
from api.result_routes import result_bp
from api.health_routes import health_bp
from api.auth_routes import auth_bp
from api.finding_routes import finding_bp
from api.report_routes import report_bp

# Initialize Migrate after db
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)   # <-- This enables 'flask db' commands
    with app.app_context():
        db.create_all()

    @app.before_request
    def handle_api_options():
        if request.method == "OPTIONS" and request.path.startswith("/api/"):
            return "", 204
        return None

    @app.after_request
    def add_api_cors_headers(response):
        if request.path.startswith("/api/"):
            origin = request.headers.get("Origin")
            if origin in app.config["CORS_ALLOWED_ORIGINS"]:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Vary"] = "Origin"
                response.headers["Access-Control-Allow-Headers"] = (
                    "Content-Type, Authorization"
                )
                response.headers["Access-Control-Allow-Methods"] = (
                    "GET, POST, PUT, PATCH, DELETE, OPTIONS"
                )
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

    # Register blueprints
    app.register_blueprint(agent_bp, url_prefix="/api/v1/agent")
    app.register_blueprint(script_bp, url_prefix="/api/v1/script")
    app.register_blueprint(result_bp, url_prefix="/api/v1/result")
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(finding_bp)
    app.register_blueprint(report_bp)

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
    app.run(host="0.0.0.0", port=port, debug=True)