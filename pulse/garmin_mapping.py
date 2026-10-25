"""Minimal mapping from Garmin's documented daily heart-rate DTOs."""

from datetime import datetime, timezone

from .display import finite, parse_time


def measurement_time(value):
    if finite(value):
        try:
            return datetime.fromtimestamp(value / 1000 if value > 1e12 else value, timezone.utc)
        except (ValueError, OverflowError, OSError):
            return None
    parsed = parse_time(value)
    return parsed.astimezone(timezone.utc) if parsed else None


def map_readings(heart, day, now=None):
    now = now or datetime.now(timezone.utc)
    heart = heart if isinstance(heart, dict) else {}
    columns = {
        d["key"].lower(): d.get("index")
        for d in (heart.get("heartRateValueDescriptors") or [])
        if isinstance(d, dict) and isinstance(d.get("key"), str)
    }
    samples = []
    timestamp_index, value_index = columns.get("timestamp"), columns.get("heartrate")
    if all(
        isinstance(i, int) and not isinstance(i, bool) and i >= 0
        for i in (timestamp_index, value_index)
    ):
        for row in heart.get("heartRateValues") or []:
            if not isinstance(row, list) or len(row) <= max(timestamp_index, value_index):
                continue
            stamp, value = measurement_time(row[timestamp_index]), row[value_index]
            if stamp and stamp <= now:
                samples.append(
                    dict(
                        time=stamp.isoformat(),
                        heartRate=value if finite(value) and value > 0 else None,
                    )
                )
    samples.sort(key=lambda r: r["time"], reverse=True)
    latest = next((sample for sample in samples if sample["heartRate"] is not None), None)

    def statistic(name):
        value = heart.get(name)
        return value if finite(value) and value > 0 else None

    return dict(
        date=day,
        fetchedAt=now.isoformat(),
        heartRate=latest["heartRate"] if latest else None,
        heartTime=latest["time"] if latest else None,
        temperature=None,
        stats=dict(
            minimum=statistic("minHeartRate"),
            maximum=statistic("maxHeartRate"),
            resting=statistic("restingHeartRate"),
        ),
        history=samples[:720],
        source="Garmin Connect Personal API · synced watch data",
    )
