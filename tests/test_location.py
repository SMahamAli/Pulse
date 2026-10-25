"""Postcode search behaviour; automated tests never require a live postcode API."""

from io import BytesIO
import json
from urllib.error import HTTPError, URLError

import pytest

from conftest import post, service_for
from pulse import location


@pytest.mark.parametrize("value", ["LS6", " ls6 ", "LS6 1AA", "ls61aa"])
def test_postcodes_reduce_to_district(value):
    assert location.postcode_district(value) == "LS6"


@pytest.mark.parametrize("value", ["", "Leeds", "12345", "https://example.com", "LS6<script>"])
def test_invalid_postcode_is_rejected(value):
    with pytest.raises(ValueError, match="UK postcode"):
        location.lookup_area(value)


def test_ls6_saved_location_works_without_network(monkeypatch, service):
    def no_network(*args, **kwargs):
        pytest.fail("The LS6 demo must not require network access")

    monkeypatch.setattr(location, "urlopen", no_network)
    result = service.nearby_hospitals("LS6 1AA")
    assert result["area"]["district"] == "LS6"
    hospitals = result["hospitals"]
    assert [h["id"] for h in hospitals] == ["leeds-general", "st-james"]
    assert 1 < hospitals[0]["distance"] < 2
    assert hospitals[0]["distance"] < hospitals[1]["distance"]
    assert hospitals[0]["waitingLabel"] == "5–10"
    assert all(h["estimate"] is None for h in hospitals)


def test_remote_lookup_uses_only_district_and_fixed_api(monkeypatch):
    def response(url, timeout):
        assert url == "https://api.postcodes.io/outcodes/LS9"
        assert timeout == 4
        return BytesIO(json.dumps({"result": {"latitude": 53.80, "longitude": -1.50}}).encode())

    monkeypatch.setattr(location, "urlopen", response)
    area = location.lookup_area("LS9 7TF")
    assert area["district"] == "LS9"
    assert location.nearby([], area) == []


@pytest.mark.parametrize(
    "failure", [URLError("offline"), HTTPError("url", 404, "Not found", {}, None)]
)
def test_lookup_failure_explains_problem(monkeypatch, failure):
    def response(*args, **kwargs):
        raise failure

    monkeypatch.setattr(location, "urlopen", response)
    with pytest.raises(ValueError, match="unavailable|not found"):
        location.lookup_area("LS9")


def test_search_does_not_save_location_or_change_checked_in_hospital(app, client):
    post(client, "/demo/patient")
    service = service_for(app, client)
    before = service.snapshot()
    response = post(client, "/hospitals", {"postcode": "LS6 1AA"})
    assert b"Closest supported hospitals to LS6" in response.data
    assert "5–10".encode() in response.data and b"people waiting" in response.data
    assert b"not travel distance or time" in response.data
    assert b"LS6 1AA" not in response.data
    assert service.snapshot() == before
    with client.session_transaction() as session:
        assert "postcode" not in session and "location" not in session
    response = post(client, "/actions/hospital", dict(visit="P-2041", hospital="leeds-general"))
    assert b"Tell the team why you are coming" in response.data
    assert service.visit("P-2041") == before["visits"][0]
    with client.session_transaction() as session:
        assert session["patient_id"] != "P-2041"
    assert service.visit("P-2041")["hospital"] == "leeds-general"


def test_empty_catalogue_and_invalid_form_have_honest_results(monkeypatch, client):
    post(client, "/demo/patient")
    monkeypatch.setattr(
        location,
        "urlopen",
        lambda *a, **k: BytesIO(b'{"result":{"latitude":50.1,"longitude":-5.5}}'),
    )
    response = post(client, "/hospitals", dict(postcode="TR1"))
    assert b"No supported hospitals within 30 miles" in response.data
    assert b"does not mean there are no hospitals near you" in response.data
    response = post(client, "/hospitals", dict(postcode="invalid"))
    assert b"Enter a UK postcode" in response.data
    assert b"Leeds General Infirmary</h2>" not in response.data
