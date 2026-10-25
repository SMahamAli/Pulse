# Oracle access check

Latest scope update: the team removed oxygen saturation entirely from the website. Our existing readings GET now returns only patient/assignment references, recorded time, heart rate and skin temperature. No table/view or privilege was changed. Actual retrieval still returned 11 patients, 11 latest readings and 10 alerts, with names/IDs matching the raw source. In the UI, open Staff → Patients → Oracle records. The source tabs explain why these database names differ from the website's workflow fixtures. Earlier references below to a NULL/unavailable oxygen field are historical.

## Current result: authenticated read-only loading works

Rechecked after Maham's update on 25 October 2026. The protected Python reader successfully loaded **11 current patients, 11 latest-reading records and 10 open/acknowledged alerts**. Anonymous GET requests to all three endpoints returned **HTTP 401**. These are actual requests to the existing Oracle database, not fixtures; the stored records are demonstration data. The counts are an observation, not a permanent expected total.

The updated VITAL_READING columns are READING_ID, ASSIGNMENT_ID, RECORDED_AT, HEART_RATE, SKIN_TEMP and DEVICE_ID. SPO2, RESP_RATE and FALL_DETECTED are absent. V_LATEST_VITALS remains invalid: Oracle reported ORA-04063, and USER_ERRORS identified ORA-00904 for RESP_RATE. Maham's table/view definitions were not changed.

Only our existing `readings/latest/` GET handler was adapted. It joins VITAL_READING to active DEVICE_ASSIGNMENT records and selects the latest record per assignment using RECORDED_AT and READING_ID for ties. SpO2 is explicitly SQL NULL because no source column exists. Patient/alert handlers still use V_CURRENT_PATIENTS and V_OPEN_ALERTS. The website matches both patient and assignment IDs and does not guess links for device-only readings. `integration/ords_read_api.sql` reflects the current query.

This verifies reading stored data, not live sensor transmission, real patient authentication or database writes. Patient registration/intake/messages/band actions still use the isolated mock service. Timestamp timezone and any future SpO2 source need team agreement. The earlier activation/update history below is superseded by this current result.

## Earlier result while source objects were being updated

The user approved the protected read-only connection. The `pulse.website.read` module is published with three GET handlers, protected by `pulse.website.read.access` and the `pulse.website.reader` role. The new `pulse.website.backend` client holds that single role. Its Oracle-generated secret is stored only in ignored `.secrets/oracle.json`; values are not documented or printed.

Python successfully obtained an OAuth token (HTTP 200). Anonymous patient GET returned HTTP 401 in both the browser and a Python request with a Pulse User-Agent. Authenticated resource GETs returned HTTP 403 with Oracle's explanation that a referenced table/view is missing or inaccessible. This is not a successful data connection yet.

A subsequent direct SQL check returned ORA-00942 for `WKSP_MAHAMALI.PATIENT` and `WKSP_MAHAMALI.V_CURRENT_PATIENTS`. `USER_TABLES` then listed only ALERT_THRESHOLD, AUDIT_LOG, ROLE, STAFF, TRIAGE_CATEGORY and WRISTBAND; a view lookup found none of the three dashboard views. This differs from the earlier browser observations below. Mohammed confirmed that Maham is updating the database. No team tables/views were created, dropped, modified or restored by this connection work. Do not run the destructive `Pulse.sql` setup automatically.

Next: Maham checks/completes the intended source schema. Then retry **Staff → Oracle patients** and verify real row counts. The API uses explicit `WKSP_MAHAMALI` view names and excludes NHS identifiers, staff passwords, respiratory rate and fall fields. The website reports the failure and does not substitute sample patients.

The remaining sections record the earlier inspection and original proposal; the status above supersedes their statements that access setup has not run.

Checked through the signed-in browser on 24 October 2026. This records what was actually observed; it does not claim Flask is connected.

## Confirmed

