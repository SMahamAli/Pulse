"""Python Playwright smoke tests. No React, Node/npm commands or JavaScript test source."""

from pathlib import Path
from threading import Thread

import pytest
from playwright.sync_api import expect, sync_playwright
from werkzeug.serving import make_server

from pulse import create_app
from pulse.garmin import GarminAccess
from pulse.oracle import OracleService

pytestmark = pytest.mark.browser


@pytest.fixture(scope="module")
def live_app():
    app = create_app({"TESTING": True})
    app.extensions["garmin_access"] = GarminAccess(environment={"GARMIN_PERSONAL_API_KEY": ""})
    app.extensions["oracle_service"] = OracleService(
        environment={"ORACLE_CLIENT_ID": "", "ORACLE_CLIENT_SECRET": ""}
    )
    return app


@pytest.fixture(scope="module")
def live_url(live_app):
    app = live_app
    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    thread.join(timeout=5)


@pytest.fixture
def page(live_url):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(
            base_url=live_url,
            viewport=dict(width=1440, height=960),
            reduced_motion="reduce",
            java_script_enabled=False,
        )
        context.route("https://fonts.googleapis.com/**", lambda route: route.abort())
        page = context.new_page()
        yield page
        browser.close()


def role(page, name):
    page.get_by_role("button", name="Switch demo role", exact=True).click()
    page.get_by_role("button", name=f"Demo {name}", exact=True).click()
    if name == "staff":
        page.get_by_role("navigation").get_by_role("link", name="Patients", exact=True).click()


def channel(page, target):
    page.get_by_role("navigation").get_by_role("link", name="Chat", exact=True).click()
    page.locator(f'.chat-options a[href="{target}"]').click()


def test_python_full_patient_staff_journey(page):
    page.goto("/")
    page.get_by_role("link", name="Register as a patient", exact=True).click()
    for label, value in {
        "Full name": "Fictional Python Patient",
        "Date of birth": "1995-04-12",
        "Email": "python@example.test",
        "Password (8 or more characters)": "fictional-only-123",
        "Confirm password": "fictional-only-123",
    }.items():
        page.get_by_label(label, exact=True).fill(value)
    page.get_by_role("button", name="Create demo profile", exact=True).click()
    expect(page.get_by_role("heading", name="Hospitals", exact=True)).to_be_visible()
    page.get_by_label("Enter your postcode", exact=True).fill("LS6")
    page.get_by_role("button", name="Search hospitals", exact=True).click()
    hospital = page.locator("article.hospital").filter(has_text="Leeds General Infirmary")
    expect(hospital).to_contain_text("people waiting")
    hospital.get_by_role("button", name="Select hospital", exact=True).click()
    page.get_by_label("Reason for attending", exact=True).fill("Fictional attendance")
    page.get_by_label("Symptoms", exact=True).fill("Original fictional symptoms")
    page.get_by_label("When did symptoms start?", exact=True).fill("This morning")
    page.get_by_role("button", name="Review information", exact=True).click()
    page.get_by_role("button", name="Edit information", exact=True).click()
    expect(page.get_by_label("Symptoms", exact=True)).to_have_value("Original fictional symptoms")
    page.get_by_role("button", name="Review information", exact=True).click()
    page.get_by_role("button", name="Submit intake", exact=True).click()
    expect(page.get_by_role("region", name="Waiting duration")).to_contain_text("Not started")
    role(page, "staff")
    page.get_by_role("link", name="Fictional Python Patient", exact=True).click()
    page.get_by_role("button", name="Confirm arrival", exact=True).click()
    expect(page.get_by_role("button", name="Confirm arrival", exact=True)).to_be_disabled()
    page.get_by_label("Available band", exact=True).select_option("PB-013")
    page.get_by_role("button", name="Assign band", exact=True).click()
    page.get_by_role("navigation").get_by_role("link", name="Devices", exact=True).click()
    page.get_by_role("button", name="Simulate changing readings", exact=True).click()
    role(page, "patient")
    expect(page.get_by_role("region", name="Waiting duration")).to_contain_text("0 min")
    expect(page.get_by_role("article", name="Heart rate", exact=True)).to_contain_text(
        "Synthetic reading"
    )
    page.get_by_role("link", name="Report new symptoms", exact=True).click()
    page.get_by_label("What has started or changed?", exact=True).fill("Fictional new symptom")
    page.get_by_label("When did this start or change?", exact=True).fill("Ten minutes ago")
    page.get_by_role("button", name="Send symptom update", exact=True).click()
    role(page, "staff")
    page.get_by_role("link", name="Symptoms to review 1", exact=True).click()
    page.get_by_role("link", name="Fictional Python Patient", exact=True).click()
    expect(page.get_by_text("Original fictional symptoms", exact=True)).to_be_visible()
    page.get_by_role("button", name="Mark reviewed", exact=True).click()
    page.get_by_role("link", name="Open conversation", exact=True).click()
    page.get_by_role("textbox", name="Reply to patient", exact=True).fill(
        "Fictional Python staff reply"
    )
    page.get_by_role("button", name="Send reply", exact=True).click()
    role(page, "patient")
    channel(page, "/messages")
    expect(page.get_by_text("Fictional Python staff reply", exact=True)).to_be_visible()
    role(page, "staff")
    page.get_by_role("link", name="Fictional Python Patient", exact=True).click()
    page.get_by_role("button", name="Close visit / release band", exact=True).click()
    page.get_by_role("navigation").get_by_role("link", name="Devices", exact=True).click()
    expect(page.locator(".inbox-row").filter(has_text="PB-013")).to_contain_text(
        "Available / unassigned"
    )


