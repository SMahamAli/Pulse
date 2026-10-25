# Pulse integration notes — Python Flask

## Hardware credential before submission

The hardware file `ESP-E12 code` now uses `YOUR_API_KEY` in its API-key assignment. Configure the real key privately in the hardware teammate's local firmware before uploading to the device. Do not commit it. The original file was preserved in an ignored local `.secrets` backup; it is not a distributable setup file. The previous key was already committed upstream, so replacing this copy does not remove its history: Mostafa/the key owner must revoke or rotate it. Sensor and transmission logic were preserved. The generated tracked `ai_api` bytecode was removed because it supplies no source API implementation.

## AI update after the team pull

The team added `model/02_reassessment_model.py`, its synthetic CSV and analysis scripts. The earlier notebook is now `model/AI_Training_backup.ipynb`. There is no source prediction API or exported fitted model in this update; the tracked `ai_api` bytecode is not an integration interface.

`pulse/assessment.py` runs the unchanged training script only when staff choose **AI research > Prepare research model**. It reuses that script's fitted Random Forest pipeline and held-out `X_test` rows. Staff select a synthetic dataset reference and see the actual classifier output. Preparation is cached in server memory until restart. Model source hashes identify the code revision; no confidence score, clinical accuracy or model version is invented. Failed preparation/prediction shows an error without substituting a completed result. The core website still opens without these optional AI libraries.

Install with `python -m pip install -r requirements-ai.txt`. Development/CI requirements include these packages so real model execution is tested. The preview never changes patient priority, staff decisions or Oracle records. Public demo staff entry remains a demonstration boundary, not production authentication.

The model expects age, sex, chief complaint, arrival mode, triage category, heart rate, blood pressure, respiratory rate, SpO2, temperature, pain score and consciousness. Several are absent from current web forms and the supported sensor feed. Skin temperature cannot silently stand in for unspecified dataset temperature. **Team agreement is still needed** on feature names/units/sources, missing data, available clinical inputs and mapping Oracle patient/assignment IDs to an inference request. The training pipeline has an imputer, but its existence does not validate using severely incomplete live inputs. No removed clinical fields were added back to the website.

The dataset explicitly describes labels from a fictional toy risk score with random noise. This implementation demonstrates software integration, not clinical validity. Patient assessment states remain separate from the research preview.

Actual local run of source revision `d201a0b5cea5`: **0 of 22 positive-labelled examples flagged**, and 0 of 400 examples flagged overall in its held-out split. This is a material unresolved model-quality issue for Elysha, even though pipeline execution succeeds. The preview derives and displays these counts from the script's actual test outputs. No decision threshold, labels or training logic were changed to hide the result.

## Current navigation and metric scope

The website now supports heart rate and skin temperature only. Oxygen saturation was removed at the team's request from web forms/cards, demo data, Python mapping, Garmin retrieval and our read-only API output. Earlier mentions below describe historical proposals. Maham's SQL and Elysha's notebook were not modified. The live source still loaded 11 patients, 11 reading records and 10 alerts; mapped names/IDs were checked against the raw API and matched.

Staff have one Patients workspace with separate Demo workflow and Oracle records source tabs. The Oracle records preserve database names/IDs; workflow records remain fictional and do not write to that database. Do not merge identities by matching names. Chat is a shared navigation hub for existing care and administrative channels. Admin-initiated patient support uses a validated demo portal reference; an Oracle ID is not yet a portal/chat identity.

Latest status: the protected read-only ORDS API and private Flask backend client in MAHAM_ALI / WKSP_MAHAMALI now load stored database records successfully. The live check returned 11 current patients, 11 latest readings and 10 alerts; anonymous access to all three resources returned 401. V_LATEST_VITALS still references a removed RESP_RATE column, so our reading handler queries supported fields through active assignments without changing Maham's table/view definitions. There is no SPO2 column in the updated table; it stays unavailable. See [connection evidence](database-access.md).

