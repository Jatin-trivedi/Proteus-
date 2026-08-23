from flask import Flask, render_template
from config import Config
from models import db
from api.agent_routes import agent_bp
from api.script_routes import script_bp
from api.result_routes import result_bp

def create_app():
    # Tell Flask where to find templates and static files
    app = Flask(__name__, 
                template_folder='dashboard/templates',
                static_folder='dashboard/static')
    app.config.from_object(Config)

    db.init_app(app)

    app.register_blueprint(agent_bp, url_prefix="/api/v1/agent")
    app.register_blueprint(script_bp, url_prefix="/api/v1/script")
    app.register_blueprint(result_bp, url_prefix="/api/v1/result")

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/scripts")
    def scripts():
        return render_template("scripts.html")

    @app.route("/results")
    def results():
        return render_template("results.html")

    @app.route("/realtime")
    def realtime():
        return render_template("realtime.html")

    return app

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)