"""Fictional demo records. No database, hardware or model connection."""

from datetime import datetime, timedelta, timezone


def create_fixtures(now=None):
    now = now or datetime.now(timezone.utc)

    def ago(minutes):
        return (now - timedelta(minutes=minutes)).isoformat()

    visits = []
    for reference, name, dob, status, minutes, device, assessment in [
        ("P-2041", "Alex Morgan", "1994-05-14", "monitoring", 47, "PB-012", "completed"),
        ("P-2042", "Jamie Parker", "1986-02-08", "awaiting band", 32, None, "pending"),
        ("P-2043", "Sam Taylor", "2001-09-23", "monitoring", 65, "PB-014", "failed"),
        ("P-2044", "Robin Lee", "1978-11-03", "awaiting arrival", None, None, "pending"),
        ("P-2045", "Casey Jordan", "1998-06-12", "monitoring", 19, "SIM-FITBIT", "pending"),
    ]:
        result = {"state": assessment}
        if assessment == "completed":
            result.update(
                category="Clinical review requested",
                explanation="Static synthetic output for demonstration. Staff review required.",
                version="demo-output-v1",
            )
        visits.append(
            dict(
                id=reference,
                patientId=reference,
                created=ago(minutes) if minutes is not None else ago(5),
                name=name,
                dob=dob,
                hospital="leeds-general",
                status=status,
                arrival=ago(minutes) if minutes is not None else None,
                device=device,
                category="Staff review complete" if reference == "P-2043" else "Awaiting review",
                assessment=result,
                intake=dict(
                    reason="Feeling unwell",
                    symptoms="Dizziness and tiredness",
                    onset="This morning",
                    conditions="None reported",
                    allergies="None reported",
                ),
                updates=[],
                notes=[],
                destination=None,
                estimate=None,
                email=None,
            )
        )
    source = "Pulse band simulator · skin temperature"
    return dict(
        hospitals=[
            dict(
                id="leeds-general",
                name="Leeds General Infirmary",
                address="Emergency Department, Jubilee Wing, Clarendon Way, Leeds LS2 9DA",
                lat=53.803364,
                lon=-1.553459,
                waiting=7,
                waitingLabel="5–10",
                updated=ago(4),
                source="Synthetic demo feed — not hospital-supplied counts",
                estimate=None,
                region="Leeds",
                careNote="Children's Emergency Department is located at this site.",
            ),
            dict(
                id="st-james",
                name="St James's University Hospital",
                address="Emergency Department, Chancellors Wing, Leeds LS9 7TF",
                lat=53.806885,
                lon=-1.520363,
                waiting=17,
                waitingLabel="15–20",
                updated=ago(6),
                source="Synthetic demo feed — not hospital-supplied counts",
                estimate=None,
                region="Leeds",
                careNote="No emergency department for children under 16 at this site.",
            ),
        ],
        visits=visits,
        readings={
            "P-2041": [
                dict(temperature=36.6, heartRate=78, time=ago(2), source=source),
                dict(temperature=36.5, heartRate=80, time=ago(6), source=source),
            ],
            "P-2043": [dict(temperature=36.8, heartRate=84, time=ago(38), source=source)],
            "P-2045": [
                dict(
                    temperature=None,
                    heartRate=74,
                    time=ago(3),
                    source="Simulated Fitbit · heart rate only",
                )
            ],
        },
        devices=[
            dict(id="PB-012", type="Pulse band", visit="P-2041", connection="Connected"),
            dict(id="PB-013", type="Pulse band", visit=None, connection="Available"),
            dict(id="PB-014", type="Pulse band", visit="P-2043", connection="Disconnected"),
            dict(id="PB-015", type="Pulse band", visit=None, connection="Available"),
            dict(
                id="SIM-FITBIT", type="Fitbit (simulated)", visit="P-2045", connection="Simulated"
            ),
        ],
        messages=[
            dict(
                id="m1",
                visit="P-2041",
                sender="patient",
                text="Could I have some water, please?",
                kind="general",
                time=ago(8),
                reviewed=None,
                read=False,
            ),
            dict(
                id="m2",
                visit="P-2041",
                sender="staff",
                text="A member of the team will come and speak with you.",
                kind="general",
                time=ago(5),
                reviewed=dict(by="Demo staff", time=ago(5)),
                read=False,
            ),
        ],
        alerts=[
            dict(
                id="a1",
                visit="P-2043",
                kind="device",
                text="Band disconnected; readings are stale. Check device connection.",
                source="Synthetic device event",
                time=ago(30),
                ack=None,
            )
        ],
        staff=[
            dict(
                id="s1", name="Jordan Ellis", email="jordan@example.test", role="staff", active=True
            ),
            dict(
                id="s-admin",
                name="Demo administrator",
                email="admin@example.test",
                role="admin",
                active=True,
            ),
        ],
    )