## What exists now

The website is served by Flask. Python routes in `pulse/__init__.py` receive forms, validate demo role/scope and CSRF, call `DemoService` in `pulse/services.py` and render Jinja HTML. This is a working Python web layer. It still uses fictional in-memory records, not Maham's running Oracle database.

The former React proposals remain in the separate Desktop `Pulse-React-backup/docs/INTEGRATION.md` snapshot for reference. They are proposals, not live endpoints. This document reflects the active Flask application.

## Responsibilities

- Mohammed: Flask website, templates, CSS, service interfaces, tests and page/data mapping.
- Mostafa: wristband/sensors, actual measurement source, units, cadence and transmission.
- Maham: Oracle database; owns schema/models/migrations.
- Elysha: actual assessment/prioritisation model, inputs, job states and outputs.
- Team to agree: who owns production backend/API orchestration, authentication, Oracle connection/deployment and synchronization. Having Flask routes does not establish a production integration or transfer ownership of Maham's work.

## Maham's actual SQL — preserved

**Database naming:** Oracle is the database and APEX is the development platform. The checked workspace is MAHAM_ALI, schema WKSP_MAHAMALI, ORDS alias `maham_ali`. `Pulse.sql` is the source filename. Flask's `pulse/oracle.py` uses Python's standard HTTPS library to call protected ORDS endpoints, so no direct Oracle database driver is required. Private credentials are outside source control. This read-only preview does not persist the demo registration, messages or band actions.

**Alignment status:** Python projections match the documented columns from the three views below, including `skin_temp`, `heart_rate`, `spo2`, `recorded_at`, patient/assignment identifiers and supplied alert fields. They are partial, tested field translations, not a complete schema adapter or live database integration. Demo patient/band IDs and website lifecycle values are separate from Oracle IDs/statuses; they must be agreed before writes. Do not tell reviewers that every website feature is database-backed.

`Pulse.sql` from fetched GitHub commit `1c61dd7` defines patient/staff/roles/zones/triage, bands/assignments, vital readings/manual observations, risk scores, alert thresholds/events and audit logs, with fictional sample rows. Views: `v_current_patients`, `v_latest_vitals`, `v_open_alerts`. It is not a website startup step and was not executed. It contains destructive setup statements and demo credential values; coordinate setup with Maham in her intended test environment.

`pulse/oracle_mapping.py` ports the previous tested JSON mappings into Python. It accepts uppercase/lowercase field names, maps skin_temp/heart_rate/spo2 and preserves missing values. It does not query Oracle. Tests construct JSON rows; they are not database integration tests.

| Actual database source | Agreement needed before connection |
| --- | --- |
| patient / v_current_patients | SQL requires arrival, triage and zone immediately; website supports registration before arrival. Agree patient versus visit IDs, repeated visits and hospital scope. Never fabricate physical presence. |
| wristband / device_assignment | Inventory status is different from connection status. Enforce unique active assignments atomically in the real database/backend; the Python process lock is not distributed transaction safety. |
| vital_reading / v_latest_vitals | Agree ingestion authentication, assignment association, numeric types, units, sources and UTC serialization. Latest view is insufficient for historical trends. Preserve skin temperature semantics; manual temperature is separate. |
| alert / v_open_alerts | View includes Open and Acknowledged; acknowledgement timestamp must be supplied from table/API. Stable event IDs, supported kinds and deduplication needed. |
| triage_category / risk_score | Recorded triage/NEWS2 is not Elysha's model. max_wait_mins is not estimated time remaining. Do not activate old respiratory/fall thresholds in the website. |
| staff / role / audit_log | Real identity/session handling, secure password hashes, hospital/visit permissions and trusted audit actors are still required. Never expose stored credential values to templates or clients. |

There are no agreed persistent representations yet for hospital crowding, portal registration, structured intake, conditions/allergies, conversations, append-only symptom reviews, independent model jobs/version/explanation and destination-confirmation history. Resolve those with Maham rather than creating a second database or independently modifying her schema.

