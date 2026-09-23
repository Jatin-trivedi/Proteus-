import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models import db


def test_jwt_secret_login_and_protected_route(tmp_path):
    database_uri = f"sqlite:///{tmp_path / 'auth.db'}"
    from config import Config
    Config.SQLALCHEMY_DATABASE_URI = database_uri
    Config.DATABASE_URL = database_uri
    app = create_app()
    app.config.update(TESTING=True, JWT_SECRET="test-jwt-secret", SECRET_KEY="test-jwt-secret")

    with app.app_context():
        db.create_all()
        client = app.test_client()

        registered = client.post(
            "/api/v1/auth/register",
            json={"username": "smoke-user", "password": "correct horse battery staple"},
        )
        assert registered.status_code == 201
        token = registered.get_json()["access_token"]

        me = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me.status_code == 200
        assert me.get_json()["username"] == "smoke-user"

        db.session.remove()
        db.drop_all()
