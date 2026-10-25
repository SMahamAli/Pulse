"""Demo role boundaries and support behaviour; not production authentication tests."""

import pytest

from conftest import post, service_for


@pytest.mark.parametrize(
    "path",
    [
        "/staff",
        "/staff/patients",
        "/staff/patients/P-2041",
        "/staff/register",
        "/intake/P-2041",
        "/messages/P-2041",
        "/symptoms/P-2041",
        "/inbox",
        "/devices",
        "/alerts",
    ],
)
def test_admin_demo_role_cannot_open_patient_care_routes(client, path):
    post(client, "/demo/admin")
    assert client.get(path).status_code == 403


@pytest.mark.parametrize(
    "action,values",
    [
        ("check_in", {"visit": "P-2042"}),
        ("assign", {"visit": "P-2042", "device": "PB-013"}),
        ("hospital", {"visit": "P-2041", "hospital": "st-james"}),
        ("help", {"visit": "P-2041"}),
        ("acknowledge", {"id": "a1"}),
        ("tick", {}),
    ],
)
def test_admin_demo_role_cannot_mutate_clinical_workflow(app, client, action, values):
    post(client, "/demo/admin")
    service = service_for(app, client)
    before = service.snapshot()
    response = post(client, f"/actions/{action}", values, follow=False)
    assert response.status_code == 403
    after = service.snapshot()
    assert after["visits"] == before["visits"] and after["devices"] == before["devices"]
    assert after["alerts"] == before["alerts"] and after["readings"] == before["readings"]


def test_admin_navigation_and_activity_are_truthful_and_exportable(app, client):
    post(client, "/login", {"email": "not-recorded@example.test", "password": "never-record-this"})
    post(client, "/demo/admin")
    response = client.get("/admin")
    assert b"Admin overview" in response.data and b"Login activity" in response.data
    for forbidden in [b"Register patient", b'href="/staff"', b'href="/inbox"', b"Alex Morgan"]:
        assert forbidden not in response.data
    activity = service_for(app, client).snapshot()["activity"]
    assert any(e["event"] == "Password sign-in unavailable" for e in activity)
    assert any(e["event"] == "Demo role entered" for e in activity)
    assert "never-record-this" not in str(activity) and "not-recorded@example.test" not in str(
        activity
    )
    export = client.get("/admin/activity.csv")
    assert export.status_code == 200 and export.mimetype == "text/csv"
    assert b"time,event,actor,detail,outcome" in export.data
    assert b"Password sign-in unavailable" in export.data
    assert client.get("/admin/security").location == "/admin"


def test_patient_admin_support_roundtrip_and_read_receipt(app, client):
    post(client, "/demo/patient")
    before_care = service_for(app, client).snapshot()["messages"]
    post(client, "/support", dict(subject="Portal question", text="Fictional portal help"))
    service = service_for(app, client)
    identifier = service.snapshot()["support"][-1]["id"]
    post(client, "/demo/admin")
    response = client.get("/support")
    assert b"Portal question" in response.data and b"Unread patient message" in response.data
    post(client, f"/support/{identifier}", dict(intent="read"))
    post(client, f"/support/{identifier}", dict(text="Fictional admin reply"))
    post(client, "/demo/patient")
    response = client.get(f"/support/{identifier}")
    assert b"Fictional admin reply" in response.data
    assert service.snapshot()["support"][-1]["messages"][-1]["readBy"] == ["admin"]
    post(client, f"/support/{identifier}", dict(intent="read"))
    assert service.snapshot()["support"][-1]["messages"][-1]["readBy"] == ["admin", "patient"]
    assert service.snapshot()["messages"] == before_care


def test_support_thread_visibility_identity_and_failure_retry(service):
    before_care = service.snapshot()["messages"]
    identifier = service.start_support("patient", "P-2041", "Account help", "Question")
    with pytest.raises(ValueError, match="unavailable"):
        service.support_thread(identifier, "staff", "P-2041")
    with pytest.raises(ValueError, match="unavailable"):
        service.support_thread(identifier, "patient", "P-2042")
    service.fail_next = True
    with pytest.raises(ValueError, match="Simulated submission failed"):
        service.reply_support(identifier, "admin", None, "Try again")
    assert len(service.support_thread(identifier, "admin", None)["messages"]) == 1
    service.reply_support(identifier, "admin", None, "Try again")
    assert len(service.support_thread(identifier, "admin", None)["messages"]) == 2
    assert service.snapshot()["messages"] == before_care
    other = service.start_support("admin", None, "Staff equipment question", "Question")
    service.reply_support(other, "staff", None, "Staff reply")
    assert service.support_threads("patient", "P-2042") == []
    assert [t["id"] for t in service.support_threads("staff", None)] == [other]


def test_support_route_rejects_forged_role_and_preserves_failed_reply(app, client):
    post(client, "/demo/patient")
    response = post(client, "/support", dict(subject="Help", text="Patient text", role="admin"))
    service = service_for(app, client)
    thread = service.snapshot()["support"][-1]
    assert thread["messages"][0]["role"] == "patient"
    post(client, "/demo/staff")
    assert client.get(f"/support/{thread['id']}").status_code == 404
    post(client, "/demo/admin")
    service.fail_next = True
    response = post(client, f"/support/{thread['id']}", dict(text="Retained retry text"))
    assert (
        b"Simulated submission failed" in response.data and b"Retained retry text" in response.data
    )
    assert len(service.snapshot()["support"][-1]["messages"]) == 1
    post(client, f"/support/{thread['id']}", dict(text="Retained retry text"))
    assert len(service.snapshot()["support"][-1]["messages"]) == 2


def test_profile_duplicates_and_activity_limit(service):
    service.add_staff("Fictional Admin", " ADDITIONAL-ADMIN@example.test ", "admin")
    with pytest.raises(ValueError, match="already uses"):
        service.add_staff("Duplicate", "additional-admin@example.test", "staff")
    assert service.snapshot()["staff"][-1]["role"] == "admin"
    assert service.snapshot()["activity"][0]["event"] == "Profile created"
    for _ in range(205):
        service.record_activity("Test demo event", "admin", "No form data")
    assert len(service.snapshot()["activity"]) == 200


def test_support_validation_and_escaped_content(app, client):
    post(client, "/demo/patient")
    service = service_for(app, client)
    for values in [dict(subject="", text="Text"), dict(subject="Subject", text="x" * 2001)]:
        post(client, "/support", values)
        assert service.snapshot()["support"] == []
    response = post(
        client, "/support", dict(subject="<b>Subject</b>", text="<script>test</script>")
    )
    assert b"&lt;script&gt;test&lt;/script&gt;" in response.data
    assert b"<script>test</script>" not in response.data


def test_non_ascii_csrf_is_blocked_and_recorded_not_a_server_error(app, client):
    post(client, "/demo/admin")
    response = client.post("/demo/staff", data={"csrf": "invalid-\u00e9"})
    assert response.status_code == 400
    assert service_for(app, client).snapshot()["activity"][0]["event"] == "Form rejected"
