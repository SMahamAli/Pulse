"""Teammate model execution, source isolation and website research-preview boundaries."""

import pytest

from conftest import post, service_for
from pulse.assessment import MODEL_SCRIPT, ResearchAssessment


@pytest.fixture(scope="module")
def fitted_research():
    pytest.importorskip("sklearn", reason="Install requirements-ai.txt to run actual model checks")
    pytest.importorskip("pandas")
    original = MODEL_SCRIPT.read_bytes()
    research = ResearchAssessment()
    research.prepare()
    assert research.status()["state"] == "ready", research.status()
    assert MODEL_SCRIPT.read_bytes() == original
    return research


def test_teammate_pipeline_predicts_held_out_rows_without_outcome_fields(fitted_research):
    research = fitted_research
    identifier = research.examples()[0]
    index = research.bundle["examples"][identifier]
    row = research.bundle["rows"].loc[[index]]
    expected = research.bundle["model"].predict(row)[0]
    result = research.predict(identifier)
    assert result["state"] == "completed" and result["flagged"] == bool(expected)
    assert result["datasetId"] == identifier and result["revision"]
    assert not {"urgent_reassessment_required", "patient_id"}.intersection(row.columns)
    assert not {"confidence", "priority", "diagnosis", "department"}.intersection(result)
    evaluation = research.status()["evaluation"]
    assert evaluation["testExamples"] == len(research.bundle["rows"])
    assert 0 <= evaluation["positiveExamplesFlagged"] <= evaluation["positiveExamples"]
    pipeline = research.bundle["model"]
    research.prepare()
    assert research.bundle["model"] is pipeline  # No training on refresh or repeated preparation.


@pytest.mark.parametrize("identifier", ["P-2041", "1000", "SYN2-UNKNOWN", ""])
def test_live_or_invented_identifiers_are_not_research_examples(fitted_research, identifier):
    with pytest.raises(ValueError, match="listed synthetic"):
        fitted_research.predict(identifier)


def test_missing_dependencies_show_setup_instead_of_fabricating_results():
    def missing(_path):
        raise ImportError("deliberately unavailable")

    research = ResearchAssessment(runner=missing)
    research.prepare()
    assert research.status()["state"] == "failed"
    assert "requirements-ai.txt" in research.status()["error"]
    assert research.examples() == []
    with pytest.raises(ValueError, match="Prepare"):
        research.predict("SYN2-00001")


def test_training_failure_can_be_retried_without_exposing_exception_details():
    calls = []

    def broken(_path):
        calls.append(1)
        raise RuntimeError("private server detail")

    research = ResearchAssessment(runner=broken)
    research.prepare()
    research.prepare()
    assert len(calls) == 2
    assert research.status()["state"] == "failed"
    assert "private server detail" not in research.status()["error"]


@pytest.mark.parametrize("role", ["patient", "admin"])
def test_research_preview_is_not_available_to_other_demo_roles(client, role):
    post(client, "/demo/" + role)
    assert client.get("/staff/ai").status_code == 403
    assert post(client, "/staff/ai", {"action": "prepare"}).status_code == 403


def test_preview_renders_real_result_without_changing_visit_decisions(app, client, fitted_research):
    app.extensions["research_assessment"] = fitted_research
    post(client, "/demo/staff")
    service = service_for(app, client)
    before = service.snapshot()["visits"]
    page = client.get("/staff/ai")
    assert b"Back to Home" in page.data
    assert b"fictional toy risk score" in page.data
    assert b"Held-out model check" in page.data
    if fitted_research.status()["evaluation"]["positiveExamplesFlagged"] == 0:
        assert b"flagged none of the positive-labelled examples" in page.data
    identifier = fitted_research.examples()[0]
    result = post(client, "/staff/ai", {"action": "predict", "example": identifier})
    assert identifier.encode() in result.data
    assert b"Research prediction result" in result.data and b"completed" in result.data
    assert service.snapshot()["visits"] == before
    rejected = post(client, "/staff/ai", {"action": "predict", "example": "P-2041"})
    assert b"listed synthetic research example" in rejected.data
    assert b'aria-label="Research prediction result"' not in rejected.data


def test_preview_requires_csrf_and_does_not_train_on_get(app, client):
    post(client, "/demo/staff")
    assert client.get("/staff/ai").status_code == 200
    assert app.extensions["research_assessment"].state == "not prepared"
    assert client.post("/staff/ai", data={"action": "prepare"}).status_code == 400


@pytest.mark.browser
def test_model_browser_preview_on_mobile_without_javascript(fitted_research):
    from threading import Thread

    from playwright.sync_api import expect, sync_playwright
    from werkzeug.serving import make_server

    from pulse import create_app

    app = create_app({"TESTING": True})
    app.extensions["research_assessment"] = fitted_research
    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(
                viewport={"width": 390, "height": 844}, java_script_enabled=False
            )
            page.route("https://fonts.googleapis.com/**", lambda route: route.abort())
            page.goto(f"http://127.0.0.1:{server.server_port}/")
            page.get_by_role("button", name="Demo staff", exact=True).click()
            page.get_by_role("navigation").get_by_role("link", name="AI research").click()
            page.get_by_role("button", name="Run research prediction").click()
            expect(page.get_by_role("region", name="Research prediction result")).to_be_visible()
            assert page.locator("body").evaluate("e => e.scrollWidth <= innerWidth")
            browser.close()
    finally:
        server.shutdown()
        thread.join(timeout=5)
