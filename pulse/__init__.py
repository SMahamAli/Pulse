"""Pulse's Flask application, with HTML templates and a replaceable demo service."""

from datetime import datetime, date, timezone
import csv
from io import StringIO
import secrets

from flask import (
    Flask,
    Response,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from . import display
from .garmin import GarminAccess
from .oracle import OracleService
from .services import DemoService, INTAKE_FIELDS, METRICS, validate_profile


def create_app(config=None):
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.update(
        SECRET_KEY=secrets.token_hex(32),
        MAX_CONTENT_LENGTH=64 * 1024,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    app.config.update(config or {})
    app.extensions["demo_services"] = {}
    app.extensions["garmin_access"] = GarminAccess()
    app.extensions["oracle_service"] = OracleService()

    @app.before_request
    def prepare_demo():
        if request.endpoint == "static":
            return
        token = session.setdefault("demo_id", secrets.token_hex(16))
        if token not in app.extensions["demo_services"]:
            app.extensions["demo_services"][token] = DemoService()
        g.service = app.extensions["demo_services"][token]
        session.setdefault("csrf", secrets.token_hex(24))
        session.setdefault("patient_id", "P-2041")
        session.setdefault("patient_owner", session["patient_id"])
        if request.method == "POST" and not secrets.compare_digest(
            request.form.get("csrf", "").encode("utf-8"), session["csrf"].encode("utf-8")
        ):
            g.service.record_activity(
                "Form rejected", session.get("role"), "Invalid CSRF token", "Blocked"
            )
            abort(400, "The form expired. Refresh the page and try again.")

    @app.after_request
    def private_pages(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        if request.endpoint != "static":
            response.headers["Cache-Control"] = "no-store"
        return response

    def require_role(*roles):
        if session.get("role") not in roles:
            g.service.record_activity(
                "Page/action denied", session.get("role"), request.endpoint, "Blocked"
            )
            abort(403, "Use an appropriate labelled demo role. This is not real authentication.")

    def allowed_visit(reference):
        require_role("patient", "staff")
        visit = g.service.visit(reference)
        if session["role"] == "patient" and visit["patientId"] != session["patient_owner"]:
            abort(403)
        return visit

    @app.context_processor
    def template_helpers():
        data = g.service.snapshot()
        role = session.get("role")
        patient = next(
            (v for v in data["visits"] if v["id"] == session["patient_id"]), data["visits"][0]
        )
        nav = (
            [
                ("Home", "patient", "heart"),
                ("My visits", "visits", "clock"),
                ("Hospitals", "hospitals", "map"),
                ("Chat", "chat", "message"),
                ("Devices", "devices", "watch"),
            ]
            if role == "patient"
            else [
                ("Home", "staff", "dashboard"),
                ("Patients", "patients", "users"),
                ("Chat", "chat", "message"),
                ("Devices", "devices", "watch"),
                ("Alerts", "alerts", "bell"),
            ]
        )
        if role == "admin":
            nav = [
                ("Home", "admin", "dashboard"),
                ("Staff & admin access", "admin_access", "users"),
                ("Login activity", "admin_activity", "activity"),
                ("Chat", "chat", "message"),
            ]
        support_threads = g.service.support_threads(role, session["patient_owner"])
        support_unread = sum(
            role not in message["readBy"]
            for thread in support_threads
            for message in thread["messages"]
        )
        counts = dict(
            waiting=sum(bool(v["arrival"]) and v["status"] != "closed" for v in data["visits"]),
            alerts=sum(not a["ack"] for a in data["alerts"]),
            help=sum(m["kind"] == "help" and not m["reviewed"] for m in data["messages"]),
            updates=sum(not u["reviewed"] for v in data["visits"] for u in v["updates"]),
            messages=sum(m["sender"] == "patient" and not m["reviewed"] for m in data["messages"]),
            disconnected=sum(
                bool(d["visit"]) and d["connection"] == "Disconnected" for d in data["devices"]
            ),
        )
        care_unread = (
            counts["messages"]
            if role == "staff"
            else sum(
                m["visit"] == session["patient_id"] and m["sender"] == "staff" and not m["read"]
                for m in data["messages"]
            )
            if role == "patient"
            else 0
        )
        parents = {
            "visits": ("patient", "Home"),
            "hospitals": ("patient", "Home"),
            "intake": (
                "hospitals" if role == "patient" else "patients",
                "Hospitals" if role == "patient" else "Patients",
            ),
            "messages": ("chat", "Chat"),
            "inbox": ("chat", "Chat"),
            "support": ("chat", "Chat"),
            "symptoms": ("patient", "Home"),
            "details": ("patients", "Patients"),
            "oracle_patients": ("patients", "Demo workflow"),
            "garmin_readings": ("devices", "Devices"),
            "admin_access": ("admin", "Home"),
            "admin_activity": ("admin", "Home"),
        }
        parent, parent_label = parents.get(request.endpoint, ("home", "Home"))
        current_page = (
            "chat"
            if request.endpoint in {"messages", "inbox", "support"}
            else "patients"
            if request.endpoint == "oracle_patients"
            else request.endpoint
        )
        return dict(
            data={key: data[key] for key in ("staff", "activity")} if role == "admin" else data,
            role=role,
            patient=patient if role != "admin" else None,
            nav=nav,
            counts=counts,
            metrics=METRICS,
            csrf=session["csrf"],
            time=display.format_time,
            waiting=display.waiting,
            metric_status=display.metric_status,
            device_status=display.device_status,
            finite=display.finite,
            trend=display.trend,
            tone=display.badge_tone,
            today=datetime.now().date().isoformat(),
            garmin_today=datetime.now(timezone.utc).date().isoformat(),
            intake_fields=INTAKE_FIELDS,
            support_unread=support_unread,
            chat_unread=support_unread + care_unread,
            navigation_page=current_page,
            back_url=url_for(parent),
            back_label=parent_label,
            show_back=bool(role) and request.endpoint not in {"patient", "staff", "admin", "home"},
        )

    def render(name, **context):
        return render_template(name, **context)

    def destination(back, reference):
        endpoints = dict(
            patient="patient",
            home="home",
            staff="staff",
            devices="devices",
            alerts="alerts",
            admin="admin",
            admin_access="admin_access",
            hospitals="hospitals",
        )
        if back in {"details", "messages"}:
            try:
                g.service.visit(reference)
            except ValueError:
                return url_for("home")
        if back == "details" and session.get("role") == "staff":
            return url_for("details", reference=reference)
        if back == "messages":
            return url_for("messages", reference=reference)
        return url_for(endpoints.get(back, "home"))

    @app.get("/")
    def home():
        if session.get("role"):
            return redirect(
                url_for(
                    "patient"
                    if session["role"] == "patient"
                    else "admin"
                    if session["role"] == "admin"
                    else "staff"
                )
            )
        return render("login.html", title="Welcome", page="login")

    @app.post("/login")
    def login():
        # Passwords are neither read into the demo service nor stored anywhere.
        g.service.record_activity(
            "Password sign-in unavailable",
            session.get("role"),
            "No identity service connected",
            "Unavailable",
        )
        flash("Real sign-in is not connected. Use a labelled demo entry below.", "error")
        return redirect(url_for("home"))

    @app.post("/demo/<role>")
    def demo_role(role):
        if role not in {"patient", "staff", "admin"}:
            abort(404)
        session["role"] = role
        g.service.record_activity(
            "Demo role entered", role, "Public demo entry, not authentication"
        )
        flash("Demo role entry — this is not secure authentication.")
        return redirect(url_for("home"))

    @app.post("/logout")
    def logout():
        g.service.record_activity(
            "Demo role exited", session.get("role"), "Signed out of demo role"
        )
        session.pop("role", None)
        return redirect(url_for("home"))

    @app.post("/reset")
    def reset():
        app.extensions["garmin_access"].clear()
        app.extensions["demo_services"].pop(session["demo_id"], None)
        session.pop("patient_id", None)
        session.pop("patient_owner", None)
        flash("Demo reset to fictional starting records.")
        return redirect(url_for("home"))

    @app.route("/register", methods=["GET", "POST"])
    @app.route("/staff/register", methods=["GET", "POST"], endpoint="assisted")
    def register():
        assisted = request.endpoint == "assisted"
        if assisted:
            require_role("staff")
        if request.method == "POST":
            try:
                profile = validate_profile(request.form, patient_account=not assisted)
                if not assisted:
                    if len(request.form.get("password", "")) < 8:
                        raise ValueError("Use a password of at least 8 characters.")
                    if request.form["password"] != request.form.get("confirm"):
                        raise ValueError("Passwords do not match.")
                reference = g.service.register(profile)
                flash("Demo profile created. No real account was created; passwords are discarded.")
                if assisted:
                    return redirect(url_for("details", reference=reference))
                session.update(role="patient", patient_id=reference, patient_owner=reference)
                return redirect(url_for("hospitals"))
            except ValueError as error:
                flash(str(error), "error")
        values = {key: request.form.get(key, "") for key in ("name", "dob", "email")}
        return render(
            "register.html",
            title="Staff-assisted registration" if assisted else "Patient registration",
            page="register",
            assisted=assisted,
            values=values,
        )

    @app.get("/patient")
    def patient():
        require_role("patient")
        reference = request.args.get("visit", session["patient_id"])
        visit = allowed_visit(reference)
        session["patient_id"] = reference
        return render(
            "patient.html",
            title="Home",
            page="patient",
            v=visit,
        )

    @app.get("/visits")
    def visits():
        require_role("patient")
        return render(
            "visits.html",
            title="My visits",
            page="visits",
            visits=g.service.patient_visits(session["patient_owner"]),
        )

    @app.route("/hospitals", methods=["GET", "POST"])
    def hospitals():
        require_role("patient")
        results = []
        location = None
        if request.method == "POST":
            results = []
            try:
                search = g.service.nearby_hospitals(request.form.get("postcode", ""))
                location, results = search["area"], search["hospitals"]
            except ValueError as error:
                flash(str(error), "error")
        return render(
            "hospitals.html",
            title="Hospitals",
            page="hospitals",
            v=g.service.visit(session["patient_id"]),
            hospitals=results,
            location=location,
            searched=request.method == "POST",
            fewest_waiting=min((h["waiting"] for h in results), default=None),
        )

    @app.route("/intake/<reference>", methods=["GET", "POST"])
    def intake(reference):
        visit = allowed_visit(reference)
        if session["role"] == "patient":
            session["patient_id"] = reference
        if not visit["hospital"]:
            flash("Choose a hospital before completing intake.", "error")
            return redirect(
                destination("hospitals" if session["role"] == "patient" else "details", reference)
            )
        if visit["intake"]:
            flash("Original intake already submitted. Use a symptom update.", "error")
            return redirect(
                destination("patient" if session["role"] == "patient" else "details", reference)
            )
        draft = g.service.drafts.get(f"intake:{reference}", {})
        review = False
        if request.method == "POST":
            draft = {
                key: request.form.get(key, "").strip()
                for key in [f[0] for f in INTAKE_FIELDS]
                + ["readingType", "readingValue", "readingSource", "readingTime"]
            }
            g.service.drafts[f"intake:{reference}"] = draft
            try:
                if any(not draft[key] for key, _, required in INTAKE_FIELDS if required):
                    raise ValueError("Complete the reason, symptoms and onset fields.")
                if draft["readingValue"]:
                    if not all(
                        draft[key] for key in ("readingType", "readingSource", "readingTime")
                    ):
                        raise ValueError(
                            "Add the optional reading's measurement, source and time, or leave it blank."
                        )
                    try:
                        value = float(draft["readingValue"])
                    except ValueError as error:
                        raise ValueError("Enter a numeric reading or leave it blank.") from error
                    if not display.finite(value):
                        raise ValueError("Enter a finite numeric reading or leave it blank.")
                    if draft["readingType"] not in {
                        "Temperature (°C)",
                        "Heart rate (bpm)",
                    }:
                        raise ValueError("Choose one of the listed measurement types.")
                    if not display.parse_time(draft["readingTime"]):
                        raise ValueError("Enter a valid measurement date and time.")
                review = request.form.get("intent") != "edit"
                if request.form.get("intent") == "submit":
                    g.service.submit_intake(reference, draft)
                    g.service.drafts.pop(f"intake:{reference}", None)
                    flash("Intake submitted. Staff must still confirm physical arrival.")
                    return redirect(
                        destination(
                            "patient" if session["role"] == "patient" else "details", reference
                        )
                    )
            except ValueError as error:
                flash(str(error), "error")
                review = False
        return render(
            "intake.html",
            title="Review your information" if review else "Your intake",
            page="intake",
            v=visit,
            values=draft,
            review=review,
        )

    @app.get("/staff")
    @app.get("/staff/patients", endpoint="patients")
    def staff():
        require_role("staff")
        if request.endpoint == "staff" and not request.args:
            return render("staff_home.html", title="Home", page="staff")
        data = g.service.snapshot()
        query = request.args.get("q", "").lower()
        status, review, connection = (
            request.args.get(k, "all") for k in ("status", "review", "device")
        )
        visits = []
        for visit in data["visits"]:
            device = next((d for d in data["devices"] if d["id"] == visit["device"]), None)
            if query not in (visit["name"] + visit["id"]).lower() or (
                status != "all" and visit["status"] != status
            ):
                continue
            if review == "symptoms" and not any(not u["reviewed"] for u in visit["updates"]):
                continue
            if review == "pending" and visit["category"] != "Awaiting review":
                continue
            if connection != "all" and (not device or device["connection"] != connection):
                continue
            visits.append(visit)
        return render(
            "staff.html",
            title="Patients"
            if request.endpoint == "patients"
            else "A clearer picture of your waiting room.",
            page=request.endpoint,
            visits=visits,
        )

    @app.get("/staff/patients/<reference>")
    def details(reference):
        require_role("staff")
        return render(
            "details.html", title="Patient details", page="details", v=g.service.visit(reference)
        )

    @app.get("/chat")
    def chat():
        require_role("patient", "staff", "admin")
        return render("chat.html", title="Chat", page="chat")

    @app.get("/staff/database")
    def oracle_patients():
        require_role("staff")
        if request.remote_addr not in {"127.0.0.1", "::1"}:
            abort(
                403,
                "This database preview is local-only until real staff authentication is connected.",
            )
        service = app.extensions["oracle_service"]
        result, error = None, None
        try:
            result = service.snapshot()
        except ValueError as problem:
            error = str(problem)
        return render(
            "oracle.html",
            title="Patients",
            page="oracle_patients",
            oracle_data=result,
            oracle_error=error,
            oracle_configuration=service.configuration(),
        )

    @app.route("/messages", defaults={"reference": None}, methods=["GET", "POST"])
    @app.route("/messages/<reference>", methods=["GET", "POST"])
    def messages(reference):
        reference = reference or session["patient_id"]
        visit = allowed_visit(reference)
        draft_key = f"message:{reference}:{session['role']}"
        if request.method == "POST":
            text = request.form.get("text", "")
            g.service.drafts[draft_key] = text
            try:
                g.service.message(
                    reference,
                    text,
                    request.form.get("kind", "general"),
                    "patient" if session["role"] == "patient" else "staff",
                )
                g.service.drafts.pop(draft_key, None)
                flash("Message sent. Submission is not proof of staff review.")
                return redirect(url_for("messages", reference=reference))
            except ValueError as error:
                flash(str(error), "error")
        return render(
            "messages.html",
            title="Messages",
            page="messages",
            v=visit,
            draft=g.service.drafts.get(draft_key, ""),
        )

    @app.route("/symptoms/<reference>", methods=["GET", "POST"])
    def symptoms(reference):
        visit = allowed_visit(reference)
        if visit["status"] == "closed":
            flash("This visit is closed. New symptoms cannot be sent to this visit.", "error")
            return redirect(
                destination("patient" if session["role"] == "patient" else "details", reference)
            )
        if request.method == "POST":
            try:
                g.service.symptom(
                    reference, request.form.get("description", ""), request.form.get("onset", "")
                )
                flash("Symptom update sent. Staff review and assessment are pending.")
                return redirect(url_for("patient"))
            except ValueError as error:
                flash(str(error), "error")
        return render("symptoms.html", title="Report new symptoms", page="symptoms", v=visit)

    @app.get("/inbox")
    def inbox():
        require_role("staff")
        return render("inbox.html", title="Inbox", page="inbox")

    @app.get("/devices")
    def devices():
        require_role("patient", "staff")
        return render(
            "devices.html",
            title="Devices",
            page="devices",
            garmin_configuration=app.extensions["garmin_access"].configuration(),
            garmin_check=g.service.garmin_check,
        )

    @app.post("/devices/garmin/check")
    def garmin_check():
        require_role("patient", "staff")
        try:
            g.service.garmin_check = app.extensions["garmin_access"].check()
            flash("Garmin API access checked. No watch readings were imported.")
        except ValueError as error:
            g.service.garmin_check = dict(
                state="Access not verified",
                message=str(error),
                checkedAt=datetime.now().astimezone().isoformat(),
            )
            flash(str(error), "error")
        return redirect(url_for("devices"))

    def require_local_garmin():
        require_role("patient", "staff")
        if request.remote_addr not in {"127.0.0.1", "::1"}:
            abort(403, "This personal-account Garmin preview is available only on this laptop.")

    @app.post("/devices/garmin/start")
    def garmin_start():
        require_local_garmin()
        try:
            selected = date.fromisoformat(request.form.get("date", ""))
            if selected > datetime.now(timezone.utc).date():
                raise ValueError()
        except ValueError:
            flash("Choose today or an earlier Garmin calendar date.", "error")
            return redirect(url_for("devices"))
        g.service.garmin_day = selected.isoformat()
        g.service.garmin_readings = None
        g.service.garmin_attempted = None
        return redirect(url_for("garmin_readings"))

    @app.get("/devices/garmin/readings")
    def garmin_readings():
        require_local_garmin()
        service = g.service
        if not service.garmin_day:
            return redirect(url_for("devices"))
        now = datetime.now(timezone.utc)
        attempted = display.parse_time(service.garmin_attempted)
        if not attempted or (now - attempted).total_seconds() >= 30:
            service.garmin_attempted = now.isoformat()
            try:
                result = app.extensions["garmin_access"].readings(service.garmin_day)
                if service.garmin_readings and result["errors"]:
                    previous = service.garmin_readings
                    if result["heartRate"] is None and previous["heartRate"] is not None:
                        for key in ("heartRate", "heartTime", "history", "stats"):
                            result[key] = previous[key]
                service.garmin_readings, service.garmin_error = result, None
            except ValueError as error:
                service.garmin_error = str(error)
        return render(
            "garmin_readings.html",
            title="Garmin readings",
            page="devices",
            garmin_data=service.garmin_readings,
            garmin_error=service.garmin_error,
            garmin_day=service.garmin_day,
            garmin_attempted=service.garmin_attempted,
            auto_refresh=30,
        )

    @app.post("/devices/garmin/stop")
    def garmin_stop():
        require_local_garmin()
        g.service.garmin_day = g.service.garmin_readings = g.service.garmin_attempted = None
        g.service.garmin_error = None
        app.extensions["garmin_access"].clear()
        flash("Garmin preview stopped and readings cleared from this browser's demo memory.")
        return redirect(url_for("devices"))

    @app.get("/alerts")
    def alerts():
        require_role("staff")
        return render(
            "alerts.html",
            title="Alerts",
            page="alerts",
            acknowledged=request.args.get("filter") == "acknowledged",
        )

    @app.get("/admin")
    def admin():
        require_role("admin")
        return render("admin_overview.html", title="Admin overview", page="admin")

    @app.get("/admin/access")
    def admin_access():
        require_role("admin")
        return render("admin.html", title="Staff & admin access", page="admin_access")

    @app.get("/admin/activity")
    def admin_activity():
        require_role("admin")
        return render("admin_activity.html", title="Login activity", page="admin_activity")

    @app.get("/admin/activity.csv")
    def admin_activity_csv():
        require_role("admin")
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=["time", "event", "actor", "detail", "outcome"])
        writer.writeheader()
        writer.writerows(g.service.snapshot()["activity"])
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={
                "Content-Disposition": 'attachment; filename="pulse-demo-activity.csv"',
            },
        )

    @app.get("/admin/security")
    def admin_security():
        require_role("admin")
        return redirect(url_for("admin"))

    @app.route("/support", defaults={"identifier": None}, methods=["GET", "POST"])
    @app.route("/support/<identifier>", methods=["GET", "POST"])
    def support(identifier):
        require_role("patient", "staff", "admin")
        role, patient_id = session["role"], session["patient_owner"]
        thread = None
        if identifier:
            try:
                thread = g.service.support_thread(identifier, role, patient_id)
            except ValueError:
                abort(404, "Support conversation unavailable for this demo role.")
        if request.method == "POST":
            try:
                if request.form.get("intent") == "read" and identifier:
                    g.service.read_support(identifier, role, patient_id)
                elif identifier:
                    g.service.reply_support(
                        identifier, role, patient_id, request.form.get("text", "")
                    )
                else:
                    identifier = g.service.start_support(
                        role,
                        patient_id,
                        request.form.get("subject", ""),
                        request.form.get("text", ""),
                        target=request.form.get("target"),
                        contact_patient=request.form.get("patient_reference", ""),
                    )
                flash("Support update saved. Sending does not guarantee immediate review.")
                return redirect(url_for("support", identifier=identifier))
            except ValueError as error:
                flash(str(error), "error")
        audience = request.args.get("audience", "staff") if role == "admin" else "admin"
        if audience not in ({"staff", "patient"} if role == "admin" else {"admin"}):
            audience = "staff" if role == "admin" else "admin"
        threads = g.service.support_threads(role, patient_id)
        if role == "admin" and request.args.get("audience"):
            threads = [t for t in threads if audience in t["participants"]]
        return render(
            "support.html",
            title="Administration chat" if role != "admin" else "Support conversations",
            page="support",
            threads=threads,
            thread=thread,
            contact_role=audience,
        )

    @app.post("/actions/<name>")
    def action(name):
        require_role("patient", "staff", "admin")
        reference = request.form.get("visit", session["patient_id"])
        back = request.form.get("back", "home")
        try:
            staff_actions = {
                "check_in",
                "assign",
                "close",
                "review",
                "decision",
                "destination",
                "note",
                "acknowledge",
            }
            if name in {"tick", "fail_next"}:
                require_role("patient", "staff")
            if name in staff_actions:
                require_role("staff")
            if name in {"add_staff", "toggle_staff"}:
                require_role("admin")
            if name in staff_actions - {"acknowledge"} or name in {"hospital", "help", "mark_read"}:
                allowed_visit(reference)
            if name == "hospital":
                if session["role"] == "patient":
                    reference = g.service.plan_visit(reference, request.form.get("hospital"))
                    session["patient_id"] = reference
                    return redirect(url_for("intake", reference=reference))
                g.service.select_hospital(reference, request.form.get("hospital"))
            elif name == "check_in":
                g.service.check_in(reference)
            elif name == "assign":
                g.service.assign(reference, request.form.get("device"))
            elif name == "close":
                g.service.close(reference)
            elif name == "review":
                g.service.review(reference, request.form.get("update") or None)
            elif name == "mark_read":
                g.service.mark_read(reference)
            elif name == "help":
                g.service.message(reference, "I need assistance, please.", "help")
            elif name == "decision":
                g.service.decision(
                    reference, request.form.get("category", ""), request.form.get("reason", "")
                )
            elif name in {"destination", "note"}:
                getattr(g.service, name)(reference, request.form.get("text", ""))
            elif name == "acknowledge":
                g.service.acknowledge(request.form.get("id"))
            elif name == "add_staff":
                g.service.add_staff(
                    request.form.get("name", ""),
                    request.form.get("email", ""),
                    request.form.get("role", ""),
                )
            elif name == "toggle_staff":
                g.service.toggle_staff(request.form.get("id"))
            elif name == "tick":
                g.service.tick()
            elif name == "fail_next":
                g.service.fail_next = True
                flash("The next demo write will fail once. Reads will still work.")
                return redirect(destination(back, reference))
            else:
                abort(404)
            flash("Demo update saved.")
        except ValueError as error:
            flash(str(error), "error")
        return redirect(destination(back, reference))

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(405)
    @app.errorhandler(413)
    def error_page(error):
        return render(
            "error.html",
            title=f"{error.code} · Request unavailable",
            page="error",
            message=error.description,
        ), error.code

    @app.errorhandler(ValueError)
    def invalid_value(error):
        return render(
            "error.html", title="Request unavailable", page="error", message=str(error)
        ), 400

    return app
