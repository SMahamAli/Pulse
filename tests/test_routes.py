import pytest

from conftest import post, service_for


def test_login_and_templates(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Decorative animation" in response.data
    assert b"Demo patient" in response.data


@pytest.mark.parametrize(
    "role,paths",
    [
        ("patient", ["/patient", "/hospitals", "/messages", "/devices", "/symptoms/P-2041"]),
        (
            "staff",
            [
                "/staff",
                "/staff/patients",
                "/staff/patients/P-2041",
                "/inbox",
                "/alerts",
                "/devices",
                "/staff/register",
            ],
        ),
        ("admin", ["/admin", "/admin/access", "/admin/activity", "/support"]),
    ],
)
def test_role_pages_render(client, role, paths):
    post(client, f"/demo/{role}")
    for path in paths:
        assert client.get(path).status_code == 200, path


def test_registration_password_discard_and_refresh_persistence(app, client):
    response = post(
        client,
        "/register",
        dict(
            name="Fictional Patient",
            dob="1995-01-01",
            email="demo@example.test",
            password="fictional-only-123",
            confirm="fictional-only-123",
        ),
    )
    assert b"No real account" in response.data
    service = service_for(app, client)
    visit = service.snapshot()["visits"][-1]
    assert visit["arrival"] is None and visit["status"] == "awaiting arrival"
    assert "fictional-only-123" not in str(service.snapshot())
    with client.session_transaction() as session:
        assert "fictional-only-123" not in str(dict(session))
    assert client.get("/patient").status_code == 200
    assert service_for(app, client).visit(visit["id"])["name"] == "Fictional Patient"


def test_registration_errors_keep_no_password(client):
    response = post(
        client,
        "/register",
        dict(
            name="Demo",
            dob="1990-01-01",
            email="demo@example.test",
            password="fictional-one",
            confirm="fictional-two",
        ),
    )
    assert b"Passwords do not match" in response.data
    assert b"fictional-one" not in response.data


def test_intake_review_edit_and_submit(app, client):
    post(client, "/demo/patient")
    service = service_for(app, client)
    service.visit("P-2041")["intake"] = None
    values = dict(reason="Fictional reason", symptoms="Original fictional symptoms", onset="Today")
    response = post(client, "/intake/P-2041", dict(**values, intent="review"))
    assert b"Review your information" in response.data and service.visit("P-2041")["intake"] is None
    response = post(client, "/intake/P-2041", dict(**values, intent="edit"))
    assert b"Original fictional symptoms" in response.data
    post(client, "/intake/P-2041", dict(**values, intent="submit"))
    assert service.visit("P-2041")["intake"]["symptoms"] == values["symptoms"]


def test_csrf_and_demo_route_guards_not_real_auth(app, client):
    client.get("/")
    assert client.post("/demo/staff").status_code == 400
    post(client, "/demo/patient")
    assert post(client, "/actions/check_in", dict(visit="P-2044"), follow=False).status_code == 403
    assert client.get("/messages/P-2042").status_code == 403
    # Public demo entry deliberately permits changing roles: not production authentication.
    assert post(client, "/demo/staff").status_code == 200
    assert client.get("/staff").status_code == 200


def test_demo_browsers_are_isolated_and_reset(app, client):
    post(client, "/demo/patient")
    service = service_for(app, client)
    service.message("P-2041", "Only this browser")
    other = app.test_client()
    post(other, "/demo/patient")
    assert not any(
        m["text"] == "Only this browser" for m in service_for(app, other).snapshot()["messages"]
    )
    post(client, "/reset")
    assert not any(
        m["text"] == "Only this browser" for m in service_for(app, client).snapshot()["messages"]
    )


def test_failed_send_draft_is_server_memory_and_can_retry(app, client):
    post(client, "/demo/patient")
    service = service_for(app, client)
    service.fail_next = True
    response = post(
        client, "/messages/P-2041", dict(text="Fictional retry message", kind="general")
    )
    assert (
        b"Simulated submission failed" in response.data
        and b"Fictional retry message" in response.data
    )
    with client.session_transaction() as session:
        assert "Fictional retry message" not in str(dict(session))
    response = post(
        client, "/messages/P-2041", dict(text="Fictional retry message", kind="general")
    )
    assert sum(m["text"] == "Fictional retry message" for m in service.snapshot()["messages"]) == 1


def test_staff_assisted_registration_admin_and_acknowledgement(app, client):
    post(client, "/demo/staff")
    post(client, "/staff/register", dict(name="No Email Patient", dob="1990-01-01"))
    service = service_for(app, client)
    assert service.snapshot()["visits"][-1]["email"] is None
    post(client, "/actions/acknowledge", dict(id="a1", back="alerts"))
    assert service.snapshot()["alerts"][0]["ack"]["by"]
    post(client, "/demo/admin")
    post(
        client,
        "/actions/add_staff",
        dict(name="Demo Colleague", email="colleague@example.test", role="staff", back="admin"),
    )
    identifier = service.snapshot()["staff"][-1]["id"]
    post(client, "/actions/toggle_staff", dict(id=identifier, back="admin"))
    assert service.snapshot()["staff"][-1]["active"] is False


def test_health_data_escaped_and_forms_not_cookies(app, client):
    post(client, "/demo/patient")
    response = post(
        client, "/messages/P-2041", dict(text="<script>alert('test')</script>", kind="general")
    )
    assert b"<script>alert" not in response.data
    assert b"&lt;script&gt;" in response.data
    assert response.headers["Cache-Control"] == "no-store"