def test_python_mobile_and_invalid_forms(page):
    page.set_viewport_size(dict(width=390, height=844))
    page.goto("/")
    page.get_by_role("link", name="Register as a patient", exact=True).click()
    for label, value in {
        "Full name": "Fictional Mobile",
        "Date of birth": "1995-01-01",
        "Email": "mobile@example.test",
        "Password (8 or more characters)": "fictional-one",
        "Confirm password": "fictional-two",
    }.items():
        page.get_by_label(label, exact=True).fill(value)
    page.get_by_role("button", name="Create demo profile", exact=True).click()
    expect(page.get_by_role("alert")).to_contain_text("Passwords do not match")
    page.get_by_role("link", name="Back to Pulse", exact=True).click()
    page.get_by_role("button", name="Demo patient", exact=True).click()
    expect(page.get_by_role("heading", name="Your visit, step by step", exact=True)).to_be_visible()
    main = page.locator("main").bounding_box()
    assert main and main["x"] + main["width"] <= page.viewport_size["width"]
    Path("test-results").mkdir(exist_ok=True)
    page.screenshot(path="test-results/flask-patient-mobile.png", full_page=True)
    role(page, "staff")
    expect(page.get_by_role("heading", name="Patients", exact=True)).to_be_visible()
    main = page.locator("main").bounding_box()
    assert main and main["x"] + main["width"] <= page.viewport_size["width"]
    page.screenshot(path="test-results/flask-staff-mobile.png", full_page=True)


def test_python_stale_readings_and_failed_message_retry(page):
    page.goto("/")
    page.get_by_role("button", name="Demo staff", exact=True).click()
    page.get_by_role("navigation").get_by_role("link", name="Patients", exact=True).click()
    expect(page.get_by_role("row").filter(has_text="Sam Taylor")).to_contain_text("Disconnected")
    page.get_by_role("link", name="Sam Taylor", exact=True).click()
    expect(page.get_by_role("article", name="Heart rate", exact=True)).to_contain_text(
        "Stale · check device"
    )
    page.get_by_role("navigation").get_by_role("link", name="Patients", exact=True).click()
    page.get_by_role("link", name="Casey Jordan", exact=True).click()
    expect(page.get_by_role("article", name="Temperature", exact=True)).to_contain_text(
        "Unavailable"
    )
    role(page, "patient")
    channel(page, "/messages")
    page.get_by_text("Demo testing tools", exact=True).click()
    page.get_by_role("button", name="Test next submission failure", exact=True).click()
    page.get_by_role("textbox", name="Your message", exact=True).fill("Fictional retry")
    page.get_by_role("button", name="Send message", exact=True).click()
    expect(page.get_by_role("alert")).to_contain_text("Simulated submission failed")
    expect(page.get_by_role("textbox", name="Your message", exact=True)).to_have_value(
        "Fictional retry"
    )
    page.get_by_role("button", name="Send message", exact=True).click()
    expect(page.get_by_text("Fictional retry", exact=True)).to_have_count(1)


