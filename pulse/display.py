"""Display helpers used by templates and tested directly in Python."""

from datetime import datetime, timezone
import math

STALE_MINUTES = 15  # Demo freshness setting, not a clinical threshold.


def parse_time(value):
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return result if result.tzinfo else result.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError, AttributeError):
        return None


def format_time(value, full=False):
    parsed = parse_time(value)
    return (
        parsed.strftime("%d/%m/%Y, %H:%M UTC" if full else "%H:%M UTC")
        if parsed
        else "Not available"
    )


def waiting_minutes(arrival, now=None):
    parsed = parse_time(arrival)
    return (
        max(0, int(((now or datetime.now(timezone.utc)) - parsed).total_seconds() // 60))
        if parsed
        else None
    )


def waiting(arrival, closed_at=None):
    minutes = waiting_minutes(arrival, parse_time(closed_at))
    return "Not started" if minutes is None else f"{minutes} min"


def device_status(device, readings=(), now=None):
    """Describe demo evidence, never claim a physical hardware connection."""
    if not device or not device.get("visit"):
        return "Unassigned"
    if device["connection"] == "Disconnected":
        return "Demo · Disconnected"
    if not readings:
        return "Awaiting first simulated reading"
    timestamp = parse_time(readings[0].get("time"))
    now = now or datetime.now(timezone.utc)
    if not timestamp or timestamp > now:
        return "Demo · Reading time unavailable"
    if (now - timestamp).total_seconds() > STALE_MINUTES * 60:
        return "Demo · Stale data"
    return "Simulated wearable" if device["connection"] == "Simulated" else "Demo · Connected"


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def metric_status(reading, key, now=None):
    if not reading or not finite(reading.get(key)):
        return "Unavailable"
    parsed = parse_time(reading.get("time"))
    now = now or datetime.now(timezone.utc)
    if not parsed or parsed > now:
        return "Reading time unavailable"
    return (
        "Stale · check device"
        if (now - parsed).total_seconds() > STALE_MINUTES * 60
        else "Synthetic reading"
    )


def badge_tone(text):
    text = str(text).lower()
    if any(word in text for word in ("failed", "error")):
        return "error"
    if any(
        word in text
        for word in ("stale", "disconnect", "pending", "awaiting", "new symptoms", "review needed")
    ):
        return "warning"
    return (
        "good"
        if any(word in text for word in ("connected", "monitoring", "reviewed", "complete"))
        else ""
    )


def trend(readings, key):
    samples = list(reversed(readings))
    valid = [r for r in samples if finite(r.get(key))]
    if len(valid) < 2:
        return dict(
            count=len(valid),
            path="",
            low=None,
            high=None,
            description="More readings needed for a trend.",
        )
    low, high = min(r[key] for r in valid), max(r[key] for r in valid)
    parts, previous = [], False
    for index, sample in enumerate(samples):
        if not finite(sample.get(key)):
            previous = False
            continue
        x = 8 + index * 284 / (len(samples) - 1)
        y = 30 if low == high else 48 - (sample[key] - low) * 36 / (high - low)
        parts.append(f"{'L' if previous else 'M'}{x:.2f},{y:.2f}")
        previous = True
    return dict(
        count=len(valid),
        path=" ".join(parts),
        low=low,
        high=high,
        description="; ".join(f"{r[key]} at {format_time(r['time'])}" for r in valid),
    )
