"""Submit the rendered demo action families and check results, not only route existence."""

import pytest

from conftest import post, service_for


@pytest.mark.parametrize(
    "role,action,values,back",
    [
        ("patient", "hospital", {"visit": "P-2041", "hospital": "st-james"}, "patient"),
        ("patient", "help", {"visit": "P-2041"}, "patient"),
        ("patient", "mark_read", {"visit": "P-2041"}, "messages"),
        ("patient", "tick", {}, "devices"),
        ("patient", "fail_next", {}, "messages"),
        ("staff", "check_in", {"visit": "P-2044"}, "details"),
        ("staff", "assign", {"visit": "P-2042", "device": "PB-013"}, "details"),
        ("staff", "close", {"visit": "P-2041"}, "details"),
        ("staff", "review", {"visit": "P-2041"}, "messages"),
        (
            "staff",
            "decision",
            {"visit": "P-2041", "category": "Test review", "reason": "Test reason"},
            "details",
        ),
        ("staff", "destination", {"visit": "P-2041", "text": "Test waiting area"}, "details"),
        ("staff", "note", {"visit": "P-2041", "text": "Test staff note"}, "details"),
        ("staff", "acknowledge", {"id": "a1"}, "alerts"),
        (
            "admin",
            "add_staff",
            {"name": "Test admin", "email": "admin2@example.test", "role": "admin"},
            "admin_access",
        ),
        ("admin", "toggle_staff", {"id": "s1"}, "admin_access"),
    ],
)
def test_action_controls_submit_and_change_expected_demo_state(
    app, client, role, action, values, back
):
    post(client, "/demo/" + role)
    service = service_for(app, client)
    response = post(client, "/actions/" + action, dict(back=back, **values))
    assert response.status_code == 200
    assert b"Request unavailable" not in response.data
    state = service.snapshot()
    checks = {
        "hospital": lambda: state["visits"][-1]["hospital"] == "st-james"
        and state["visits"][-1]["arrival"] is None,
        "help": lambda: state["messages"][-1]["kind"] == "help"
        and state["alerts"][-1]["kind"] == "help",
        "mark_read": lambda: next(m for m in state["messages"] if m["id"] == "m2")["read"],
        "tick": lambda: len(state["readings"]["P-2041"]) == 3,
        "fail_next": lambda: service.fail_next,
        "check_in": lambda: service.visit("P-2044")["status"] == "awaiting band",
        "assign": lambda: service.visit("P-2042")["device"] == "PB-013",
        "close": lambda: service.visit("P-2041")["status"] == "closed"
        and state["devices"][0]["visit"] is None,
        "review": lambda: state["messages"][0]["reviewed"]["by"],
        "decision": lambda: service.visit("P-2041")["category"] == "Test review",
        "destination": lambda: service.visit("P-2041")["destination"]["text"]
        == "Test waiting area",
        "note": lambda: service.visit("P-2041")["notes"][-1]["text"] == "Test staff note",
        "acknowledge": lambda: state["alerts"][0]["ack"]["by"],
        "add_staff": lambda: state["staff"][-1]["role"] == "admin",
        "toggle_staff": lambda: state["staff"][0]["active"] is False,
    }
    assert checks[action]()


@pytest.mark.parametrize(
    "action,values,expected",
    [
        (
            "assign",
            {"visit": "P-2042", "device": "missing"},
            "Band is already assigned or unavailable",
        ),
        ("review", {"visit": "P-2041", "update": "missing"}, "Symptom update not found"),
        ("decision", {"visit": "P-2041", "category": "", "reason": ""}, "Enter a staff category"),
        ("destination", {"visit": "P-2041", "text": ""}, "Enter a confirmed department"),
        ("note", {"visit": "P-2041", "text": ""}, "Enter a note"),
        ("acknowledge", {"id": "missing"}, "Alert not found"),
    ],
)
def test_rejected_staff_forms_return_usable_page_without_partial_update(
    app, client, action, values, expected
):
    post(client, "/demo/staff")
    service = service_for(app, client)
    before = service.snapshot()
    response = post(client, "/actions/" + action, dict(back="staff", **values))
    assert response.status_code == 200 and expected.encode() in response.data
    assert service.snapshot() == before


def test_old_action_form_after_reset_returns_home_instead_of_broken_details(app, client):
    post(client, "/demo/staff")
    service = service_for(app, client)
    reference = service.register(dict(name="Test stale form", dob="1990-01-01"))
    post(client, "/reset")
    response = post(client, "/actions/close", dict(visit=reference, back="details"))
    assert response.status_code == 200
    assert b"Visit not found" in response.data
    assert b"Stay close. See what needs attention." in response.data
