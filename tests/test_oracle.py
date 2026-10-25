import io
import json
from urllib.error import HTTPError

import pytest

from conftest import post
from pulse.oracle import BASE, OracleService


class Responses:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests = []

    def open(self, request, timeout):
        self.requests.append(request)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return io.BytesIO(json.dumps(response).encode())


def oracle(tmp_path, *responses):
    transport = Responses(*responses)
    service = OracleService(
        environment={"ORACLE_CLIENT_ID": "test-client", "ORACLE_CLIENT_SECRET": "test-secret"},
        config_file=tmp_path / "not-present",
        opener=transport,
    )
    return service, transport


TOKEN = {"access_token": "test-token", "expires_in": 3600}
EMPTY = {"items": [], "hasMore": False}


def test_reads_actual_fields_and_preserves_missing_measurements(tmp_path):
    service, transport = oracle(
        tmp_path,
        TOKEN,
        {"items": [{"PATIENT_ID": 1000, "FORENAME": "Fictional", "SURNAME": "Patient"}]},
        {
            "items": [
                {
                    "PATIENT_ID": 1000,
                    "HEART_RATE": 75,
                    "SPO2": None,
                    "SKIN_TEMP": 35.2,
                    "RECORDED_AT": "2026-10-24T10:00:00",
                }
            ]
        },
        EMPTY,
    )
    result = service.snapshot()
    assert result["patients"][0]["databasePatientId"] == "1000"
    assert "spo2" not in result["readings"][0]
    assert result["readings"][0]["time"] == "2026-10-24T10:00:00"
    assert transport.requests[0].full_url == BASE + "oauth/token"
    assert transport.requests[0].get_method() == "POST"
    assert all(r.get_method() == "GET" for r in transport.requests[1:])
    assert all("test-secret" not in r.full_url for r in transport.requests)


@pytest.mark.parametrize(
    "target", ["https://other.example/steal", BASE + "staff/", BASE + "pulse/v1/patients/"]
)
def test_rejects_foreign_wrong_path_and_repeated_pagination(tmp_path, target):
    service, transport = oracle(
        tmp_path, TOKEN, {"items": [], "hasMore": True, "links": [{"rel": "next", "href": target}]}
    )
    with pytest.raises(ValueError, match="unsafe or repeated"):
        service.snapshot()
    assert len(transport.requests) == 2


def test_pagination_and_token_reuse(tmp_path):
    service, transport = oracle(
        tmp_path,
        TOKEN,
        {
            "items": [{"patient_id": 1}],
            "hasMore": True,
            "links": [{"rel": "next", "href": BASE + "pulse/v1/patients/?offset=25"}],
        },
        {"items": [{"patient_id": 2}], "hasMore": False},
        EMPTY,
        EMPTY,
        EMPTY,
        EMPTY,
        EMPTY,
    )
    assert len(service.snapshot()["patients"]) == 2
    assert service.snapshot()["patients"] == []
    assert sum(r.get_method() == "POST" for r in transport.requests) == 1


def test_access_failure_does_not_leak_response_or_keep_token(tmp_path):
    service, _ = oracle(
        tmp_path, TOKEN, HTTPError(BASE, 401, "test-secret", {}, io.BytesIO(b"private response"))
    )
    with pytest.raises(ValueError, match="rejected backend access") as error:
        service.snapshot()
    assert "test-secret" not in str(error.value)
    assert "private response" not in str(error.value)
    assert service._token is None


def test_staff_preview_reports_unconfigured_without_demo_rows(client):
    post(client, "/demo/staff")
    response = client.get("/staff/database")
    assert response.status_code == 200
    assert b"Oracle connection pending" in response.data
    assert b"No mock rows are substituted" in response.data
    assert b"Alex Morgan" not in response.data


@pytest.mark.parametrize("role", ["patient", "admin"])
def test_other_demo_roles_cannot_open_database_preview(client, role):
    post(client, "/demo/" + role)
    assert client.get("/staff/database").status_code == 403


def test_remote_clients_cannot_open_database_preview(client):
    post(client, "/demo/staff")
    assert (
        client.get("/staff/database", environ_overrides={"REMOTE_ADDR": "192.0.2.10"}).status_code
        == 403
    )


def test_configured_but_missing_views_does_not_ask_for_another_login(app, client, tmp_path):
    reader, _ = oracle(tmp_path, TOKEN, HTTPError(BASE, 403, "Forbidden", {}, None))
    app.extensions["oracle_service"] = reader
    post(client, "/demo/staff")
    response = client.get("/staff/database")
    assert b"Oracle records unavailable" in response.data
    assert b"Check the API permissions and source tables/views" in response.data
    assert b"needs its own protected API client credentials" not in response.data
    assert b"test-secret" not in response.data


def test_oracle_page_renders_supplied_rows_without_mixing_demo_patients(app, client, tmp_path):
    reader, _ = oracle(
        tmp_path,
        TOKEN,
        {
            "items": [
                {
                    "patient_id": 1000,
                    "forename": "Test",
                    "assignment_id": 7001,
                    "surname": "Record",
                    "nhs_number": "excluded-identifier",
                    "device_id": 3000,
                    "status": "Waiting",
                }
            ]
        },
        {
            "items": [
                {
                    "patient_id": 1000,
                    "heart_rate": 73,
                    "assignment_id": 7001,
                    "spo2": None,
                    "skin_temp": 35.1,
                    "recorded_at": "2026-10-24T10:00:00",
                }
            ]
        },
        EMPTY,
    )
    app.extensions["oracle_service"] = reader
    post(client, "/demo/staff")
    response = client.get("/staff/database")
    assert b"Test Record" in response.data and b"73.0 bpm" in response.data
    assert b"connectivity not verified" in response.data
    assert b"timezone unconfirmed" in response.data
    assert b"excluded-identifier" not in response.data
    assert b"Alex Morgan" not in response.data
    assert b"Register patient" not in response.data
    assert b"test-secret" not in response.data


@pytest.mark.parametrize("assignment", [7001, None])
def test_oracle_page_never_attaches_another_assignment_reading(app, client, tmp_path, assignment):
    reader, _ = oracle(
        tmp_path,
        TOKEN,
        {
            "items": [
                {
                    "patient_id": 1000,
                    "forename": "Test",
                    "surname": "Record",
                    "assignment_id": assignment,
                }
            ]
        },
        {"items": [{"patient_id": 1000, "assignment_id": 7002, "heart_rate": 191}]},
        EMPTY,
    )
    app.extensions["oracle_service"] = reader
    post(client, "/demo/staff")
    response = client.get("/staff/database")
    assert response.status_code == 200
    assert b"191.0 bpm" not in response.data
    assert b"No readings supplied for this active assignment" in response.data