## Replaceable Python boundaries

Keep the service method behaviour in `pulse/services.py`, but replace memory access with agreed repository/API calls. Keep fixtures out of route/template code. Use Python database access only on the server with environment-provided secrets; never expose credentials in HTML, CSS, browser helpers, cookies or source control. No real credentials are configured now.

Intended flow: Mostafa's band → authenticated server ingestion → Maham's Oracle data → authorized Flask pages/API. Server sends intake, age/conditions and sourced available readings to Elysha's model, then records and displays actual pending/completed/failed results. Explanations/version/department appear only when supplied. Staff decision/reason and confirmed destination stay separate. `AssessmentService.request()` currently returns pending only; no fixed rules or synthetic output are presented as a running model.

Current POST web routes are for the local demo, not a public hardware/model API contract. Agree JSON endpoints, errors, idempotency, server time, persistence and ownership before connecting teammates. Do not ingest hardware by posting patient-facing forms.

## Current browser/session limits

The mock now distinguishes stable `patientId` (the demo person) from `id` (each visit reference). A cookie remembers the demo owner and currently selected visit. `DemoService.plan_visit` reuses an unfinished draft or creates a fresh visit; it never changes the old intake, confirmed arrival or band. `patient_visits` supplies the history page. These are in-memory website fields, not changes to Maham's schema. Agree their mapping to persistent people/encounters before enabling writes. Staff-assisted registration creates a separate demo person; portal activation is still unimplemented.

Server memory persists through refresh and is shared by tabs using the same cookie; reset/restart clears it. Other browsers have isolated demos. No durable storage, real multi-user synchronization, distributed worker state or offline mode exists. Demo staff profiles do not control public role-entry buttons. Server demo guards and CSRF are useful basics, not proof of real authentication/authorization or clinical security.

Forms preserve message drafts in server memory on a simulated failure. Passwords are discarded. Session cookies carry identifiers/role/CSRF only, not health form data. Responses use no-store. Production identity, retention/deletion, encryption, audit, deployment limits and clinical/privacy review remain needed.

## Maps, crowding and wearable work

Google Maps directions are external links using known addresses. The initial page contains only postcode search; no map or preloaded hospital cards. Leeds names/ED postcodes were checked against Leeds Teaching Hospitals. Waiting ranges are synthetic people counts, independent of wait estimates. Fewer waiting patients does not guarantee shorter/suitable care. A real hospital feed and approved geography are required; Maps is not that feed.

The application has no authored JavaScript or script tags. Postcode search posts to Flask, which calls the replaceable `pulse/location.py` lookup and distance helpers through `DemoService.nearby_hospitals`. Full postcodes are reduced to their district before an external lookup; no search location is written to records/session or placed in the URL. LS6 has saved Postcodes.io coordinates for offline demonstration. Other districts use the public outcodes endpoint with a four-second timeout and explicit failure/empty states. Distances are straight-line estimates from district and hospital-postcode centres, not route distances. Results cover only our two supported Leeds hospitals within 30 miles, not a comprehensive hospital directory. Browser GPS remains unavailable. The old area selector and fictional London hospitals were removed.

No personal wearable integration or vendor login exists. Fitbit's sample has heart rate only. Apple Watch/WHOOP/Fitbit require agreed vendor permissions/APIs and backend/native support as applicable. Pulse band remains the fallback. The freshness cutoff is illustrative, not a clinical threshold.

## Team update pulled

The branch was fast-forwarded to `54fcf11`; `AI_Training.ipynb` and the team README were inspected and preserved. See `team-sync.md` for actual model experiments, review-table fields, README differences and decisions required. `pulse/ai_mapping.py` prepares that review-table JSON boundary without executing the notebook or treating anomalies/duration estimates as urgency/time-until-seen. No live AI connection was added.

