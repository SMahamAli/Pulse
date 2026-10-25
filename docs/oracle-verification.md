# Oracle bridge verification — 24 October 2026

## Current result after Maham's update — 25 October 2026

The protected reader now succeeds: **11 patients, 11 latest readings, 10 alerts**. Token/resource requests succeeded; separate anonymous requests to all three resources returned **401**. No private credentials or raw record dumps were printed. Actual counts can change.

Initial readings GET returned 500. Direct SQL reported ORA-04063 for V_LATEST_VITALS; USER_ERRORS identified removed RESP_RATE. The new VITAL_READING table also has no SPO2 column. Only our existing GET handler was changed to select heart rate/skin temperature through active assignments, returning SQL NULL for unavailable SpO2. Maham's table/view definitions and repository SQL/notebook were untouched.

Latest records are selected per assignment using recorded time and reading ID to break ties. The page matches patient AND assignment, reports missing SpO2 honestly and does not infer device connectivity or timezone. A repeated browser-role change was resolved by re-entering demo staff; roles are shared across this browser's tabs.

Final automated checks: **167 passed in 101.50 seconds**, including 12 browser flows. Ruff lint, formatting (25 files), syntax compilation and whitespace checks passed. Two new cases verify that another or missing assignment cannot receive a displayed reading. GitHub CI has not run. Live Chrome showed the connected data page; these remain stored demonstration data, not a verified hardware stream or persistent website workflow.

The older results below are historical and superseded by this section.

Executed locally:

- `python -m pytest -q -m "not browser"`: **118 passed**, 9 deselected.
- `python -m pytest -q -m browser`: **9 passed**, 118 deselected. Uses isolated test services, not the private Oracle connection.
- `python -m ruff check .`: passed.
- `python -m ruff format --check pulse tests app.py`: 23 files already formatted.
- `python -m compileall -q app.py pulse tests`: passed.
- Broad `ruff format --check .` also inspected Elysha's original notebook and reported it would reformat that file. The notebook was preserved unchanged; application formatting passes.
- Flask restarted successfully at `http://127.0.0.1:5000`.
- Signed-in APEX read-only preflight returned no matching proposed Pulse module, role or backend client. No remote writes executed.

New automated coverage: supported field mapping, null measurements, unchanged timestamp strings, GET-only resource reads, token reuse, pagination, rejecting foreign/repeated links, sanitised access errors, missing configuration, demo-role restrictions and loopback restriction. These checks do not prove production identity security or a working live Oracle endpoint.

Still awaiting execution: protected API setup, backend client creation, anonymous access denial, authenticated live HTTP reads, and live Oracle page inspection. The setup SQL has not been executed on Oracle. GitHub CI has not run.

## Activation follow-up (supersedes the pending setup above)

- User explicitly approved API and backend-client creation.
- Protected GET-only API setup processed successfully in Oracle. Only new ORDS metadata/client permissions were created; source tables/views were untouched.
- Backend credential saved privately; `git check-ignore .secrets/oracle.json` confirms it is ignored.
- Token request: HTTP 200. Anonymous patient resource: HTTP 401 (browser and Python).
- Authenticated GETs for patients, latest readings and alerts: HTTP 403, with Oracle reporting missing/inaccessible source tables or views.
- Direct SQL confirmed PATIENT/V_CURRENT_PATIENTS missing. USER_TABLES listed six tables, unlike the earlier inspection. The reason for the schema change is unknown.
- Do not claim live record loading passed. Source-object restoration/completion belongs to Maham and was not performed. Flask displays an explicit error without mock fallback. GitHub CI has not run.

Final local regression run: `python -m pytest -q` — **129 passed in 38.44 seconds**, including 9 browser checks. Ruff lint, application formatting (23 files) and syntax compilation passed. A live Chrome inspection confirmed the configured-but-unavailable state without substitute patients; the final database object query still returned six tables and no views. Mohammed confirmed Maham is updating the database. Screenshot: ignored `test-results/oracle-status.jpg`. Flask remains running locally. No push or merge performed.

Maham's `Pulse.sql` and Elysha's notebook have no Git diff. No schemas, migrations, tables or sample clinical thresholds were changed.