- Service: Oracle-hosted APEX at `https://oracleapex.com/ords/`. This current workspace is separate from the earlier university-hosted screenshot.
- Workspace: `MAHAM_ALI`. Database schema: `WKSP_MAHAMALI`.
- 13 existing tables: ALERT, ALERT_THRESHOLD, AUDIT_LOG, DEVICE_ASSIGNMENT, MANUAL_OBSERVATION, PATIENT, RISK_SCORE, ROLE, STAFF, TRIAGE_CATEGORY, VITAL_READING, WRISTBAND and ZONE.
- PATIENT data was readable. Object Browser's Count Rows reported **14 rows**.
- Existing views: V_CURRENT_PATIENTS, V_LATEST_VITALS and V_OPEN_ALERTS.
- V_LATEST_VITALS columns: PATIENT_ID, ASSIGNMENT_ID, RECORDED_AT, HEART_RATE, SPO2, RESP_RATE, SKIN_TEMP and FALL_DETECTED. The supported website mapping uses heart rate, SpO2 and skin temperature; the extra respiratory/fall fields were not activated in the website.
- PATIENT requires arrival, triage and zone immediately. This still needs agreement with the website's pre-arrival registration workflow; no fake check-in or invented clinical category should fill the gap.
- Existing ORDS configuration: REST access enabled, alias `maham_ali`. Metadata authorization switch was off. No setting was changed or saved.
- The existing catalogue at `https://oracleapex.com/ords/maham_ali/metadata-catalog/` returned `items: []`, `count: 0`, `hasMore: false` in the browser. No usable resource endpoint was discovered. This does not prove there are no protected/custom APIs elsewhere.

The first catalogue request from Python timed out; the browser request succeeded and returned the empty catalogue. No statement about working Python connectivity is based on that timeout.

## Proposed next step: protected read-only API (not published)

Flask needs API access independent of the interactive APEX browser session. APEX developer login is not itself a configured database/REST credential for Flask. Do not copy browser session URLs into backend configuration.

| Proposed GET path | Existing source | Intended scope |
| --- | --- | --- |
| `/ords/maham_ali/pulse/v1/patients/` | V_CURRENT_PATIENTS | Current patient/assignment reference and recorded visit fields |
| `/ords/maham_ali/pulse/v1/readings/latest/` | V_LATEST_VITALS | Patient/assignment, recorded time, HEART_RATE, SPO2, SKIN_TEMP only |
| `/ords/maham_ali/pulse/v1/alerts/` | V_OPEN_ALERTS | Existing supplied alert/reference/status fields |

These are proposals for team approval, not existing endpoints. Use an authenticated backend-only role/client, require authorization on all three paths, and verify anonymous access is rejected. Keep client secrets/tokens only on the Flask server in ignored/private configuration. Do not automatically REST-enable entire tables: that could expose extra fields and write methods. Exclude STAFF/PASSWORD_HASH and patient NHS identifiers from the integration. Agree field selection, retention and timestamps/timezone with Maham before implementation.

Start with GET only. No insert/update/delete handlers, no registration writes, no band changes, no schema alterations, no execution of Pulse.sql and no changes to grants/settings were performed. Authentication setup and publishing new protected endpoints would change access permissions, so they require a separate explicit approval before any remote action.

After publishing, test HTTP authorization, actual JSON fields/nulls/timezones and connect Python to those agreed endpoints using the existing mapper. Keep Oracle IDs separate from synthetic demo IDs; do not silently mix real database rows with demo mutations. Writes, shared messaging and lifecycle changes require a separate agreement with Maham/backend ownership.

Official background: [Oracle ORDS resource/catalogue patterns](https://docs.oracle.com/en/database/oracle/oracle-rest-data-services/24.4/orddg/developing-REST-applications.html) and [SQL Developer Web from APEX](https://docs.oracle.com/en/database/oracle/apex/24.1/aeutl/accessing-sql-developer-web-from-sql-workshop-menu.html).

## Python bridge prepared locally

`pulse/oracle.py` reads those proposed paths using a server-side OAuth client. It rejects redirects/foreign pagination, preserves missing measurements, and reports failures without replacing them with demo rows. `/staff/database` displays mapped records separately from the existing synthetic workflow. It is restricted to loopback and the demo staff role; this is not production authentication.

Private configuration: `.secrets/oracle.json` with `client_id` and `client_secret`, or `ORACLE_CLIENT_ID` / `ORACLE_CLIENT_SECRET` environment variables. No credentials are included in source. Tokens remain in server memory. Configuration alone does not mean connected: all three GET requests must succeed.

`integration/ords_read_api.sql` is the reviewable proposed GET-only setup. It guards the schema and existing object names, protects the module before publishing, excludes NHS numbers and staff passwords, and never alters Maham's tables. It has not been executed or validated on Oracle. A read-only SQL preflight in APEX found no module, role or client with the proposed Pulse names. A client must still be registered and granted the single reader role, followed by anonymous-denial and authenticated-response checks. No live backend connection is claimed yet.

Database timestamps are displayed without inventing a timezone. Confirm the timezone with Maham before calculating waiting durations or data freshness. Existing database assignments alone do not prove a device is connected.