def test_staff_controls_help_alerts_and_admin(page):
    page.goto("/")
    # Native keyboard operation and the CSS animation control work without scripts.
    page.keyboard.press("Tab")
    expect(page.get_by_label("Pause decorative animation", exact=True)).to_be_focused()
    page.keyboard.press("Space")
    expect(page.get_by_label("Pause decorative animation", exact=True)).to_be_checked()
    page.get_by_role("button", name="Demo patient", exact=True).click()
    Path("test-results").mkdir(exist_ok=True)
    page.screenshot(path="test-results/flask-patient-desktop.png", full_page=True)
    page.get_by_role("button", name="Request assistance", exact=True).click()
    channel(page, "/messages")
    expect(page.get_by_text("I need assistance, please.", exact=True)).to_be_visible()
    page.get_by_role("button", name="Mark staff replies read", exact=True).click()
    role(page, "staff")
    page.screenshot(path="test-results/flask-staff-desktop.png", full_page=True)
    page.get_by_role("navigation").get_by_role("link", name="Alerts", exact=True).click()
    help_alert = page.get_by_role("article").filter(has_text="I need assistance, please.")
    help_alert.get_by_role("button", name="Acknowledge", exact=True).click()
    page.get_by_role("link", name="Acknowledged", exact=True).click()
    expect(page.get_by_text("Acknowledged by Demo staff", exact=False)).to_be_visible()
    page.get_by_role("navigation").get_by_role("link", name="Patients", exact=True).click()
    page.get_by_label("Search patients", exact=True).fill("Alex")
    page.get_by_role("button", name="Apply filters", exact=True).click()
    expect(page.get_by_role("link", name="Sam Taylor", exact=True)).to_have_count(0)
    page.get_by_role("link", name="Alex Morgan", exact=True).click()
    page.get_by_label("Review / override reason", exact=True).fill("Fictional staff review")
    page.get_by_role("button", name="Record staff decision", exact=True).click()
    expect(page.get_by_text("Staff decision: Staff review complete.", exact=False)).to_be_visible()
    page.get_by_label("Confirmed department / waiting area", exact=True).fill("Demo waiting area B")
    page.get_by_role("button", name="Confirm destination", exact=True).click()
    page.get_by_label("New staff note", exact=True).fill("Fictional review note")
    page.get_by_role("button", name="Add note", exact=True).click()
    expect(page.get_by_text("Fictional review note", exact=False)).to_be_visible()
    page.get_by_role("link", name="Open conversation", exact=True).click()
    page.get_by_role("button", name="Mark general/help reviewed", exact=True).click()
    role(page, "patient")
    expect(page.get_by_text("Demo waiting area B", exact=True)).to_be_visible()
    role(page, "admin")
    page.get_by_role("link", name="Manage profiles", exact=True).click()
    page.get_by_label("Name", exact=True).fill("Fictional Colleague")
    page.get_by_label("Work email (fictional)", exact=True).fill("colleague@example.test")
    page.get_by_label("Role", exact=True).select_option("staff")
    page.get_by_role("button", name="Create demo profile", exact=True).click()
    colleague = page.locator(".inbox-row").filter(has_text="Fictional Colleague")
    colleague.get_by_role("button", name="Deactivate", exact=True).click()
    expect(colleague).to_contain_text("Inactive")
    colleague.get_by_role("button", name="Activate", exact=True).click()
    expect(colleague).to_contain_text("Active")
    page.get_by_role("button", name="Reset this browser's demo", exact=True).click()
    expect(page.get_by_text("Fictional Colleague", exact=True)).to_have_count(0)


