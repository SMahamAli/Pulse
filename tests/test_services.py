from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest

from pulse import display
from pulse.oracle_mapping import map_current_patient, map_latest_vitals, map_open_alert


def prepared(service):
    reference = service.register(dict(name="Fictional Patient", dob="1990-01-01"))
    service.select_hospital(reference, "leeds-general")
    service.submit_intake(
        reference, dict(reason="Demo", symptoms="Original symptoms", onset="Today")
    )
    return reference


def test_registration_and_intake_are_not_arrival(service):
    reference = prepared(service)
    visit = service.visit(reference)
    assert visit["arrival"] is None
    assert visit["email"] is None
    assert visit["status"] == "awaiting arrival"
    assert display.waiting(visit["arrival"]) == "Not started"
    with pytest.raises(ValueError, match="arrival"):
        service.assign(reference, "PB-013")


def test_confirmed_checkin_starts_waiting_once(service, clock):
    reference = prepared(service)
    clock[0] += timedelta(minutes=20)
    service.check_in(reference)
    arrival = service.visit(reference)["arrival"]
    assert display.waiting_minutes(arrival, clock[0]) == 0
    clock[0] += timedelta(minutes=7, seconds=59)
    service.check_in(reference)
    assert service.visit(reference)["arrival"] == arrival
    assert display.waiting_minutes(arrival, clock[0]) == 7


def test_checkin_requires_hospital_and_intake(service):
    reference = service.register(dict(name="Demo", dob="1990-01-01"))
    with pytest.raises(ValueError, match="hospital"):
        service.check_in(reference)


def test_band_is_exclusive_and_released_on_close(service):
    reference = prepared(service)
    service.check_in(reference)
    service.assign(reference, "PB-013")
    with pytest.raises(ValueError, match="already assigned"):
        service.assign("P-2042", "PB-013")
    with pytest.raises(ValueError, match="already has"):
        service.assign(reference, "PB-015")
    service.tick()
    before = service.snapshot()["readings"][reference]
    service.close(reference)
    service.close(reference)
    service.tick()
    assert service.visit(reference)["device"] is None
    assert service.snapshot()["readings"][reference] == before
    service.assign("P-2042", "PB-013")
    assert service.visit("P-2042")["device"] == "PB-013"


def test_competing_assignments_one_demo_success(service):
    reference = prepared(service)
    service.check_in(reference)

    def assign(reference):
        try:
            service.assign(reference, "PB-013")
            return True
        except ValueError:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(assign, [reference, "P-2042"]))
    assert sum(outcomes) == 1  # Local process lock, not Oracle transaction proof.


def test_symptoms_preserve_intake_and_append_review_items(service):
    reference = prepared(service)
    original = service.snapshot()["visits"][-1]["intake"]
    service.symptom(reference, "Fictional change", "Ten minutes ago")
    service.symptom(reference, "Another change", "Now")
    snapshot = service.snapshot()
    visit = service.visit(reference)
    assert visit["intake"] == original
    assert len(visit["updates"]) == 2
    assert all(u["reviewed"] is None for u in visit["updates"])
    assert visit["assessment"] == {"state": "pending"}
    assert visit["category"] == "Awaiting review"
    assert len([m for m in snapshot["messages"] if m["visit"] == reference]) == 2
    assert len([a for a in snapshot["alerts"] if a["visit"] == reference]) == 2
    service.snapshot()
    assert len(service.snapshot()["alerts"]) == len(snapshot["alerts"])
    with pytest.raises(ValueError, match="already submitted"):
        service.submit_intake(reference, original)


def test_review_stamps_only_selected_update_and_message(service):
    service.symptom("P-2041", "One", "Today")
    service.symptom("P-2041", "Two", "Today")
    identifier = service.visit("P-2041")["updates"][0]["id"]
    service.review("P-2041", identifier)
    updates = service.visit("P-2041")["updates"]
    assert updates[0]["reviewed"]["time"] == service.now()
    assert updates[1]["reviewed"] is None
    assert (
        next(m for m in service.snapshot()["messages"] if m["id"] == identifier)["reviewed"]
        == updates[0]["reviewed"]
    )
    assert service.visit("P-2041")["assessment"]["state"] == "pending"


def test_human_messages_review_unread_and_leaving(service):
    service.message("P-2041", "I want to discuss leaving.")
    assert service.visit("P-2041")["status"] == "monitoring"
    assert service.snapshot()["messages"][-1]["reviewed"] is None
    service.review("P-2041")
    assert service.snapshot()["messages"][-1]["reviewed"]["by"]
    service.message("P-2041", "Fictional reply", sender="staff")
    assert service.snapshot()["messages"][-1]["read"] is False
    service.mark_read("P-2041")
    assert service.snapshot()["messages"][-1]["read"] is True


