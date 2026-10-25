"""Garmin HTTP test doubles only. No real credentials or personal data requests."""

import base64
from datetime import datetime, timezone
from io import BytesIO
import json
from urllib.error import HTTPError, URLError

import pytest

from conftest import post, service_for
from pulse.garmin import GarminAccess, NoCredentialRedirect, TOKEN_URL


TEST_KEY = "fictional-test-key-not-a-real-credential"


def token(expiry=None):
    expiry = expiry if expiry is not None else datetime.now(timezone.utc).timestamp() + 3600
    payload = base64.urlsafe_b64encode(json.dumps({"exp": expiry}).encode()).decode().rstrip("=")
    return f"test-header.{payload}.test-signature"


class TokenServer:
    def __init__(self, content=None, error=None):
        self.content = content if content is not None else token().encode()
        self.error = error
        self.calls = 0

    def open(self, request, timeout):
        self.calls += 1
        assert request.full_url == TOKEN_URL
        assert request.method == "POST" and timeout == 8
        assert request.get_header("Authorization") == f"ApiKey {TEST_KEY}"
        assert TEST_KEY not in request.full_url and request.data == b""
        if self.error:
            raise self.error
        return BytesIO(self.content)


def access_client(tmp_path, server=None, environment=None):
    return GarminAccess(
        key_file=tmp_path / "absent-key",
        environment=environment
        if environment is not None
        else {"GARMIN_PERSONAL_API_KEY": TEST_KEY},
        opener=server or TokenServer(),
    )


def test_garmin_configuration_and_absent_key_do_not_request_network(tmp_path):
    server = TokenServer()
    access = access_client(tmp_path, server, environment={})
    assert access.configuration() == "Not configured"
    with pytest.raises(ValueError, match="not configured"):
        access.check()
    assert server.calls == 0


def test_key_file_and_explicit_empty_environment_precedence(tmp_path):
    key_file = tmp_path / "local-fictional-key"
    key_file.write_text(TEST_KEY + "\n", encoding="utf-8")
    access = GarminAccess(key_file=key_file, environment={}, opener=TokenServer())
    assert access.configuration() == "Configured locally"
    assert access.check()["state"] == "API access verified"
    access = GarminAccess(key_file=key_file, environment={"GARMIN_PERSONAL_API_KEY": ""})
    assert access.configuration() == "Not configured"


def test_success_returns_only_access_metadata_not_key_or_token(tmp_path):
    bearer = token()
    server = TokenServer(bearer.encode())
    result = access_client(tmp_path, server).check()
    assert server.calls == 1
    assert result["state"] == "API access verified"
    assert "No health data was requested" in result["message"]
    assert TEST_KEY not in str(result) and bearer not in str(result)
    assert set(result) == {"state", "message", "checkedAt"}
    assert list(tmp_path.iterdir()) == []  # No token cache written to disk.


def test_json_access_token_envelope(tmp_path):
    server = TokenServer(json.dumps({"access_token": token()}).encode())
    assert access_client(tmp_path, server).check()["state"] == "API access verified"


@pytest.mark.parametrize(
    "status,expected",
    [
        (401, "rejected"),
        (403, "rejected"),
        (429, "request limit"),
        (500, "failed"),
        (302, "failed"),
    ],
)
def test_http_failures_never_expose_vendor_response(tmp_path, status, expected):
    server = TokenServer(
        error=HTTPError(TOKEN_URL, status, TEST_KEY, {}, BytesIO(TEST_KEY.encode()))
    )
    with pytest.raises(ValueError, match=expected) as error:
        access_client(tmp_path, server).check()
    assert TEST_KEY not in str(error.value)


@pytest.mark.parametrize("content", [b"", b"invalid", b"{}", b"bad.bad.bad", b"x" * 16385])
def test_bad_token_responses_are_not_connected_states(tmp_path, content):
    with pytest.raises(ValueError, match="unexpected|invalid"):
        access_client(tmp_path, TokenServer(content)).check()


def test_expired_token_network_failure_and_header_injection(tmp_path):
    with pytest.raises(ValueError, match="expired"):
        access_client(tmp_path, TokenServer(token(1).encode())).check()
    with pytest.raises(ValueError, match="could not be reached") as error:
        access_client(tmp_path, TokenServer(error=URLError(TEST_KEY))).check()
    assert TEST_KEY not in str(error.value)
    with pytest.raises(ValueError, match="format"):
        access_client(tmp_path, environment={"GARMIN_PERSONAL_API_KEY": "bad\nheader"}).check()
    assert (
        NoCredentialRedirect().redirect_request(None, None, 302, "", {}, "https://other.test")
        is None
    )


def test_routes_do_not_expose_credentials_or_change_demo_readings(app, client, tmp_path):
    app.extensions["garmin_access"] = access_client(tmp_path)
    post(client, "/demo/patient")
    service = service_for(app, client)
    before = service.snapshot()
    response = post(client, "/devices/garmin/check")
    assert b"API access verified" in response.data
    assert b"Watch connection not verified" in response.data
    assert TEST_KEY.encode() not in response.data
    assert service.snapshot() == before
    with client.session_transaction() as session:
        assert TEST_KEY not in str(dict(session)) and "garmin" not in session
    post(client, "/demo/admin")
    assert post(client, "/devices/garmin/check", follow=False).status_code == 403


def test_configuration_error_and_missing_key_render_helpful_ui(app, client, tmp_path):
    app.extensions["garmin_access"] = access_client(tmp_path, environment={})
    post(client, "/demo/patient")
    response = post(client, "/devices/garmin/check")
    assert b"Garmin is not configured" in response.data
    assert b"Access not verified" in response.data
    assert b"Garmin setup instructions" in response.data