def test_assisted_registration_filters_and_device_options(page):
    page.goto("/")
    page.get_by_role("button", name="Demo staff", exact=True).click()
    page.get_by_role("link", name="Register patient", exact=True).click()
    expect(page.get_by_label("Email", exact=True)).to_have_count(0)
    page.get_by_label("Full name", exact=True).fill("Fictional Assisted Patient")
    page.get_by_label("Date of birth", exact=True).fill("1990-02-01")
    page.get_by_role("button", name="Create patient reference", exact=True).click()
    page.get_by_role("button", name="Leeds General Infirmary", exact=True).click()
    page.get_by_role("link", name="Record intake", exact=True).click()
    page.get_by_label("Reason for attending", exact=True).fill("Fictional attendance")
    page.get_by_label("Symptoms", exact=True).fill("Fictional symptoms")
    page.get_by_label("When did symptoms start?", exact=True).fill("Today")
    page.get_by_role("button", name="Review information", exact=True).click()
    page.get_by_role("button", name="Submit intake", exact=True).click()
    page.get_by_role("button", name="Confirm arrival", exact=True).click()
    page.get_by_label("Available band", exact=True).select_option("PB-013")
    page.get_by_role("button", name="Assign band", exact=True).click()
    page.get_by_role("navigation").get_by_role("link", name="Patients", exact=True).click()
    page.get_by_label("Search patients", exact=True).fill("Fictional Assisted")
    page.get_by_role("button", name="Apply filters", exact=True).click()
    expect(page.get_by_role("row").filter(has_text="Fictional Assisted")).to_contain_text(
        "Awaiting first simulated reading"
    )
    page.get_by_label("Search patients", exact=True).fill("Nobody matches this")
    page.get_by_role("button", name="Apply filters", exact=True).click()
    expect(page.get_by_text("No matching patients.", exact=True)).to_be_visible()
    page.get_by_role("navigation").get_by_role("link", name="Devices", exact=True).click()
    for section in page.locator(".three-grid section").all():
        section.get_by_text("Integration details", exact=True).click()
        expect(section).to_contain_text("No vendor passwords are collected")


def test_postcode_search_and_selection_on_mobile(page):
    page.set_viewport_size(dict(width=390, height=844))
    page.goto("/")
    page.get_by_role("link", name="Register as a patient", exact=True).click()
    for label, value in {
        "Full name": "Fictional Leeds Patient",
        "Date of birth": "1995-04-12",
        "Email": "leeds@example.test",
        "Password (8 or more characters)": "fictional-only-123",
        "Confirm password": "fictional-only-123",
    }.items():
        page.get_by_label(label, exact=True).fill(value)
    page.get_by_role("button", name="Create demo profile", exact=True).click()
    expect(page.locator("article.hospital")).to_have_count(0)
    page.get_by_label("Enter your postcode", exact=True).fill("LS6 1AA")
    page.get_by_role("button", name="Search hospitals", exact=True).click()
    expect(page.get_by_label("Enter your postcode", exact=True)).to_have_value("LS6")
    hospitals = page.locator("article.hospital")
    expect(hospitals).to_have_count(2)
    expect(hospitals.first).to_contain_text("Leeds General Infirmary")
    expect(hospitals.first).to_contain_text("5–10")
    expect(hospitals.first).to_contain_text("people waiting · simulated")
    expect(hospitals.first).to_contain_text("Estimate unavailable")
    Path("test-results").mkdir(exist_ok=True)
    page.screenshot(path="test-results/postcode-mobile.png", full_page=True)
    main = page.locator("main").bounding_box()
    assert main and main["x"] + main["width"] <= page.viewport_size["width"]
    hospitals.first.get_by_role("button", name="Select hospital", exact=True).click()
    expect(page.get_by_role("heading", name="Tell the team why you are coming.")).to_be_visible()
    page.get_by_role("navigation").get_by_role("link", name="Home", exact=True).click()
    expect(page.get_by_text("Leeds General Infirmary", exact=False)).to_be_visible()
    expect(page.get_by_role("region", name="Waiting duration")).to_contain_text("Not started")


