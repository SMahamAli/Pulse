"""Replaceable Python demo service; no second database or competing AI model."""

from copy import deepcopy
from datetime import datetime, date, timezone
from functools import wraps
from threading import RLock
import re

from .fixtures import create_fixtures
from .location import lookup_area, nearby

INTAKE_FIELDS = [
    ("reason", "Reason for attending", True),
    ("symptoms", "Symptoms", True),
    ("onset", "When did symptoms start?", True),
    ("conditions", "Relevant conditions (optional)", False),
    ("allergies", "Allergies (optional)", False),
]
METRICS = [
    dict(key="temperature", label="Temperature", unit="°C"),
    dict(key="heartRate", label="Heart rate", unit="bpm"),
]


def mutation(method):
    """One demo write at a time; not a replacement for database transactions."""

    @wraps(method)
    def wrapped(self, *args, **kwargs):
        with self.lock:
            if self.fail_next:
                self.fail_next = False
                raise ValueError(
                    "Simulated submission failed. Your changes were not saved. Please retry."
                )
            return method(self, *args, **kwargs)

    return wrapped


def validate_profile(profile, patient_account=False):
    name = profile.get("name", "").strip()
    if not name or len(name) > 100:
        raise ValueError("Enter a name (up to 100 characters).")
    try:
        dob = date.fromisoformat(profile.get("dob", ""))
    except ValueError as error:
        raise ValueError("Enter a valid date of birth.") from error
    if dob > date.today():
        raise ValueError("Date of birth cannot be in the future.")
    email = (profile.get("email") or "").strip()
    if patient_account and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise ValueError("Enter a valid email address.")
    return dict(name=name, dob=dob.isoformat(), email=email or None)


