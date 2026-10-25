"""Map Maham's Oracle view fields to display fields; never modify the schema."""

import math


def field(row, name):
    return row.get(name, row.get(name.upper()))


def number(value):
    if value is None or isinstance(value, bool) or not str(value).strip():
        return None
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (ValueError, TypeError):
        return None


def identifier(value):
    return str(value) if value is not None else None


def map_latest_vitals(row):
    return dict(
        patientId=identifier(field(row, "patient_id")),
        assignmentId=identifier(field(row, "assignment_id")),
        temperature=number(field(row, "skin_temp")),
        heartRate=number(field(row, "heart_rate")),
        time=field(row, "recorded_at"),
        source="Pulse database · wristband skin temperature",
    )


def map_current_patient(row):
    return dict(
        databasePatientId=identifier(field(row, "patient_id")),
        name=" ".join(str(v) for v in [field(row, "forename"), field(row, "surname")] if v),
        age=number(field(row, "age")),
        arrival=field(row, "arrival_time"),
        presentingComplaint=field(row, "presenting_complaint"),
        databaseStatus=field(row, "status"),
        recordedTriage=field(row, "triage"),
        recordedZone=field(row, "zone_name"),
        assignmentId=identifier(field(row, "assignment_id")),
        deviceId=identifier(field(row, "device_id")),
    )


def map_open_alert(row):
    return dict(
        id=identifier(field(row, "alert_id")),
        databasePatientId=identifier(field(row, "patient_id")),
        patientName=field(row, "patient_name"),
        recordedZone=field(row, "zone_name"),
        databaseType=field(row, "alert_type"),
        suppliedSeverity=field(row, "severity"),
        text=field(row, "message"),
        time=field(row, "triggered_at"),
        databaseStatus=field(row, "status"),
        acknowledgedBy=str(field(row, "acknowledged_by") or "").strip() or None,
        acknowledgedAt=None,
    )