def test_admin_workspace_support_and_mobile(page):
    page.goto("/")
    page.get_by_role("button", name="Demo patient", exact=True).click()
    channel(page, "/support")
    page.get_by_label("Subject", exact=True).fill("Fictional portal question")
    page.get_by_label("Your support message", exact=True).fill("Fictional account support")
    page.get_by_role("button", name="Send support message", exact=True).click()
    role(page, "admin")
    navigation = page.get_by_role("navigation")
    expect(navigation.get_by_role("link", name="Patients", exact=True)).to_have_count(0)
    expect(page.get_by_role("link", name="Register patient", exact=True)).to_have_count(0)
    Path("test-results").mkdir(exist_ok=True)
    page.screenshot(path="test-results/admin-overview-desktop.png", full_page=True)
    channel(page, "/support?audience=patient")
    page.get_by_role("link").filter(has_text="Fictional portal question").click()
    expect(page.get_by_text("Fictional account support", exact=True)).to_be_visible()
    page.get_by_role("button", name="Mark conversation read", exact=True).click()
    page.get_by_label("Your support reply", exact=True).fill("Fictional administrator response")
    page.get_by_role("button", name="Send support reply", exact=True).click()
    role(page, "patient")
    channel(page, "/support")
    page.get_by_role("link").filter(has_text="Fictional portal question").click()
    expect(page.get_by_text("Fictional administrator response", exact=True)).to_be_visible()
    page.get_by_role("button", name="Mark conversation read", exact=True).click()
    role(page, "admin")
    channel(page, "/support?audience=staff")
    page.get_by_label("Subject", exact=True).fill("Fictional staff question")
    page.get_by_label("Your support message", exact=True).fill("Fictional staff equipment support")
    page.get_by_role("button", name="Send support message", exact=True).click()
    role(page, "staff")
    channel(page, "/support")
    page.get_by_role("link").filter(has_text="Fictional staff question").click()
    page.get_by_label("Your support reply", exact=True).fill("Fictional staff response")
    page.get_by_role("button", name="Send support reply", exact=True).click()
    role(page, "admin")
    page.set_viewport_size(dict(width=390, height=844))
    page.screenshot(path="test-results/admin-overview-mobile.png", full_page=True)
    navigation.get_by_role("link", name="Login activity", exact=True).click()
    expect(page.get_by_role("link", name="Download activity CSV", exact=True)).to_be_visible()
    expect(page.get_by_role("cell", name="Demo role entered", exact=True).first).to_be_visible()
    expect(navigation.get_by_role("link", name="Security", exact=True)).to_have_count(0)
    channel(page, "/support?audience=staff")
    page.get_by_role("link").filter(has_text="Fictional staff question").click()
    expect(page.get_by_text("Fictional staff response", exact=True)).to_be_visible()
    page.screenshot(path="test-results/admin-support-mobile.png", full_page=True)
    main = page.locator("main").bounding_box()
    assert main and main["x"] + main["width"] <= page.viewport_size["width"]


def test_garmin_card_no_credentials_no_false_watch_connection(page):
    page.set_viewport_size(dict(width=390, height=844))
    page.goto("/")
    page.get_by_role("button", name="Demo patient", exact=True).click()
    page.get_by_role("navigation").get_by_role("link", name="Devices", exact=True).click()
    card = page.get_by_role("region", name="Garmin Connect", exact=True)
    expect(card).to_contain_text("Not configured")
    expect(card).to_contain_text("Watch connection not verified")
    card.get_by_role("button", name="Check Garmin API access", exact=True).click()
    expect(page.get_by_role("alert")).to_contain_text("Garmin is not configured")
    card.get_by_text("Garmin setup instructions", exact=True).click()
    expect(card).to_contain_text(".secrets/garmin-personal-api-key")
    Path("test-results").mkdir(exist_ok=True)
    page.screenshot(path="test-results/garmin-mobile.png", full_page=True)
    main = page.locator("main").bounding_box()
    assert main and main["x"] + main["width"] <= page.viewport_size["width"]


