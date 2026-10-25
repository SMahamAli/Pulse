"""Official DTO mapping and local owner preview; all values/credentials synthetic."""

from datetime import datetime, timedelta, timezone
from io import BytesIO
import json
from urllib.error import HTTPError

import pytest

from conftest import post, service_for
from pulse.garmin import GarminAccess, TOKEN_URL
from pulse.garmin_mapping import map_readings
from test_garmin import TEST_KEY, token


def payloads(now):
    return dict(
        heartRateValueDescriptors=[dict(index=1, key="timestamp"), dict(index=0, key="heartrate")],
        heartRateValues=[
            [73, (now - timedelta(minutes=2)).timestamp() * 1000],
            [None, (now - timedelta(minutes=3)).timestamp() * 1000],
            [70, (now - timedelta(minutes=4)).timestamp() * 1000],
        ],
        minHeartRate=52,
        maxHeartRate=115,
        restingHeartRate=58,
    )


def test_descriptor_mapping_latest_stats_timestamp_and_gaps():
    now = datetime.now(timezone.utc)
    result = map_readings(payloads(now), now.date().isoformat(), now)
    assert result["heartRate"] == 73
    assert result["stats"] == dict(minimum=52, maximum=115, resting=58)
    assert result["history"][1]["heartRate"] is None
    assert result["stress"] is None
    assert "temperature" not in result
    assert result["heartTime"] == (now - timedelta(minutes=2)).isoformat()


def test_missing_descriptors_future_and_invalid_values_are_not_invented():
    now = datetime.now(timezone.utc)
    heart = payloads(now)
    heart["heartRateValues"] += [[100, (now + timedelta(hours=1)).timestamp() * 1000], [False, 0]]
    result = map_readings(heart, "2026-10-24", now)
    assert result["heartRate"] == 73
    heart["heartRateValueDescriptors"] = None
    assert map_readings(heart, "2026-10-24", now)["heartRate"] is None


@pytest.mark.parametrize(
    "value,expected",
    [
        (0, 0),
        (28, 28),
        (100, 100),
        (-1, None),
        (101, None),
        (None, None),
        (True, None),
        ("28", None),
    ],
)
def test_daily_stress_maps_only_valid_vendor_scores(value, expected):
    now = datetime.now(timezone.utc)
    day = now.date().isoformat()
    stress = [{"calendarDate": day, "values": {"overallStressLevel": value}}]
    result = map_readings(payloads(now), day, now, stress=stress)
    assert result["stress"] == expected
    assert result["stressDate"] == (day if expected is not None else None)
    assert result["stressFetchedAt"] == (now.isoformat() if expected is not None else None)
    assert "stressTime" not in result  # No individual measurement timestamp in this endpoint.


def test_stress_from_another_date_is_not_attached_to_selected_day():
    result = map_readings(
        {},
        "2026-10-25",
        stress=[{"calendarDate": "2026-10-24", "values": {"overallStressLevel": 30}}],
    )
    assert result["stress"] is None and result["stressDate"] is None


def test_stress_failure_preserves_available_heart_rate_and_sanitizes_errors():
    class MissingStress(DataServer):
        def open(self, request, timeout):
            if "/stats/stress/" in request.full_url:
                self.calls.append(request.full_url)
                raise HTTPError(request.full_url, 403, TEST_KEY, {}, None)
            return super().open(request, timeout)

    access = GarminAccess(environment={"GARMIN_PERSONAL_API_KEY": TEST_KEY}, opener=MissingStress())
    result = access.readings(datetime.now(timezone.utc).date().isoformat())
    assert result["heartRate"] == 73 and result["stress"] is None
    assert result["errors"] == ["Stress: Garmin returned HTTP 403; no new measurement available."]
    assert TEST_KEY not in str(result)


class DataServer:
    def __init__(self, reading_status=None):
        self.calls = []
        self.reading_status = reading_status
        self.bearer = token()

    def open(self, request, timeout):
        self.calls.append(request.full_url)
        assert request.full_url.startswith("https://personal.connectapi.garmin.com/")
        if request.full_url == TOKEN_URL:
            assert request.get_header("Authorization") == f"ApiKey {TEST_KEY}"
            return BytesIO(self.bearer.encode())
        assert request.get_header("Authorization") == f"Bearer {self.bearer}"
        heart = payloads(datetime.now(timezone.utc))
        if self.reading_status:
            raise HTTPError(request.full_url, self.reading_status, TEST_KEY, {}, None)
        if "/stats/stress/" in request.full_url:
            heart = [
                {
                    "calendarDate": datetime.now(timezone.utc).date().isoformat(),
                    "values": {"overallStressLevel": 28},
                }
            ]
        return BytesIO(json.dumps(heart).encode())


