# Pulse implementation explanation (Python version)

The active website is Python Flask, Jinja HTML templates and CSS. Python handles page rendering, routes, form validation, demo state, reading/history calculations and tests. It is accurate to say **Python Flask backend with a server-rendered HTML/CSS interface and Python tests**. HTML/CSS are not Python. No authored JavaScript is used or served; postcode search runs in Python; approximate distances are calculated from a postcode district centre. Browser GPS is unavailable.

## Main files

| File | Simple explanation |
| --- | --- |
| app.py | Starts the Flask server on port 5000 |
| pulse/__init__.py | Creates Flask, handles GET/POST routes, cookies, CSRF, demo-role guards and page rendering |
| pulse/services.py | Demo actions: register, intake, check-in, assignment, readings, messages, symptoms/review, notes, decisions, alerts and admin |
| pulse/fixtures.py | Fictional starting records, separate from routes/templates |
| pulse/display.py | Waiting time, source-aware reading status, freshness and SVG chart coordinates |
| pulse/oracle_mapping.py | Translates JSON shaped like Maham's SQL views; does not connect to Oracle |
| templates/base.html | Shared page frame and navigation |
| templates/macros.html | Reusable fields, status badges, command forms, metric cards and charts |
| Other templates | Separate patient/staff/admin pages and forms |
| static/styles.css | Existing black/red CSS, mobile layouts, focus/status styles and decorative heartbeat |
| templates/hospitals.html | Search-only starting page; Python POST postcode search and distance-sorted results; no browser scripts |
| pulse/location.py | Postcode-district validation/lookup, saved LS6 fallback and straight-line distance calculation |
| tests/test_services.py | Python workflow/display/Oracle mapping behaviour |
| tests/test_routes.py | Flask pages/forms/session state, errors, escaping, CSRF and demo restrictions |
| tests/test_theme.py | Calculates token contrast; not full accessibility proof |
| tests/test_browser.py | Python Playwright core journey, mobile forms and stale/missing/failure states |
| requirements*.txt / pyproject.toml | Python dependencies and test/lint settings |
| .github/workflows/ci.yml | Python CI; not run on GitHub yet, no deployment |
| Pulse.sql | Maham's unchanged schema/seed/views; not executed by the website |
| Desktop/Pulse-React-backup | Previous React source/tests/docs preserved outside this project |

## Architecture and state

An HTML form posts to a Python route. The route validates the request and calls `DemoService`. The service changes its records in server memory. Flask renders a new Jinja HTML page with the updated snapshot. This is ordinary server-side web rendering, not React or Python running inside the browser.

Each browser cookie identifies a separate demo instance. It contains identifiers, role choice and CSRF token, not health form data or passwords. Refresh retains records. Tabs sharing the cookie share records; separate browsers/devices do not. Reset/restart clears the demo. Multiple production workers would not share this memory. No second database was built.

Python `RLock` serializes writes within one demo/process so two active visits cannot take the same band. The real database integration still needs its own transaction/constraints. Demo roles are publicly selectable; route guards and CSRF do not establish real identity, secure staff access or production authorization.

## Two journeys

**New symptoms:** `symptoms.html` → Python route `/symptoms/<reference>` → `DemoService.symptom()` → appended history plus message and review-needed alert → staff page filters/symptom history → `review()` records demo identity/time → staff opens conversation and `message()` replies. Original intake remains unchanged; assessment stays pending. No model is invoked.

**Band/readings:** staff POST check-in records arrival and starts software waiting time → assignment validates active arrival/device availability → simulator generates explicitly synthetic samples → Python display helpers/template metric cards show values/source/time/history. Disconnected sample Sam retains stale readings; missing Fitbit metrics display Unavailable. Closing releases the band. No real sensor is read.

## Oracle mapping test name

The previous `oracle-mapping.test.js` is preserved in the legacy archive; it is no longer an active test. Its behaviour is now tested in Python `test_oracle_json_mapping_not_database_access` inside `tests/test_services.py`. Oracle identifies the expected database row shape; mapping means translating fields. It is not a database query or integration/security test. Blank numbers stay null; supported metrics only; triage and stored NEWS2 remain separate from Elysha's AI output.

## Meaningful checks and limitations

Python tests preserve arrival versus registration, elapsed waiting, exclusive assignment/release, append-only symptoms, human messages/read/review state, stable acknowledgements, missing/stale/disconnected readings, retries and mapping boundaries. Flask tests check actual responses and form errors, password discard, server-memory drafts, cookie isolation/reset, escaping and CSRF. Browser tests run core pages with JavaScript disabled and optional fonts blocked. No assertion is presented as proof of Oracle deployment, real access control, medical validation or model performance.

The basic CSS-token contrast test computes ratios instead of merely checking strings; it does not replace screen-reader, gradient/inheritance, physical-device or full WCAG testing. Python syntax compilation replaces the former frontend build check; there is no npm build now.

See development-guide.md for setup, manual-testing.md for recorded checks and pending cases, and INTEGRATION.md for teammate work still needed.

The sharing review adds `tests/test_readiness.py`: assignment-to-first-reading behaviour, expired freshness, frozen waiting on closure, separate symptom/general review, invalid optional readings, closed/overlong symptom rejection, reachable links/form targets and staff filters. Two additional Python browser flows exercise assisted registration and staff/admin controls. Form-target OPTIONS tests check routing only; browser/service tests check actions. No new test framework was added.


## Admin workspace and support update

admin_overview.html, admin.html, admin_activity.html and admin_security.html separate administration from clinical care. support.html renders support conversations. DemoService owns support messages, read markers and local activity records. tests/test_admin_support.py checks direct-route/action boundaries, thread participants/patient ownership, sender-role spoofing, escaping, failed-send retry, duplicate profile emails, event limits and CSV contents. These are demo-boundary checks, not proof of production identity/security. The existing Python browser suite now exercises patient-admin and staff-admin replies, unread/read status and mobile admin pages.

## Garmin access check

pulse/garmin.py loads a key from a server environment variable or ignored local file, performs a fixed-host HTTPS token exchange without redirects, validates response shape/expiry and discards the token. The Devices route stores only a dated result. tests/test_garmin.py verifies secret exclusion, no disk cache, error sanitisation, invalid/expired token states, role guards and no changes to synthetic readings. It is not a real account/watch/metric integration test.

## Garmin readings update (supersedes access-check-only notes above)

The local owner preview now requests documented daily heart-rate and SpO2 data, maps timestamped samples/daily HR statistics, and polls every 30 seconds through a native HTML refresh. Temperature remains unavailable; no direct live-watch connection is claimed. Values remain separate from synthetic visits and Oracle/model data. The readings client caches bearer tokens only in server memory; Stop/Clear removes them. Local loopback and patient/staff demo role checks apply, but real authenticated ownership/consent is still required before any public/multi-user use. Real owner HR/statistics and the website preview have now been verified after exact-text key configuration; token/HR/SpO2 endpoints returned HTTP 200, but no timestamped SpO2 sample was supplied. Automated tests continue to use synthetic HTTP responses. See garmin-setup.md for current instructions, schemas, mapping and limitations.

Latest Garmin access result: exact-text credential corrected the screenshot transcription. Authentication and both measurement endpoints returned HTTP 200; owner HR/statistics rendered on the running site. The credential remains in the ignored local secret file only; no secret, raw measurement values or personal-data screenshots were added to source. No push/merge.