def test_help_acknowledgement_is_separate_and_stable(service, clock):
    service.message("P-2041", "Fictional assistance request", "help")
    identifier = service.snapshot()["alerts"][-1]["id"]
    service.acknowledge(identifier)
    stamp = service.snapshot()["alerts"][-1]["ack"]
    assert stamp["by"] and stamp["time"] == service.now()
    clock[0] += timedelta(minutes=1)
    service.acknowledge(identifier)
    assert service.snapshot()["alerts"][-1]["ack"] == stamp
    assert service.snapshot()["messages"][-1]["reviewed"] is None


def test_missing_stale_disconnected_and_changing_readings(service, clock):
    snapshot = service.snapshot()
    personal = snapshot["readings"]["P-2045"][0]
    assert display.metric_status(personal, "temperature", clock[0]) == "Unavailable"
    old = snapshot["readings"]["P-2043"][0]
    assert display.metric_status(old, "heartRate", clock[0]) == "Stale · check device"
    service.tick()
    assert service.snapshot()["readings"]["P-2043"] == snapshot["readings"]["P-2043"]
    assert len(service.snapshot()["readings"]["P-2041"]) == 3


def test_freshness_boundaries_invalid_and_future(clock):
    reading = dict(heartRate=78, time=clock[0].isoformat())
    assert (
        display.metric_status(reading, "heartRate", clock[0] + timedelta(minutes=15))
        == "Synthetic reading"
    )
    assert display.metric_status(
        reading, "heartRate", clock[0] + timedelta(minutes=15, seconds=1)
    ).startswith("Stale")
    assert (
        display.metric_status(dict(heartRate=78, time="invalid"), "heartRate")
        == "Reading time unavailable"
    )
    assert (
        display.metric_status(reading, "heartRate", clock[0] - timedelta(seconds=1))
        == "Reading time unavailable"
    )
    assert display.waiting_minutes("invalid") is None


def test_failure_does_not_mutate_and_retry_sends_once(service):
    before = service.snapshot()
    service.fail_next = True
    service.snapshot()
    with pytest.raises(ValueError, match="Simulated submission failed"):
        service.message("P-2041", "Retry me")
    assert service.snapshot() == before
    service.message("P-2041", "Retry me")
    assert sum(m["text"] == "Retry me" for m in service.snapshot()["messages"]) == 1


def test_staff_decision_destination_and_snapshot(service):
    snapshot = service.snapshot()
    snapshot["visits"][0]["name"] = "Changed outside service"
    assert service.snapshot()["visits"][0]["name"] == "Alex Morgan"
    with pytest.raises(ValueError, match="reason"):
        service.decision("P-2041", "Reviewed", "")
    service.decision("P-2041", "Reviewed", "Fictional review reason")
    service.destination("P-2041", "Waiting area B")
    service.note("P-2041", "Fictional note")
    assert service.visit("P-2041")["destination"]["text"] == "Waiting area B"
    assert len(service.visit("P-2041")["notes"]) == 2
    service.close("P-2041")
    with pytest.raises(ValueError, match="closed"):
        service.message("P-2041", "Cannot send")


def test_oracle_json_mapping_not_database_access():
    row = dict(
        PATIENT_ID=7, SKIN_TEMP="36.4", HEART_RATE=" ", SPO2=None, RESP_RATE=18, FALL_DETECTED="Y"
    )
    mapped = map_latest_vitals(row)
    assert mapped["temperature"] == 36.4
    assert mapped["heartRate"] is None
    assert set(mapped) == {
        "patientId",
        "assignmentId",
        "temperature",
        "heartRate",
        "time",
        "source",
    }
    for value in [None, "", "   ", True, "invalid", float("inf")]:
        assert map_latest_vitals(dict(heart_rate=value))["heartRate"] is None
    assert map_latest_vitals(dict(heart_rate=0))["heartRate"] == 0
    assert map_latest_vitals(dict(heart_rate="78"))["heartRate"] == 78
    patient = map_current_patient(
        dict(
            patient_id=7, forename="Demo", surname="Patient", triage="Urgent", status="In Treatment"
        )
    )
    assert patient["databaseStatus"] == "In Treatment" and "assessment" not in patient
    assert map_open_alert(dict(STATUS="Acknowledged"))["acknowledgedAt"] is None


def test_trend_preserves_gaps_and_missing_values():
    series = display.trend(
        [
            dict(heartRate=80, time="2026-10-24T10:02:00Z"),
            dict(heartRate=None, time="2026-10-24T10:01:00Z"),
            dict(heartRate=78, time="2026-10-24T10:00:00Z"),
        ],
        "heartRate",
    )
    assert series["path"].count("M") == 2 and "L" not in series["path"]
    assert display.trend([], "temperature")["count"] == 0
    assert display.trend([dict(temperature=None)], "temperature")["path"] == ""


def test_blank_database_acknowledgement_is_not_a_named_reviewer():
    assert map_open_alert({"acknowledged_by": " "})["acknowledgedBy"] is None