def test_read_transport_reuses_token_only_in_server_memory(tmp_path):
    server = DataServer()
    access = GarminAccess(environment={"GARMIN_PERSONAL_API_KEY": TEST_KEY}, opener=server)
    day = datetime.now(timezone.utc).date().isoformat()
    assert access.readings(day)["heartRate"] == 73
    assert access.readings(day)["heartRate"] == 73
    assert server.calls.count(TOKEN_URL) == 1
    assert len(server.calls) == 5
    assert list(tmp_path.iterdir()) == []
    access.clear()
    assert access._bearer is None


def test_partial_data_and_revocation_never_expose_key():
    access = GarminAccess(environment={"GARMIN_PERSONAL_API_KEY": TEST_KEY}, opener=DataServer(403))
    result = access.readings(datetime.now(timezone.utc).date().isoformat())
    assert result["heartRate"] is None
    assert "HTTP 403" in result["errors"][0] and TEST_KEY not in str(result)
    access.opener = DataServer(401)
    access.clear()
    with pytest.raises(ValueError, match="revoked") as error:
        access.readings(datetime.now(timezone.utc).date().isoformat())
    assert TEST_KEY not in str(error.value) and access._bearer is None


def test_rate_limit_pauses_further_vendor_requests():
    server = DataServer(429)
    access = GarminAccess(environment={"GARMIN_PERSONAL_API_KEY": TEST_KEY}, opener=server)
    for _ in range(2):
        with pytest.raises(ValueError, match="rate-limited"):
            access.readings(datetime.now(timezone.utc).date().isoformat())
    assert len(server.calls) == 2  # Token and HR; cooldown blocks the second refresh.


class PreviewClient:
    def __init__(self):
        self.calls = 0
        self.fail = False

    def configuration(self):
        return "Configured locally"

    def readings(self, day):
        self.calls += 1
        if self.fail:
            raise ValueError("Garmin could not be reached.")
        now = datetime.now(timezone.utc)
        result = map_readings(
            payloads(now),
            day,
            now,
            stress=[{"calendarDate": day, "values": {"overallStressLevel": 28}}],
        )
        result["errors"] = []
        return result

    def clear(self):
        pass


def test_preview_polling_stop_and_no_fake_visit_or_cookie_writes(app, client):
    provider = PreviewClient()
    app.extensions["garmin_access"] = provider
    post(client, "/demo/patient")
    service = service_for(app, client)
    before = service.snapshot()
    response = post(
        client, "/devices/garmin/start", {"date": datetime.now(timezone.utc).date().isoformat()}
    )
    assert b"73" in response.data and b"Daily heart-rate statistics" in response.data
    assert (
        b"Synthetic reading" not in response.data
        and b"Latest synced Garmin readings" in response.data
    )
    assert b'http-equiv="refresh" content="10;' in response.data
    assert b"Daily stress score" in response.data and b"Temperature" not in response.data
    client.get("/devices/garmin/readings")
    assert provider.calls == 1
    service.garmin_attempted = (datetime.now(timezone.utc) - timedelta(seconds=11)).isoformat()
    client.get("/devices/garmin/readings")
    assert provider.calls == 2
    assert service.snapshot() == before
    with client.session_transaction() as session:
        assert "heartRate" not in str(dict(session)) and "spo2" not in str(dict(session))
    original = service.garmin_readings["heartTime"]
    provider.fail = True
    service.garmin_attempted = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    response = client.get("/devices/garmin/readings")
    assert (
        b"Earlier samples remain" in response.data
        and service.garmin_readings["heartTime"] == original
    )
    post(client, "/devices/garmin/stop")
    assert service.garmin_readings is None and service.garmin_day is None


def test_preview_local_and_role_guards_and_invalid_date(app, client):
    post(client, "/demo/admin")
    assert client.get("/devices/garmin/readings").status_code == 403
    post(client, "/demo/patient")
    response = post(client, "/devices/garmin/start", {"date": "invalid"})
    assert b"Choose today or an earlier" in response.data
    assert service_for(app, client).garmin_day is None
    assert (
        client.get(
            "/devices/garmin/readings", environ_overrides={"REMOTE_ADDR": "203.0.113.1"}
        ).status_code
        == 403
    )


def test_default_calendar_date_can_be_submitted_across_local_midnight(app, client, monkeypatch):
    from html.parser import HTMLParser

    class SplitDay(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return cls(2026, 10, 25, 0, 5)
            return cls(2026, 10, 24, 23, 5, tzinfo=timezone.utc).astimezone(tz)

    class DateField(HTMLParser):
        value = None
        maximum = None

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == "input" and attrs.get("name") == "date":
                self.value, self.maximum = attrs["value"], attrs["max"]

    monkeypatch.setattr("pulse.datetime", SplitDay)
    app.extensions["garmin_access"] = PreviewClient()
    post(client, "/demo/patient")
    field = DateField()
    field.feed(client.get("/devices").get_data(as_text=True))
    assert field.value == field.maximum == "2026-10-24"
    response = post(client, "/devices/garmin/start", {"date": field.value})
    assert response.status_code == 200
    assert b"Latest synced Garmin readings" in response.data
    assert service_for(app, client).garmin_day == field.value