def test_garmin_synced_preview_with_http_double(page, live_app, monkeypatch):
    from test_garmin_readings import PreviewClient

    monkeypatch.setitem(live_app.extensions, "garmin_access", PreviewClient())
    page.set_viewport_size(dict(width=390, height=844))
    page.goto("/")
    page.get_by_role("button", name="Demo patient", exact=True).click()
    page.get_by_role("navigation").get_by_role("link", name="Devices", exact=True).click()
    page.get_by_role("button", name="Show Garmin readings", exact=True).click()
    expect(
        page.get_by_role("heading", name="Latest synced Garmin readings", exact=True)
    ).to_be_visible()
    expect(page.get_by_role("article", name="Garmin Heart rate", exact=True)).to_contain_text("73")
    expect(
        page.get_by_role("article", name="Garmin daily stress score", exact=True)
    ).to_contain_text("28")
    expect(page.get_by_role("article", name="Garmin Temperature", exact=True)).to_have_count(0)
    expect(
        page.get_by_role("heading", name="Daily heart-rate statistics", exact=True)
    ).to_be_visible()
    page.screenshot(path="test-results/garmin-synced-preview-mobile.png", full_page=True)
    main = page.locator("main").bounding_box()
    assert main and main["x"] + main["width"] <= page.viewport_size["width"]
    page.get_by_role("button", name="Stop and clear Garmin preview", exact=True).click()
    expect(page.get_by_role("heading", name="Devices", exact=True)).to_be_visible()


@pytest.mark.parametrize("width,height", [(1440, 960), (390, 844)])
def test_checked_in_patient_plans_visit_and_opens_history_forms(page, width, height):
    failures = []
    page.on(
        "response",
        lambda response: failures.append(response.url) if response.status >= 500 else None,
    )
    page.set_viewport_size(dict(width=width, height=height))
    page.goto("/")
    page.get_by_role("button", name="Demo patient", exact=True).click()
    page.get_by_role("navigation").get_by_role("link", name="Hospitals", exact=True).click()
    page.get_by_label("Enter your postcode", exact=True).fill("LS6")
    page.get_by_role("button", name="Search hospitals", exact=True).click()
    hospital = page.locator("article.hospital").filter(has_text="St James's University Hospital")
    choose = hospital.get_by_role("button", name="Start a new visit here", exact=True)
    expect(choose).to_be_enabled()
    choose.focus()
    page.keyboard.press("Enter")
    expect(page.get_by_role("heading", name="Tell the team why you are coming.")).to_be_visible()
    reference = page.url.rsplit("/", 1)[-1]
    for label, value in {
        "Reason for attending": "Fictional second attendance",
        "Symptoms": "Second visit original symptoms",
        "When did symptoms start?": "This afternoon",
    }.items():
        page.get_by_label(label, exact=True).fill(value)
    page.get_by_role("button", name="Review information", exact=True).click()
    page.get_by_role("button", name="Edit information", exact=True).click()
    expect(page.get_by_label("Symptoms", exact=True)).to_have_value(
        "Second visit original symptoms"
    )
    page.get_by_role("button", name="Review information", exact=True).click()
    page.get_by_role("button", name="Submit intake", exact=True).click()
    expect(page.get_by_role("region", name="Waiting duration")).to_contain_text("Not started")
    page.get_by_role("navigation").get_by_role("link", name="My visits", exact=True).click()
    expect(page.locator("article.visit-history-card")).to_have_count(2)
    current = page.get_by_role("article", name=f"Visit {reference}", exact=True)
    expect(current).to_contain_text("St James's University Hospital")
    current.get_by_text("View submitted intake form", exact=True).click()
    expect(current.get_by_text("Second visit original symptoms", exact=True)).to_be_visible()
    original = page.get_by_role("article", name="Visit P-2041", exact=True)
    expect(original).to_contain_text("monitoring")
    original.get_by_text("View submitted intake form", exact=True).click()
    expect(original.get_by_text("Dizziness and tiredness", exact=True)).to_be_visible()
    main = page.locator("main").bounding_box()
    assert main and main["x"] + main["width"] <= width
    Path("test-results").mkdir(exist_ok=True)
    page.screenshot(path=f"test-results/visit-history-{width}.png", full_page=True)
    original.get_by_role("link", name="View visit", exact=True).click()
    expect(page.get_by_role("region", name="Waiting duration")).not_to_contain_text("Not started")
    page.get_by_role("link", name="View all my visits", exact=True).click()
    current.get_by_role("link", name="View visit", exact=True).click()
    role(page, "staff")
    page.get_by_label("Search patients", exact=True).fill(reference)
    page.get_by_role("button", name="Apply filters", exact=True).click()
    page.get_by_role("link", name="Alex Morgan", exact=True).click()
    page.get_by_role("button", name="Confirm arrival", exact=True).click()
    page.get_by_role("button", name="Close visit / release band", exact=True).click()
    role(page, "patient")
    page.get_by_role("navigation").get_by_role("link", name="My visits", exact=True).click()
    expect(current).to_contain_text("closed")
    current.get_by_text("View submitted intake form", exact=True).click()
    expect(current.get_by_text("Second visit original symptoms", exact=True)).to_be_visible()
    expect(original).to_contain_text("monitoring")
    page.get_by_role("link", name="Plan a new visit", exact=True).click()
    page.get_by_label("Enter your postcode", exact=True).fill("LS6")
    page.get_by_role("button", name="Search hospitals", exact=True).click()
    page.locator("article.hospital").first.get_by_role(
        "button", name="Start a new visit here"
    ).click()
    expect(page.get_by_role("heading", name="Tell the team why you are coming.")).to_be_visible()
    page.get_by_role("navigation").get_by_role("link", name="My visits", exact=True).click()
    expect(page.locator("article.visit-history-card")).to_have_count(3)
    assert failures == []