### Postcode data sources

- Postcodes.io outcode lookup: https://postcodes.io/docs/outcode/lookup/
- Leeds emergency departments, locations and age-specific service notes: https://www.leedsth.nhs.uk/services/emergency-departments/
- LGI emergency entrance: https://www.leedsth.nhs.uk/hospitals/leeds-general-infirmary/directions/

Checked 24 October 2026. Postcodes.io supplies geographic coordinates only, not crowding. Full postcodes are reduced to a district before lookup. The LS6 saved coordinates are a dated fallback; no live location-service claim is made for that path. Hospital coordinates represent the destination postcode, not a measured entrance position. Leeds waiting ranges are synthetic display examples, never derived from distance or turned into clinical wait predictions. Backend agreement is needed on real count/range fields and provenance.


## Admin and support boundaries

Admin now has /admin, /admin/access, /admin/activity, /admin/activity.csv and /admin/security. It has no clinical list/detail/inbox/device/alert pages; demo role guards reject direct clinical requests from that role. This is tested separation between publicly selectable demo roles, not proof of real authorization. Production identity must establish real accounts, activation, hospital scope and permitted operations independently of demo buttons.

/support and /support/<id> provide separate non-clinical support: patient-admin and staff-admin pairs. Admin can initiate staff conversations; patients initiate their own admin requests. Existing patient-staff clinical messages remain separate. The server takes sender role from the session, checks participation/patient reference, escapes text and validates lengths. Read receipt means another demo role explicitly marked the thread read, not clinical review. Staff/admin identities represent role inboxes within one demo, not individually authenticated people.

DemoService keeps support threads/messages and at most 200 access events in server memory. Events record demo entry/exit, unavailable password sign-in, rejected CSRF/role requests and profile changes. They contain no passwords, submitted form text or IP addresses. This is not a durable/tamper-resistant audit trail. Reset/restart clears it; CSV export is an admin-only demo route. Profile activation cannot revoke public demo entry.

Proposals for team agreement: backend thread/message storage with authenticated participants, individual sender identity, read timestamps, inbox scope, retention and polling/realtime delivery; identity-provider access events and appropriate audit protection. Maham's schema is unchanged. Real MFA/password reset/session revocation and production HTTPS configuration remain future work, not working toggles on the security page.

## Garmin Personal API boundary

See garmin-setup.md for local secret setup and official references. Devices now has a server-side personal-key token exchange; it requests no health resource, retains no bearer token and imports no reading. Key/token values never enter demo snapshots/cookies/templates or audit/support logs. The supplied chat credential was not stored or used. Live access remains unverified until the owner configures a replacement. A personal key represents one owner, not all patients. Agree consent, individual account identity, supported metric endpoints/mapping, sync timestamps and deliberate owner-to-visit association before health data import. No database or model integration was changed.

## Garmin readings update (supersedes access-check-only notes above)

The local owner preview now requests documented daily heart-rate and SpO2 data, maps timestamped samples/daily HR statistics, and polls every 30 seconds through a native HTML refresh. Temperature remains unavailable; no direct live-watch connection is claimed. Values remain separate from synthetic visits and Oracle/model data. The readings client caches bearer tokens only in server memory; Stop/Clear removes them. Local loopback and patient/staff demo role checks apply, but real authenticated ownership/consent is still required before any public/multi-user use. Real owner HR/statistics and the website preview have now been verified after exact-text key configuration; token/HR/SpO2 endpoints returned HTTP 200, but no timestamped SpO2 sample was supplied. Automated tests continue to use synthetic HTTP responses. See garmin-setup.md for current instructions, schemas, mapping and limitations.

Latest Garmin access result: exact-text credential corrected the screenshot transcription. Authentication and both measurement endpoints returned HTTP 200; owner HR/statistics rendered on the running site. The credential remains in the ignored local secret file only; no secret, raw measurement values or personal-data screenshots were added to source. No push/merge.
