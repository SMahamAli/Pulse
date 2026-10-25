"""Regression checks for the controls and edge cases audited before sharing."""

from datetime import timedelta
from html.parser import HTMLParser

import pytest

from conftest import post, service_for
from pulse import display


def test_assignment_waits_for_readings_and_freshness_is_not_permanent(service, clock):
    service.assign("P-2042", "PB-013")
    device = next(d for d in service.snapshot()["devices"] if d["id"] == "PB-013")
    assert device["connection"] == "Awaiting data"
    assert display.device_status(device, [], clock[0]) == "Awaiting first simulated reading"
    service.tick()
    data = service.snapshot()
    device = next(d for d in data["devices"] if d["id"] == "PB-013")
    assert display.device_status(device, data["readings"]["P-2042"], clock[0]) == "Demo · Connected"
    clock[0] += timedelta(minutes=16)
    assert "Stale" in display.device_status(device, data["readings"]["P-2042"], clock[0])
    disconnected = next(d for d in data["devices"] if d["id"] == "PB-014")
    assert "Disconnected" in display.device_status(disconnected, [], clock[0])


def test_closure_freezes_elapsed_time_and_blocks_new_symptoms(service, clock):
    arrival = service.visit("P-2041")["arrival"]
    service.close("P-2041")
    closed_at = service.visit("P-2041")["closedAt"]
    duration = display.waiting(arrival, closed_at)
    clock[0] += timedelta(hours=1)
    service.close("P-2041")
    assert service.visit("P-2041")["closedAt"] == closed_at
    assert display.waiting(arrival, closed_at) == duration
    with pytest.raises(ValueError, match="closed"):
        service.symptom("P-2041", "New description", "Now")


def test_general_message_review_does_not_complete_symptom_review(service):
    service.symptom("P-2041", "Fictional symptom change", "Now")
    service.review("P-2041")
    update = service.visit("P-2041")["updates"][-1]
    message = next(m for m in service.snapshot()["messages"] if m["id"] == update["id"])
    assert update["reviewed"] is None and message["reviewed"] is None
    service.review("P-2041", update["id"])
    assert service.visit("P-2041")["updates"][-1]["reviewed"]["by"]


@pytest.mark.parametrize(
    "value,kind,time,error",
    [
        ("nan", "Heart rate (bpm)", "2026-10-24T10:00", "finite numeric"),
        ("inf", "Heart rate (bpm)", "2026-10-24T10:00", "finite numeric"),
        ("abc", "Heart rate (bpm)", "2026-10-24T10:00", "numeric reading"),
        ("78", "Invented metric", "2026-10-24T10:00", "listed measurement"),
        ("78", "Heart rate (bpm)", "invalid", "valid measurement date"),
    ],
)
def test_invalid_optional_reading_is_not_submitted(app, client, value, kind, time, error):
    post(client, "/demo/patient")
    service = service_for(app, client)
    service.visit("P-2041")["intake"] = None
    response = post(
        client,
        "/intake/P-2041",
        dict(
            reason="Fictional reason",
            symptoms="Fictional symptoms",
            onset="Today",
            intent="submit",
            readingValue=value,
            readingType=kind,
            readingTime=time,
            readingSource="Demo equipment",
        ),
    )
    assert error.encode() in response.data
    assert service.visit("P-2041")["intake"] is None


def test_closed_patient_controls_explain_unavailability(app, client):
    post(client, "/demo/patient")
    service_for(app, client).close("P-2041")
    response = client.get("/patient")
    assert b"Visit closed: new messages" in response.data
    assert b'href="/symptoms/P-2041"' not in response.data
    response = post(client, "/symptoms/P-2041", dict(description="Change", onset="Now"))
    assert b"This visit is closed" in response.data
    assert service_for(app, client).visit("P-2041")["updates"] == []


def test_overlong_symptom_is_rejected_without_partial_update(service):
    before = service.snapshot()
    with pytest.raises(ValueError, match="2000"):
        service.symptom("P-2041", "x" * 2001, "Now")
    assert service.snapshot() == before


@pytest.mark.parametrize("role", ["patient", "staff", "admin"])
def test_reachable_internal_links_and_form_targets_exist(client, role):
    class Targets(HTMLParser):
        def __init__(self):
            super().__init__()
            self.links = set()
            self.forms = set()

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == "a" and attrs.get("href", "").startswith("/"):
                self.links.add(attrs["href"])
            if tag == "form" and attrs.get("action", "").startswith("/"):
                self.forms.add(attrs["action"])

    post(client, f"/demo/{role}")
    queue, seen, forms = ["/"], set(), set()
    while queue:
        path = queue.pop()
        if path in seen:
            continue
        seen.add(path)
        response = client.get(path, follow_redirects=True)
        assert response.status_code == 200, path
        parser = Targets()
        parser.feed(response.get_data(as_text=True))
        queue.extend(parser.links - seen)
        forms.update(parser.forms)
    # OPTIONS checks routing only; the browser tests verify actual form behaviour.
    for path in forms:
        assert "POST" in client.options(path).headers["Allow"], path
    assert len(seen) >= 5


def test_staff_status_review_device_filters_and_no_matches(client):
    post(client, "/demo/staff")
    for query, included, excluded in [
        ("status=awaiting+arrival", "Robin Lee", "Alex Morgan"),
        ("device=Disconnected", "Sam Taylor", "Alex Morgan"),
        ("review=symptoms", "No matching patients.", "Alex Morgan"),
        ("q=Alex&status=closed", "No matching patients.", "Alex Morgan"),
    ]:
        response = client.get("/staff/patients?" + query)
        assert included.encode() in response.data
        assert excluded.encode() not in response.data
