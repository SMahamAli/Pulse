from datetime import datetime, timezone

import pytest

from pulse import create_app
from pulse.garmin import GarminAccess
from pulse.oracle import OracleService
from pulse.services import DemoService


@pytest.fixture
def clock():
    return [datetime(2026, 10, 24, 10, tzinfo=timezone.utc)]


@pytest.fixture
def service(clock):
    return DemoService(clock=lambda: clock[0])


@pytest.fixture
def app(tmp_path):
    app = create_app({"TESTING": True, "SECRET_KEY": "fictional-test-key-only"})
    app.extensions["garmin_access"] = GarminAccess(environment={}, key_file=tmp_path / "unset-key")
    app.extensions["oracle_service"] = OracleService(
        environment={}, config_file=tmp_path / "unset-oracle"
    )
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def post(client, path, data=None, follow=True):
    client.get("/")
    with client.session_transaction() as session:
        token = session["csrf"]
    return client.post(path, data={"csrf": token, **(data or {})}, follow_redirects=follow)


def service_for(app, client):
    with client.session_transaction() as session:
        return app.extensions["demo_services"][session["demo_id"]]
