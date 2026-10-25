"""Hospital selection and multiple visits, without changing the original attendance."""

from copy import deepcopy

import pytest

from conftest import post, service_for


INTAKE = dict(reason="Fictional attendance", symptoms="Original test symptoms", onset="Today")


@pytest.mark.parametrize("original", ["P-2041", "P-2044"])
def test_submitted_or_checked_in_visit_is_preserved_when_planning_another(service, original):
    before = deepcopy(service.visit(original))
    reference = service.plan_visit(original, "st-james")
    assert reference != original and service.visit(original) == before
    planned = service.visit(reference)
    assert planned["patientId"] == before["patientId"]
    assert planned["hospital"] == "st-james"
    assert planned["arrival"] is None and planned["status"] == "awaiting arrival"
    assert planned["intake"] is None and planned["device"] is None
    assert planned["updates"] == [] and planned["notes"] == []
    assert planned["assessment"] == {"state": "pending"}
    assert len(service.patient_visits(before["patientId"])) == 2


def test_closed_visit_retains_form_and_new_visit_has_no_band(service):
    service.close("P-2041")
    closed = deepcopy(service.visit("P-2041"))
    new = service.plan_visit("P-2041", "st-james")
    assert service.visit("P-2041") == closed
    assert service.visit(new)["device"] is None
    assert next(d for d in service.snapshot()["devices"] if d["id"] == "PB-012")["visit"] is None


def test_unsubmitted_draft_is_reused_without_duplicate_attendance(service):
    new = service.plan_visit("P-2041", "leeds-general")
    again = service.plan_visit("P-2041", "st-james")
    assert again == new
    assert service.visit(new)["hospital"] == "st-james"
    assert len(service.patient_visits("P-2041")) == 2
    before = service.snapshot()
    with pytest.raises(ValueError, match="listed hospital"):
        service.plan_visit(new, "unknown")
    assert service.snapshot() == before


def test_demo_patient_can_choose_hospital_and_reopen_each_submitted_form(app, client):
    post(client, "/demo/patient")
    service = service_for(app, client)
    original = deepcopy(service.visit("P-2041"))
    response = post(client, "/actions/hospital", dict(visit="P-2041", hospital="st-james"))
    assert response.status_code == 200
    assert b"Tell the team why you are coming" in response.data
    with client.session_transaction() as session:
        reference = session["patient_id"]
        assert session["patient_owner"] == "P-2041"
    post(client, f"/intake/{reference}", dict(**INTAKE, intent="review"))
    response = post(client, f"/intake/{reference}", dict(**INTAKE, intent="submit"))
    assert b"Not started" in response.data
    assert service.visit("P-2041") == original
    history = client.get("/visits").get_data(as_text=True)
    assert "St James&#39;s University Hospital" in history
    assert "Leeds General Infirmary" in history
    assert "Original test symptoms" in history and "Dizziness and tiredness" in history
    assert "Jamie Parker" not in history
    assert client.get("/patient?visit=P-2041").status_code == 200
    response = client.get(f"/patient?visit={reference}")
    assert b"Original test symptoms" in response.data
    post(client, f"/symptoms/{reference}", dict(description="Another symptom", onset="Now"))
    assert service.visit(reference)["intake"]["symptoms"] == INTAKE["symptoms"]
    assert client.get("/visits").status_code == 200


def test_only_own_visit_history_can_be_opened_in_demo(client):
    post(client, "/demo/patient")
    assert client.get("/patient?visit=P-2042").status_code == 403
    assert client.get("/intake/P-2042").status_code == 403
    assert (
        post(client, "/actions/hospital", dict(visit="P-2042", hospital="st-james")).status_code
        == 403
    )


def test_staff_checks_in_correct_new_visit_and_patient_can_return_to_old_visit(app, client):
    post(client, "/demo/patient")
    post(client, "/actions/hospital", dict(visit="P-2041", hospital="st-james"))
    with client.session_transaction() as session:
        reference = session["patient_id"]
    post(client, f"/intake/{reference}", dict(**INTAKE, intent="submit"))
    post(client, "/demo/staff")
    response = post(client, "/actions/check_in", dict(visit=reference, back="details"))
    assert response.status_code == 200
    service = service_for(app, client)
    assert service.visit(reference)["arrival"]
    post(client, "/demo/patient")
    client.get("/patient?visit=P-2041")
    client.get(f"/patient?visit={reference}")
    with client.session_transaction() as session:
        assert session["patient_id"] == reference and session["patient_owner"] == "P-2041"


def test_registration_starts_its_own_history_and_reset_restores_default(app, client):
    post(
        client,
        "/register",
        dict(
            name="Fictional New Person",
            dob="1990-01-01",
            email="history@example.test",
            password="fictional123",
            confirm="fictional123",
        ),
    )
    history = client.get("/visits")
    assert b'aria-label="Visit P-2051"' in history.data
    assert b'aria-label="Visit P-2041"' not in history.data
    post(client, "/reset")
    assert client.get("/visits").status_code == 200
    with client.session_transaction() as session:
        assert session["patient_id"] == session["patient_owner"] == "P-2041"


def test_support_conversation_stays_with_person_when_selected_visit_changes(app, client):
    post(client, "/demo/patient")
    post(client, "/support", dict(subject="Fictional account question", text="Test support"))
    service = service_for(app, client)
    thread_id = service.snapshot()["support"][0]["id"]
    post(client, "/actions/hospital", dict(visit="P-2041", hospital="st-james"))
    response = client.get(f"/support/{thread_id}")
    assert response.status_code == 200 and b"Test support" in response.data


def test_intake_requires_hospital_and_failure_can_be_retried(app, client):
    post(
        client,
        "/register",
        dict(
            name="Fictional Person",
            dob="1990-01-01",
            email="retry@example.test",
            password="fictional123",
            confirm="fictional123",
        ),
    )
    with client.session_transaction() as session:
        reference = session["patient_id"]
    assert b"Choose a hospital" in client.get(f"/intake/{reference}", follow_redirects=True).data
    service = service_for(app, client)
    service.fail_next = True
    response = post(
        client, "/actions/hospital", dict(visit=reference, hospital="st-james", back="hospitals")
    )
    assert b"Simulated submission failed" in response.data
    assert service.visit(reference)["hospital"] is None
    response = post(client, "/actions/hospital", dict(visit=reference, hospital="st-james"))
    assert b"Tell the team why you are coming" in response.data