def test_chat_channels_back_links_and_admin_patient_contact(page):
    page.set_viewport_size(dict(width=390, height=844))
    page.goto("/")
    page.get_by_role("button", name="Demo admin", exact=True).click()
    channel(page, "/support?audience=patient")
    page.get_by_label("Demo patient reference", exact=True).fill("P-2041")
    page.get_by_label("Subject", exact=True).fill("Fictional welcome")
    page.get_by_label("Your support message", exact=True).fill("Fictional portal guidance")
    page.get_by_role("button", name="Send support message", exact=True).click()
    expect(page.get_by_text("Fictional portal guidance", exact=True)).to_be_visible()
    page.get_by_role("link", name="Back to Chat", exact=True).click()
    expect(page.locator(".channel-card")).to_have_count(2)
    Path("test-results").mkdir(exist_ok=True)
    page.screenshot(path="test-results/chat-admin-mobile.png", full_page=True)
    role(page, "patient")
    channel(page, "/support")
    page.get_by_role("link").filter(has_text="Fictional welcome").click()
    expect(page.get_by_text("Fictional portal guidance", exact=True)).to_be_visible()
    page.get_by_role("link", name="Back to Chat", exact=True).click()
    page.screenshot(path="test-results/chat-patient-mobile.png", full_page=True)
    main = page.locator("main").bounding_box()
    assert main and main["x"] + main["width"] <= 390


def test_all_role_navigation_and_admin_download_without_server_errors(page):
    failures = []
    page.on(
        "response",
        lambda response: failures.append(response.url) if response.status >= 500 else None,
    )
    page.goto("/")
    # Real sign-in is explicitly unavailable, and returns a usable page.
    page.get_by_label("Email address", exact=True).fill("fictional@example.test")
    page.get_by_label("Password", exact=True).fill("fictional-password")
    page.get_by_role("button", name="Sign in", exact=True).click()
    expect(page.get_by_text("Real sign-in is not connected.", exact=False)).to_be_visible()
    for role_name in ("patient", "staff", "admin"):
        page.get_by_role("button", name=f"Demo {role_name}", exact=True).click()
        navigation = page.get_by_role("navigation")
        targets = [link.get_attribute("href") for link in navigation.get_by_role("link").all()]
        for path in targets:
            with page.expect_navigation() as navigation_result:
                navigation.locator(f'a[href="{path}"]').click()
            assert navigation_result.value.status == 200, path
            expect(page.get_by_role("heading", level=1)).to_have_count(1)
            expect(page.get_by_role("heading", name="403 · Request unavailable")).to_have_count(0)
        if role_name == "admin":
            navigation.get_by_role("link", name="Login activity", exact=True).click()
            with page.expect_download() as downloaded:
                page.get_by_role("link", name="Download activity CSV", exact=True).click()
            download = downloaded.value
            assert download.suggested_filename == "pulse-demo-activity.csv"
            assert "time,event,actor,detail,outcome" in Path(download.path()).read_text()
        page.get_by_role("button", name="Log out", exact=True).click()
        expect(page.get_by_role("button", name="Demo patient", exact=True)).to_be_visible()
    assert failures == []
