"""Script-free app and proposed teammate output mapping. Notebook/SQL are not executed."""

from pathlib import Path
import re

from conftest import post
from pulse.ai_mapping import map_notebook_review


def test_application_has_no_authored_javascript():
    for directory in ("pulse", "templates", "static", "tests"):
        assert not [
            p for p in Path(directory).rglob("*") if p.suffix in {".js", ".jsx", ".ts", ".tsx"}
        ]
    for path in Path("templates").glob("*.html"):
        assert not re.search(
            r"<script\b|\bon[a-z]+\s*=|javascript:", path.read_text(encoding="utf-8"), re.I
        ), path


def test_hospitals_start_with_search_instead_of_preloaded_results(client):
    post(client, "/demo/patient")
    response = client.get("/hospitals")
    assert response.status_code == 200
    assert b"Enter your postcode" in response.data
    assert b"Search hospitals" in response.data
    assert b'<article class="panel hospital">' not in response.data
    assert b"Riverside" not in response.data and b"Northgate" not in response.data
    assert b"Show area" not in response.data and b"map-placeholder" not in response.data
    assert b"<script" not in response.data
    assert b'<article class="panel hospital">' not in client.get("/hospitals?area=unknown").data


def test_notebook_mapping_preserves_supplied_score_without_inventing_priority():
    result = map_notebook_review(
        dict(
            stay_id=123,
            charttime="2026-10-24T10:00:00Z",
            heartrate=78,
            o2sat=97,
            anomaly_score=-0.03,
            demo_flag=True,
            missing_sensor_data=False,
            dashboard_message="Unusual pattern; review observation",
        )
    )
    assert result["datasetStayId"] == "123"
    assert result["anomalyScore"] == -0.03 and result["demoFlag"] is True
    assert result["missingSensorData"] is False
    assert not ({"visitId", "priority", "diagnosis", "confidence", "estimate"} & result.keys())


def test_notebook_mapping_does_not_replace_missing_values_with_zero_or_normal():
    result = map_notebook_review(
        dict(heartrate=" ", o2sat=None, anomaly_score="", demo_flag="false")
    )
    assert result["heartRate"] is None
    assert result["anomalyScore"] is None and result["demoFlag"] is None
    assert result["dashboardMessage"] is None and result["missingSensorData"] is True
