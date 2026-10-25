"""Navigation clarity, source separation and the human Chat workspace."""

from html.parser import HTMLParser

import pytest

from conftest import post, service_for


class Navigation(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_nav = False
        self.labels = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "nav" and attrs.get("aria-label") == "Main navigation":
            self.in_nav = True
        if self.in_nav and tag == "a":
            self.labels.append(attrs.get("aria-label", attrs.get("title")))

    def handle_endtag(self, tag):
        if tag == "nav":
            self.in_nav = False


@pytest.mark.parametrize(
    "role,expected",
    [
        ("patient", ["Home", "My visits", "Hospitals", "Chat", "Devices"]),
        ("staff", ["Home", "Patients", "Chat", "Devices", "Alerts"]),
        ("admin", ["Home", "Staff & admin access", "Login activity", "Chat"]),
    ],
)
def test_role_navigation_has_unique_meaningful_destinations(client, role, expected):
    post(client, "/demo/" + role)
    response = client.get("/", follow_redirects=True)
    parser = Navigation()
    parser.feed(response.get_data(as_text=True))
    assert parser.labels == expected
    assert len(set(parser.labels)) == len(parser.labels)


@pytest.mark.parametrize(
    "role,targets",
    [
        ("patient", ["/messages", "/support"]),
        ("staff", ["/inbox", "/support"]),
        ("admin", ["/support?audience=patient", "/support?audience=staff"]),
    ],
)
def test_chat_hub_has_two_working_human_channels(client, role, targets):
    post(client, "/demo/" + role)
    hub = client.get("/chat")
    assert hub.status_code == 200 and b"not an AI chatbot" in hub.data
    for target in targets:
        assert target.replace("&", "&amp;").encode() in hub.data
        response = client.get(target)
        assert response.status_code == 200
        assert b"Back to Chat" in response.data


def test_admin_can_start_patient_support_without_clinical_access(app, client):
    post(client, "/demo/admin")
    post(
        client,
        "/support?audience=patient",
        dict(
            target="patient",
            patient_reference="P-2041",
            subject="Test portal help",
            text="Fictional admin message",
        ),
    )
    service = service_for(app, client)
    thread = service.snapshot()["support"][-1]
    assert thread["participants"] == ["admin", "patient"] and thread["patientId"] == "P-2041"
    assert client.get("/staff/patients/P-2041").status_code == 403
    post(client, "/demo/patient")
    response = client.get("/support/" + thread["id"])
    assert b"Fictional admin message" in response.data
    post(client, "/support/" + thread["id"], dict(text="Fictional patient reply"))
    post(client, "/demo/admin")
    assert b"Fictional patient reply" in client.get("/support/" + thread["id"]).data


def test_staff_home_is_summary_and_patients_has_explicit_sources(client):
    post(client, "/demo/staff")
    home = client.get("/staff")
    assert b"YOUR SHIFT AT A GLANCE" in home.data and b"<table>" not in home.data
    patients = client.get("/staff/patients")
    assert b"<table>" in patients.data and b"Alex Morgan" in patients.data
    assert b"Demo workflow" in patients.data and b"Oracle records" in patients.data
    assert b"separate demonstration datasets" in patients.data


@pytest.mark.parametrize(
    "role,paths",
    [
        ("patient", ["/patient", "/hospitals", "/devices", "/messages", "/visits"]),
        ("staff", ["/staff", "/staff/patients", "/staff/patients/P-2041"]),
    ],
)
def test_removed_metric_not_rendered_in_website(client, role, paths):
    post(client, "/demo/" + role)
    for path in paths:
        response = client.get(path)
        assert response.status_code == 200
        assert b"spo2" not in response.data.lower()
        assert b"oxygen saturation" not in response.data.lower()