class DemoService:
    def __init__(self, clock=None):
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.lock = RLock()
        self.state = create_fixtures(self.clock())
        self.state.update(activity=[], support=[])
        self.serial = 2050
        self.fail_next = False
        self.drafts = {}  # Server memory only, never passwords or cookie payloads.
        self.garmin_check = None  # Metadata only; never API keys, tokens or health data.
        self.garmin_day = None
        self.garmin_readings = None  # Owner preview only; kept out of synthetic visit snapshots.
        self.garmin_attempted = None
        self.garmin_error = None

    def now(self):
        return self.clock().isoformat()

    def next_id(self, prefix):
        self.serial += 1
        return f"{prefix}{self.serial}"

    def visit(self, reference):
        result = next((v for v in self.state["visits"] if v["id"] == reference), None)
        if result is None:
            raise ValueError("Visit not found.")
        return result

    def snapshot(self):
        with self.lock:
            return deepcopy(self.state)

    def patient_visits(self, patient_id):
        """Visit history for one demo patient; separate from the selected visit reference."""
        with self.lock:
            return deepcopy(
                [v for v in reversed(self.state["visits"]) if v["patientId"] == patient_id]
            )

    def nearby_hospitals(self, postcode):
        area = lookup_area(postcode)
        return dict(area=area, hospitals=nearby(self.snapshot()["hospitals"], area))

    def record_activity(self, event, role, detail, outcome="Recorded"):
        """Local demo events only; not a durable identity/security audit log."""
        with self.lock:
            self.state["activity"].insert(
                0,
                dict(
                    time=self.now(),
                    event=event,
                    actor=f"Demo {role or 'visitor'}",
                    detail=detail,
                    outcome=outcome,
                ),
            )
            del self.state["activity"][200:]

    def support_thread(self, identifier, role, patient_id):
        with self.lock:
            thread = next((t for t in self.state["support"] if t["id"] == identifier), None)
            if (
                not thread
                or role not in thread["participants"]
                or (role == "patient" and thread["patientId"] != patient_id)
            ):
                raise ValueError("Support conversation unavailable for this demo role.")
            return deepcopy(thread)

    def support_threads(self, role, patient_id):
        with self.lock:
            return deepcopy(
                [
                    thread
                    for thread in reversed(self.state["support"])
                    if role in thread["participants"]
                    and (role != "patient" or thread["patientId"] == patient_id)
                ]
            )

    @mutation
    def start_support(self, role, patient_id, subject, text, target=None, contact_patient=""):
        if role not in {"patient", "staff", "admin"}:
            raise ValueError("Choose a demo role first.")
        if not subject.strip() or len(subject.strip()) > 100:
            raise ValueError("Enter a subject of up to 100 characters.")
        if not text.strip() or len(text.strip()) > 2000:
            raise ValueError("Enter a support message of up to 2000 characters.")
        if role == "patient":
            self.visit(patient_id)
        identifier = self.next_id("support-")
        target = (target or "staff") if role == "admin" else "admin"
        if target not in ({"patient", "staff"} if role == "admin" else {"admin"}):
            raise ValueError("Choose a supported chat recipient.")
        owner = patient_id if role == "patient" else None
        if role == "admin" and target == "patient":
            owner = contact_patient.strip()
            if not self.patient_visits(owner):
                raise ValueError("Enter a known demo patient reference, for example P-2041.")
        self.state["support"].append(
            dict(
                id=identifier,
                subject=subject.strip(),
                participants=[role, target],
                patientId=owner,
                created=self.now(),
                messages=[dict(role=role, text=text.strip(), time=self.now(), readBy=[role])],
            )
        )
        return identifier

    @mutation
    def reply_support(self, identifier, role, patient_id, text):
        self.support_thread(identifier, role, patient_id)
        if not text.strip() or len(text.strip()) > 2000:
            raise ValueError("Enter a support message of up to 2000 characters.")
        thread = next(t for t in self.state["support"] if t["id"] == identifier)
        thread["messages"].append(
            dict(
                role=role,
                text=text.strip(),
                time=self.now(),
                readBy=[role],
            )
        )

    @mutation
    def read_support(self, identifier, role, patient_id):
        self.support_thread(identifier, role, patient_id)
        thread = next(t for t in self.state["support"] if t["id"] == identifier)
        for message in thread["messages"]:
            if role not in message["readBy"]:
                message["readBy"].append(role)

    def active(self, reference):
        visit = self.visit(reference)
        if visit["status"] == "closed":
            raise ValueError("This visit is closed.")
        return visit

    def alert(self, reference, kind, text, identifier):
        self.state["alerts"].append(
            dict(
                id=identifier,
                visit=reference,
                kind=kind,
                text=text,
                source="Demo workflow event",
                time=self.now(),
                ack=None,
            )
        )

    @mutation
    def register(self, profile):
        profile = validate_profile(profile)
        return self._create_visit(profile)

    def _create_visit(self, profile, patient_id=None):
        """Called inside a mutation lock. Only basic profile fields carry into a new visit."""
        reference = self.next_id("P-")
        self.state["visits"].append(
            dict(
                **profile,
                id=reference,
                patientId=patient_id or reference,
                created=self.now(),
                hospital=None,
                arrival=None,
                status="awaiting arrival",
                device=None,
                intake=None,
                updates=[],
                notes=[],
                category="Awaiting review",
                assessment=dict(state="pending"),
                destination=None,
                estimate=None,
            )
        )
        return reference

    @mutation
    def plan_visit(self, reference, hospital):
        """Choose an intake draft, preserving submitted/checked-in/closed visit records."""
        current = self.visit(reference)
        if not any(h["id"] == hospital for h in self.state["hospitals"]):
            raise ValueError("Choose a listed hospital.")
        draft = next(
            (
                v
                for v in reversed(self.state["visits"])
                if v["patientId"] == current["patientId"]
                and not v["arrival"]
                and not v["intake"]
                and v["status"] != "closed"
            ),
            None,
        )
        if draft is None:
            profile = {key: current.get(key) for key in ("name", "dob", "email")}
            draft = self.visit(self._create_visit(profile, current["patientId"]))
        draft["hospital"] = hospital
        return draft["id"]

    @mutation
    def select_hospital(self, reference, hospital):
        visit = self.active(reference)
        if visit["arrival"]:
            raise ValueError("Hospital selection is locked after check-in. Speak to staff.")
        if not any(h["id"] == hospital for h in self.state["hospitals"]):
            raise ValueError("Choose a listed hospital.")
        visit["hospital"] = hospital

    @mutation
    def submit_intake(self, reference, intake):
        visit = self.active(reference)
        if not visit["hospital"]:
            raise ValueError("Choose a hospital before completing intake.")
        if visit["intake"]:
            raise ValueError("Original intake already submitted. Use a symptom update.")
        if any(not intake.get(key, "").strip() for key, _, required in INTAKE_FIELDS if required):
            raise ValueError("Complete the reason, symptoms and onset fields.")
        visit["intake"] = dict(deepcopy(intake), submitted=self.now())
        visit["assessment"] = dict(state="pending")

    @mutation
    def check_in(self, reference):
        visit = self.active(reference)
        if not visit["hospital"] or not visit["intake"]:
            raise ValueError("Select a hospital and complete intake first.")
        if not visit["arrival"]:
            visit.update(arrival=self.now(), status="awaiting band")

    @mutation
    def assign(self, reference, device_id):
        visit = self.active(reference)
        if not visit["arrival"]:
            raise ValueError("Confirm arrival before assigning a band.")
        if visit["device"]:
            raise ValueError("Visit already has a device.")
        device = next((d for d in self.state["devices"] if d["id"] == device_id), None)
        if not device or device["visit"] or device["type"] != "Pulse band":
            raise ValueError("Band is already assigned or unavailable.")
        device.update(visit=reference, connection="Awaiting data")
        visit.update(device=device_id, status="monitoring")

    @mutation
    def message(self, reference, text, kind="general", sender="patient"):
        self.active(reference)
        text = text.strip()
        if not text or len(text) > 2000:
            raise ValueError("Enter a message of up to 2000 characters.")
        if kind not in {"general", "help"} or sender not in {"patient", "staff"}:
            raise ValueError("Unsupported message type.")
        identifier = self.next_id("m")
        self.state["messages"].append(
            dict(
                id=identifier,
                visit=reference,
                text=text,
                kind=kind,
                sender=sender,
                time=self.now(),
                reviewed=dict(by="Demo staff", time=self.now()) if sender == "staff" else None,
                read=False,
            )
        )
        if kind == "help" and sender == "patient":
            self.alert(reference, "help", text, identifier)

    @mutation
    def symptom(self, reference, description, onset):
        visit = self.active(reference)
        if not description.strip() or not onset.strip():
            raise ValueError("Describe the change and when it started.")
        if len(description) > 2000 or len(onset) > 2000:
            raise ValueError("Keep each symptom field within 2000 characters.")
        identifier = self.next_id("u")
        update = dict(
            id=identifier,
            description=description.strip(),
            onset=onset.strip(),
            time=self.now(),
            reviewed=None,
        )
        visit["updates"].append(update)
        visit["assessment"] = dict(state="pending")
        self.state["messages"].append(
            dict(
                id=identifier,
                visit=reference,
                text=f"{description.strip()} · Started/changed: {onset.strip()}",
                kind="symptom",
                sender="patient",
                time=update["time"],
                reviewed=None,
                read=False,
            )
        )
        self.alert(reference, "symptom", description.strip(), identifier)

    @mutation
    def review(self, reference, update_id=None):
        visit = self.visit(reference)
        stamp = dict(by="Demo staff · Jordan Ellis", time=self.now())
        if update_id:
            update = next((u for u in visit["updates"] if u["id"] == update_id), None)
            if not update:
                raise ValueError("Symptom update not found.")
            update["reviewed"] = stamp
        for message in self.state["messages"]:
            if (
                message["visit"] == reference
                and message["sender"] == "patient"
                and (not update_id or message["id"] == update_id)
                and (update_id or message["kind"] != "symptom")
            ):
                message["reviewed"] = stamp

    @mutation
    def mark_read(self, reference):
        for message in self.state["messages"]:
            if message["visit"] == reference and message["sender"] == "staff":
                message["read"] = True

    @mutation
    def note(self, reference, text):
        if not text.strip():
            raise ValueError("Enter a note.")
        self.visit(reference)["notes"].append(
            dict(text=text.strip(), by="Demo staff", time=self.now())
        )

    @mutation
    def decision(self, reference, category, reason):
        if not category.strip() or not reason.strip():
            raise ValueError("Enter a staff category and review / override reason.")
        visit = self.visit(reference)
        visit["category"] = category.strip()
        visit["notes"].append(
            dict(
                text=f"Staff decision: {category.strip()}. Reason: {reason.strip()}",
                by="Demo staff",
                time=self.now(),
            )
        )

    @mutation
    def destination(self, reference, text):
        if not text.strip():
            raise ValueError("Enter a confirmed department / waiting area.")
        self.visit(reference)["destination"] = dict(
            text=text.strip(), by="Demo staff", time=self.now()
        )

    @mutation
    def close(self, reference):
        visit = self.visit(reference)
        if visit["device"]:
            device = next(d for d in self.state["devices"] if d["id"] == visit["device"])
            device.update(visit=None, connection="Available")
        if visit["status"] != "closed":
            visit["closedAt"] = self.now()
        visit.update(status="closed", device=None)

    @mutation
    def acknowledge(self, identifier):
        alert = next((a for a in self.state["alerts"] if a["id"] == identifier), None)
        if not alert:
            raise ValueError("Alert not found.")
        if not alert["ack"]:
            alert["ack"] = dict(by="Demo staff", time=self.now())

    @mutation
    def add_staff(self, name, email, role):
        email = email.strip().lower()
        if (
            not name.strip()
            or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email)
            or role not in {"staff", "admin"}
        ):
            raise ValueError("Enter a name, valid fictional email and supported role.")
        if any(s["email"].lower() == email for s in self.state["staff"]):
            raise ValueError("A demo profile already uses that email.")
        self.state["staff"].append(
            dict(
                id=self.next_id("s"), name=name.strip(), email=email.strip(), role=role, active=True
            )
        )
        self.record_activity("Profile created", "admin", f"Created demo {role} profile")

    @mutation
    def toggle_staff(self, identifier):
        staff = next((s for s in self.state["staff"] if s["id"] == identifier), None)
        if not staff:
            raise ValueError("Staff profile not found.")
        staff["active"] = not staff["active"]
        self.record_activity(
            "Profile status changed",
            "admin",
            f"{staff['id']}: {'Activated' if staff['active'] else 'Deactivated'}",
        )

    @mutation
    def tick(self):
        for visit in self.state["visits"]:
            device = next((d for d in self.state["devices"] if d["id"] == visit["device"]), None)
            if (
                visit["status"] != "monitoring"
                or not device
                or device["connection"] not in {"Connected", "Awaiting data"}
            ):
                continue
            device["connection"] = "Connected"
            self.serial += 1
            reading = dict(
                temperature=round(36.5 + (self.serial % 3) / 10, 1),
                heartRate=76 + self.serial % 8,
                time=self.now(),
                source="Pulse band simulator · skin temperature",
            )
            self.state["readings"][visit["id"]] = [
                reading,
                *self.state["readings"].get(visit["id"], []),
            ][:12]


class AssessmentService:
    """Replace with Elysha's agreed job API; never invent a completed assessment."""

    def request(self, _inputs):
        return dict(state="pending")
