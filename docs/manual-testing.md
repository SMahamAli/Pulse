# Python migration checks and manual test record

## Current navigation and presentation review

Final follow-up: **179 tests passed in 47.38 seconds**, including 13 browser flows, with lint/format/compile/whitespace checks passing. An additional regression verifies that a blank Oracle acknowledgement actor is shown as unavailable rather than a named reviewer. Internal database table names were removed from the product's summary cards; source provenance remains explicit. The scan of shareable files found no configured private key values, one README, and no diff to the team's SQL/notebook. This is the final count for this review, superseding 178 below.

**178 tests passed in 38.13 seconds**, including 13 Chromium flows with JavaScript disabled. Ruff lint, formatting (26 Python files), syntax compilation and Git whitespace checks passed. This supersedes the older totals and navigation/metric descriptions below. GitHub CI has not run.

| ID | Feature | Steps | Expected result | Actual result | Status |
| --- | --- | --- | --- | --- | --- |
| NAV-01 | Unique role navigation | Enter each role and inspect/click its sidebar | Patient Home/My visits distinct; one Chat; no duplicate staff patient menus | Role navigation assertions and browser matrix passed | Pass |
| NAV-02 | Staff Home/Patients | Open summary, then patient source tabs | Home has counts/review links; Patients owns workflow table and Oracle tab | Route assertions and browser navigation passed | Pass |
| CHAT-01 | Care/admin channels | Patient/staff open Chat, send/reply/read in each channel | Correct human conversation, visit reviews preserved | Browser and service round trips passed | Pass |
| CHAT-02 | Admin initiates patient chat | Chat → Patients, known portal reference, send; switch to patient and reply | Support visible to matching patient; no clinical admin access | Added route and mobile browser tests passed | Pass |
| BACK-01 | Contextual back links | Open conversation, intake, detail, device preview and admin features | Parent link returns to relevant workspace, without JavaScript | Channel route checks and browser Back to Chat flow passed | Pass |
| METRIC-01 | Removed metric | Browse care/device/intake views and exercise Garmin provider | Only heart rate/temperature displayed; no obsolete request | Absence assertions, mapper/transport and browser tests passed | Pass |
| DATA-01 | Source identity | Fetch Oracle and compare mapped names/IDs with raw patient rows | Exact source identity, no fixture substitution | Actual check matched all 11 patients; 11 readings and 10 alerts loaded | Pass |
| UI-02 | Motion/mobile | Inspect Chat at 390×844; use reduced-motion browser mode | Readable cards/back link, no main overflow | Screenshot inspected and browser geometry check passed | Pass |

The existing read-only API handler was narrowed to patient/assignment/time, heart rate and skin temperature. No database table/view, credential or privilege was changed. Maham's repository SQL and Elysha's notebook remain unchanged. Core flow tests still cover registration, hospital selection, intake, history, check-in, assignment, readings, symptoms/review, replies and closure. External hardware/model inference, persistent form/chat writes and production authentication remain unimplemented; no clinical validation, deployment or GitHub CI success is claimed.

## Latest Oracle read verification

After Maham's update, actual authenticated requests loaded **11 current patients, 11 latest readings and 10 alerts**. All three anonymous GETs returned 401. An invalid old reading view referenced removed RESP_RATE; our read-only API handler was adapted to existing heart-rate/skin-temperature columns without changing her tables or view. SpO2 remains unavailable. Website forms/messages/band actions are still local demo data.

| Test ID | Feature | Steps | Expected result | Actual result | Pass/fail |
| --- | --- | --- | --- | --- | --- |
| ORA-LIVE-01 | Protected reads | Fetch all three resources through OracleService | Source rows, no fallback data | 11 / 11 / 10 records loaded | Pass |
| ORA-LIVE-02 | Anonymous requests | Request each resource without credentials | No records disclosed | HTTP 401 on all three | Pass |
| ORA-LIVE-03 | Reading source compatibility | Inspect columns/view errors; adapt our GET handler | Supported fields only, no schema edits | HR/skin temperature loaded; SpO2 NULL/unavailable | Pass |
| ORA-LIVE-04 | Correct assignment | Present same-patient reading from wrong/missing assignment | Reading not displayed against another assignment | Two added regression cases passed | Pass |
| ORA-LIVE-05 | Browser display | Enter Demo staff and open Oracle patients | Connected status, records and source labels | Live Chrome connected page verified | Pass |

Final suite: **167 passed**, including 12 browser flows; lint, formatting, compilation and whitespace checks passed. This supersedes PENDING-01 and the earlier 165-test count below. Actual hardware/model/write integration, timestamp timezone and production identity remain unverified. No push, merge or GitHub CI run.

## Current patient-flow and controls review

Final executed checks: **165 passed** with `python -m pytest -q` (153 non-browser cases and 12 Chromium flows), 116.83 seconds. Ruff lint, Ruff formatting (25 Python files), Python syntax compilation and `git diff --check` passed. These are local results; GitHub CI has not run. An earlier full run found the Garmin local-midnight/UTC date mismatch; it was fixed and a deterministic regression test added before the final passing run.

| Test ID | Feature | Steps | Expected result | Actual result | Pass/fail |
| --- | --- | --- | --- | --- | --- |
| VIS-01 | Hospital choice for existing patient | Demo patient → Hospitals → LS6 → Start a new visit here | Enabled choice; new intake; old checked-in visit unchanged | Passed route/service checks and desktop/mobile browser clicks | Pass |
| VIS-02 | Registration and forms | Register fictional patient; test errors; select hospital; review, edit and submit | Helpful errors, correct hospital/form; no passwords retained; no physical check-in | Automated checks passed | Pass |
| VIS-03 | My visits | Open history; expand both forms; View visit; close new visit; plan another | Only own visits; correct hospital/status/form; original visit preserved | Passed at 1440×960 and 390×844 | Pass |
| VIS-04 | Draft reuse | Select hospital again before submitting | Reuse unfinished draft; no duplicate unsubmitted visit | Service/route regression passed | Pass |
| VIS-05 | Staff workflow | Search new reference; intake; confirm arrival; assign; simulate; close | Waiting starts at arrival; exclusive band; release on closure | Full patient/staff browser flow and service tests passed | Pass |
| BTN-01 | Care messages and retry | Send general/help; mark read/reviewed; simulate one failure; retry; reply | Correct conversation/state; retained draft; no duplicate send | Browser and route checks passed; failure test is under Demo testing tools | Pass |
| BTN-02 | New symptoms | Submit change; staff reviews and responds | Original form preserved; timestamped update/message/alert | Automated checks passed | Pass |
| BTN-03 | Staff action forms | Submit review, category/reason, destination, note, acknowledgement; reject invalid IDs/empty values | Expected state changes or usable validation page; no partial updates | 22 control-audit cases passed, including stale form after reset | Pass |
| BTN-04 | Admin/support | Create staff/admin profiles; activate/deactivate; start/read/reply to support | Admin workspace stays separate; correct replies/unread states | Browser and route checks passed | Pass |
| BTN-05 | Navigation/download/session | Click every role's sidebar links; download CSV; logout/switch/reset | Valid destinations, CSV, usable role entry; no server errors | Chromium navigation matrix and internal-link crawl passed | Pass |
| UI-01 | Responsive and keyboard | Desktop/mobile new flow; keyboard hospital choice; pause animation; inspect screenshots | Readable cards/forms, no main overflow, keyboard operation | Browser geometry checks and visual screenshot inspection passed; mobile banner adjusted | Pass |
| EXT-01 | Garmin without live credentials | Disabled configuration or HTTP double; submit default date across local/UTC midnight | Honest unavailable state or supplied test readings; valid default date | Unit/route/browser tests passed; no real Garmin request made in this review | Pass |
| EXT-02 | Oracle page without live database calls | Isolated unconfigured/fake service in tests | Status/error visible; no mock fallback for failed Oracle request | Existing Oracle client/route tests and navigation check passed | Pass |

Still awaiting external/manual verification:

| Test ID | Feature | Steps | Expected result | Actual result | Pass/fail |
| --- | --- | --- | --- | --- | --- |
| PENDING-01 | Updated Oracle tables | After Maham finishes, retry protected read API and compare records | Correct real database rows/nulls/times | Paused at the user's request; not retested | Not executed |
| PENDING-02 | Hardware/model | Agree and connect real ingestion/model services | Supplied readings and model states, without fabricated output | Not connected | Not executed |
| PENDING-03 | Live external services | Recheck other postcode districts, directions and optional owner Garmin account | Provider response/link behavior verified | LS6 and automated doubles tested; external services not comprehensively checked | Not executed |
| PENDING-04 | Other platforms/accessibility | Fresh teammate Mac/Linux setup, other browser engines, screen reader | Installation and usability checked | Windows local Python/Chromium verified; broader manual checks still needed | Not executed |

This is ready for a **demo code review**, not a completed hospital deployment. No real hospital is notified. Demo roles are not real authentication. Separate browsers remain isolated and reset/restart clears memory. The historical results below describe older versions and are superseded by this section.

## Latest real Garmin verification: success

The user supplied the exact credential as text, correcting screenshot transcription errors. Official token, daily heart-rate and daily SpO2 endpoints returned **HTTP 200**. Timestamped HR/history and supplied daily HR statistics were available; no timestamped SpO2 sample was returned. The running website rendered the real owner preview successfully in an isolated local session, then Stop/Clear was executed. No key/token/raw measurement value was printed or saved in screenshots. This supersedes the earlier 401/empty-key notes below. No application code changed for this credential correction; automated tests were not rerun. The last full synthetic suite remains 117 passing tests. The secret is ignored and untracked, and no push/merge was performed.


## Retest with the latest supplied Garmin screenshot

Updated the differing character visible in the clearer screenshot in the ignored local secret file. A request to the official Garmin token endpoint again returned **HTTP 401 Unauthorized**. Heart-rate/SpO2 endpoints were not reached, and no health values or tokens were displayed or saved. Screenshot transcription ambiguity versus invalid/revoked credentials remains unresolved. No application code changed, so automated tests were not rerun for this credential-only check.


## Latest real Garmin access attempt

At the user's explicit request the screenshot-transcribed credential was placed only in the ignored local key file. The official Garmin token endpoint returned **HTTP 401 Unauthorized**. No key/token/vendor response body was printed, and no health readings were fetched. Actual account integration remains **blocked by rejected credentials**; screenshot transcription versus validity/revocation cannot be distinguished from that response. Prior synthetic test passes do not prove real Garmin access. No source-code changes were needed for this configuration check; existing automated tests were not rerun.


## Garmin synced-readings update

Final suite: **117 passed** (108 non-browser cases, 9 Chromium flows), 37.85 seconds, using fictional credentials/HTTP responses. Ruff lint/format (21 Python files), compilation and Git whitespace checks passed. The full run used a fresh validated ignored workspace basetemp to avoid the known Windows temporary-directory permission conflict. No GitHub CI run is claimed.

| ID | Feature | Steps | Expected result | Actual result | Pass/fail |
| --- | --- | --- | --- | --- | --- |
| READ-01 | Official field mapping | Map reordered HR descriptors, null gaps, latest SpO2 UTC time, supplied HR stats, future/invalid values | Latest timestamped values; missing stays unavailable; no temperature invention | Mapper tests passed against synthetic DTO-shaped payloads | Pass |
| READ-02 | Server transport | Token then fixed HR/SpO2 GET endpoints; repeat fetch; revoke/partial error/rate limit | Server-only bearer reuse; no raw credential/error exposure; cooldown on 429 | HTTP-double tests passed | Pass |
| READ-03 | Preview and polling | Start locally, GET twice within 30 seconds, fail next retrieval, stop/clear | Native refresh; no excess request; retained samples keep old time; cleared on stop | Route tests passed; no visit/snapshot/cookie health-data changes | Pass |
| READ-04 | Local/role boundaries | Admin or external remote address attempts preview; invalid date | Rejected; no public owner-preview access | Route tests passed; not production authentication proof | Pass |
| READ-05 | Mobile display | Show HR, stale SpO2, unavailable temperature, statistics and trend at 390x844; stop | Honest source/times/age, no synthetic labels on owner page, no overflow | Chromium test passed; only synthetic-data screenshot inspected | Pass |

Garmin's official public OpenAPI schemas and client endpoints were inspected. The actual account remains **unverified** because the local key source is empty. No real measurement values, key or tokens were printed/saved in test artifacts. No true live sensor stream, guaranteed watch sync delay, public multi-user authorization, Oracle persistence or model ingestion was implemented. The page reads latest synced cloud values only after the owner configures a valid key locally.

## Garmin access-check update

Full verification: **109 passed** (101 non-browser cases and 8 Chromium flows), 20.83 seconds. Ruff lint/format (19 Python files), syntax compilation and whitespace checks passed. The full run used a new ignored `test-results/pytest-garmin-<unique-id>` basetemp folder to avoid a local Windows permissions conflict; no existing temporary directory was deleted. No GitHub CI result is claimed.

| ID | Feature | Steps | Expected result | Actual result | Pass/fail |
| --- | --- | --- | --- | --- | --- |
| GARMIN-01 | Secret loading | Fictional local key file; environment override/empty; invalid header characters | Server-only key source, clear unavailable state, no network if absent | Python tests passed | Pass |
| GARMIN-02 | Token exchange | Fake plain-text/JSON token replies; expired/malformed tokens; timeout, rejection and rate limit | Metadata only, safe errors, no redirect or token cache | HTTP test doubles passed; no real key used | Pass |
| GARMIN-03 | Data separation | Patient checks access; inspect response/cookie/demo snapshot; admin attempts check | No key/token in HTML/cookie/snapshot; no change to readings; admin rejected | Route tests passed | Pass |
| GARMIN-04 | Mobile Devices | Open Garmin card at 390x844, submit without key, expand setup | Clear error/setup; watch unverified and metrics unavailable; no overflow | Script-disabled Chromium test passed; screenshot inspected | Pass |
| GARMIN-05 | Git hygiene | Check .secrets/key and common token-cache filenames | Ignored; no supplied credential in source | Ignore checks passed; original SQL/notebook unchanged | Pass |

The first browser run failed in fixture setup because of a Windows pytest temporary-directory permission conflict. Browser fixtures now explicitly disable real credentials without needing that directory; the final full suite used a fresh validated workspace temp path and passed. No live Garmin token exchange, health-data endpoint, watch connection, metric mapping or account-to-visit association was tested. The supplied chat key was not copied or used. An owner-controlled replacement must be configured locally before a real access check. See garmin-setup.md.

## Dedicated admin and support update

Final full suite: **91 passed** (84 non-browser cases and 7 Chromium flows), 24.51 seconds. Ruff lint/format (17 Python files), syntax compilation and Git whitespace checks passed. Browser tests disable JavaScript. No GitHub CI run or push/merge is claimed. SQL and notebook remain unchanged.

| ID | Feature | Steps | Expected result | Actual result | Pass/fail |
| --- | --- | --- | --- | --- | --- |
| ADMIN-01 | Admin navigation | Enter demo admin; inspect overview, access, activity, security and support | No clinical sidebar or Register patient action | Browser test passed; desktop/mobile screenshots inspected | Pass |
| ADMIN-02 | Route/action separation | Request clinical routes/actions directly as admin | Reject without changing visits/devices/alerts/readings | 16 parameterised route/action cases passed; demo boundaries only, not real authentication proof | Pass |
| ADMIN-03 | Profiles/activity | Create staff/admin record, duplicate email, activate/deactivate; export activity CSV | Profiles update; duplicate rejected; actual demo events exported without passwords/form data | Service/route/browser tests passed | Pass |
| ADMIN-04 | Patient/admin support | Patient opens request; admin reads/replies; patient marks reply read | Correct thread, sender/time, unread/read changes; clinical inbox unchanged | Service/route/browser tests passed | Pass |
| ADMIN-05 | Staff/admin support | Admin starts staff request; staff replies; admin sees reply | Shared conversation within same browser demo only | Service/browser tests passed | Pass |
| ADMIN-06 | Support boundaries/errors | Wrong patient/role, forged sender, empty/overlong text, HTML payload, failed-send retry | No cross-thread access; sender from session; escaped text; retained retry without duplicate | Python route/service tests passed | Pass |
| ADMIN-07 | Security status/forms | Read implementation/status page; send invalid non-ASCII CSRF | Realistic implemented/missing states; invalid token returns 400 and records rejection | Browser/route tests passed | Pass |

Activity is capped at 200 local events and cleared by reset/restart. Support uses role inboxes, not authenticated individual accounts. Profile toggles do not revoke public demo entry. No real MFA, password reset, production identity security, durable audit or cross-device delivery was tested. Full screen-reader/keyboard traversal, other browsers and physical-device checks remain awaiting execution.

## Search-only hospital page update

Removed Riverside/Northgate from runtime fixtures and moved seeded visits/staff heading to Leeds. Removed the old area selector, preloaded cards and map placeholder. Initial GET now displays only the postcode form; submitting LS6 displays the two Leeds results. Updated core/assisted browser journeys and added a regression assertion for zero hospital cards before search. All 67 tests passed in 12.39 seconds, including 6 Chromium flows with JavaScript disabled. Ruff lint/format and Python compilation passed. Historical sections below describe earlier versions. No SQL/notebook changes, push or merge.

## Postcode search update

Final checks: **67 tests passed** (61 non-browser cases and 6 browser flows), 12.46 seconds. Ruff lint/format (16 Python files), syntax compilation and Git whitespace checks passed. GitHub CI has not run for these local changes.

The Leeds NHS emergency department directory was checked for LGI LS2 9DA and St James's LS9 7TF. Postcodes.io coordinates for those destination postcodes and LS6 were retrieved successfully. This verifies locations, not waiting counts.

| ID | Feature | Steps | Expected result | Actual result | Pass/fail |
| --- | --- | --- | --- | --- | --- |
| LOC-01 | Validation/privacy | Submit LS6, full/lowercase postcode, malformed text | Normalize to district only; reject malformed input | Python tests passed; location not added to session/visit and full postcode not rendered back | Pass |
| LOC-02 | Nearby results | Search LS6 with network disabled | LGI then St James's; approximate miles; synthetic 5–10 and 15–20 people; no invented wait | Unit/route/mobile Chromium tests passed | Pass |
| LOC-03 | Selection/check-in | New patient selects LGI; checked-in patient attempts change | Selection opens intake without arrival; existing hospital stays locked | Browser and route tests passed | Pass |
| LOC-04 | Lookup failures | Mock valid response, 404, network failure and no supported sites nearby | Fixed API URL, district only, helpful error or limited-catalogue empty state | Python tests passed; automated tests need no external API | Pass |
| LOC-05 | Mobile | At 390x844 register, search full postcode, inspect results, choose hospital | Readable form/list, no main-area overflow, working selection without JavaScript | Browser test passed; screenshot inspected | Pass |

No live hospital count integration, GPS, route/travel-time calculation or comprehensive hospital directory was added. External directions destinations and physical devices remain awaiting manual checks.

## Latest sharing review (24 October 2026)

This section supersedes earlier counts below. **51 tests passed**: 46 non-browser cases and 5 Python Playwright Chromium cases. The final full run took 11.14 seconds (an earlier complete run also passed in 112.85 seconds). Ruff lint, Ruff format (14 Python files), syntax compilation and `git diff --check` passed. No GitHub CI run or real integration result is claimed.

| ID | Feature | Steps | Expected result | Actual result | Pass/fail |
| --- | --- | --- | --- | --- | --- |
| READY-01 | Complete core flow | Register, hospital, intake review/edit/submit, role switch, check-in, assign, simulate, symptoms, staff review/reply, close | Arrival-based waiting; linked history/messages; band released | Browser and service tests passed with JavaScript disabled | Pass |
| READY-02 | Assisted registration | Staff creates patient without email, selects hospital, records intake, confirms arrival and assigns band | No fake email/account; assigned visit in patient list | Browser test passed | Pass |
| READY-03 | Assistance and alerts | Patient requests help, staff opens Alerts, acknowledges, opens Acknowledged | Request appears; identity/time recorded; acknowledgement separate from review | Browser and service tests passed | Pass |
| READY-04 | Staff controls | Search; status/review/device filters; no-match query; decision with reason; note; confirmed destination | Correct rows, saved staff decision/note, destination visible to patient | Browser and route tests passed | Pass |
| READY-05 | Inbox and review | Patient messages/symptoms; staff reply; general/help review; selected symptom review; patient marks replies read | Human conversation preserved; symptom review separate; no completed model fabricated | Browser and service tests passed | Pass |
| READY-06 | Admin | Create fictional staff, deactivate, activate, reset | Profile updates in demo only, reset removes it | Browser test passed; not real access-control testing | Pass |
| READY-07 | Device evidence | Assign before first reading; simulate; advance clock; inspect disconnected and missing metrics | Awaiting data first, explicitly demo connection, stale after configured interval, no invented zero | Service/browser tests passed | Pass |
| READY-08 | Closed visit | Close twice, advance time, attempt symptom submission | Stable close time, waiting stops, band released, new symptoms unavailable | Route/service tests passed | Pass |
| READY-09 | Invalid forms/retry | Password mismatch; nonnumeric/nonfinite/unknown-type/invalid-time readings; overlong symptoms; failed message retry | Helpful errors, no partial writes, original text retained, successful retry once | Route/service/browser tests passed | Pass |
| READY-10 | Navigation and targets | Follow reachable internal links for each demo role; inspect POST routing | No broken internal links or missing form targets | 3 recursive route tests passed; OPTIONS is routing evidence only | Pass |
| READY-11 | Responsive/keyboard | Chromium 1440x960 and 390x844; keyboard Tab/Space animation toggle; inspect screenshots | Readable layout, main area within viewport, visible status text | Browser checks passed; patient/staff desktop and mobile screenshots inspected. Wide table scrolls within its region and now has a hint/focus outline | Pass for checked screens |
| READY-12 | Contrast and source hygiene | Calculate token ratios; inspect ignored paths and credential patterns | Text pairs >=4.5:1, tested focus/input pairs >=3:1; no authored app JS or bundled local environments | Automated checks passed; credential-pattern scan found no matches in 35 app/config/test files | Pass within these checks |

The first expanded browser runs exposed two inaccurate test locators (assisted button name and note text with timestamp) and an unclear accessible name on the admin role selector. Locators and the selector label were corrected; the complete rerun passed. The project's SQL and notebook remain unchanged. This is not a complete security/secret audit.

Still awaiting: full keyboard traversal/screen-reader audit, physical mobile devices, Safari/Firefox, external directions destination check, and real Oracle/hardware/model/authentication/multi-user tests. External-link syntax is not proof that a real hospital accepts patients. Earlier results below are retained as history.

24 October 2026. Active app: Python Flask, HTML/Jinja and CSS. Python requirements installed in `.venv`; browser tests use Python Playwright Chromium. No Oracle, physical band, wearable vendor, live crowding feed or AI model was connected.

## Executed checks

| ID | Feature | Steps | Expected | Actual | Result |
| --- | --- | --- | --- | --- | --- |
| PY-01 | Core journey | Python browser test: register, select hospital, review/edit intake, check in, assign, simulate readings, report symptoms, review/reply, close/release | Same core patient/staff story works without React | Python Chromium test passed with JavaScript disabled | Pass |
| PY-02 | Mobile/forms | 390×844 patient/staff pages; mismatched registration passwords | No page overflow, readable cards/navigation, clear validation | Browser checks passed; full-page screenshots inspected | Pass |
| PY-03 | Stale/missing/retry | Sam/Casey details; fail next message and retry | Stale/unavailable text, retained composer, one successful retry | Python browser test passed | Pass |
| PY-04 | Workflow rules | Python service tests | Arrival-based waiting, exclusive/released band, immutable intake, linked review items and acknowledgement | Service tests passed | Pass |
| PY-05 | Server forms | Flask test client follows routes/forms and demo role changes | Pages render, validation and CSRF work, no passwords/health drafts in cookies | Route tests passed; these are not real identity/access tests | Pass |
| PY-06 | Sessions/reset | Refresh and two browser-cookie clients | Refresh keeps memory; separate browsers isolated; reset clears | Route test passed | Pass |
| PY-07 | Oracle mapping | Construct JSON rows, invalid/blank numbers and recorded triage | Nulls preserved; no unsupported metrics or invented assessment/timestamp | Python mapping test passed; no Oracle query | Pass |
| PY-08 | Source preservation | Verify archive SHA-256 manifest and SQL blob | Legacy source unchanged and SQL untouched | All 33 legacy files and original SQL blob matched | Pass |
| PY-09 | Theme | Calculate designated CSS token contrast | Text ≥4.5:1; tested form/focus edges ≥3:1 | Python contrast calculation passed; same black/red tokens retained | Pass |

Initial route run caught a no-email normalization error (`None.strip`) in assisted registration. It was fixed, then all 27 initial non-browser tests passed. Initial Python browser run passed all 3 tests; a harmless local pytest cache-directory warning was removed by disabling the optional cache plugin. A contrast test and font-fallback polish were added afterward. Final counts/checks are recorded below after execution.

## Awaiting checks/integration

| ID | Feature | Steps | Expected | Actual | Result |
| --- | --- | --- | --- | --- | --- |
| MAN-01 | Full accessibility | All screens keyboard-only and NVDA/VoiceOver, zoom 200% | Meaningful focus/labels/announcements | No full screen-reader audit | Awaiting |
| MAN-02 | More browsers/devices | Safari, Firefox, iOS/Android physical devices | Responsive usable pages | Chromium desktop/mobile viewport only | Awaiting |
| MAN-03 | External directions | Inspect known-address directions links | Approved destination opens externally | Automatic browser location/distances removed; external destination not manually checked in this review | Awaiting external-link check |
| MAN-04 | Real integrations | Oracle transactions, production auth/scope, hardware reconnect, real model job/error, multi-device sync | Agreed end-to-end behaviour | Not connected; public demo roles remain simulated | Blocked by integration |
| MAN-05 | Clinical/security/privacy | Review actual deployment, data handling and intended clinical scope | Appropriate approved evidence | Not performed; no validation/certification claimed | Awaiting |

No npm/React checks are described as Python checks. The former JavaScript tests and results are preserved only in the legacy archive. Python CI is configured but has not run on GitHub. No deployment, push, merge commit or SQL execution was performed. A later safe fast-forward pull is recorded in team-sync.md.

## Final migration verification

- Full Python suite: **31 passed** (28 service/route/mapping/theme checks and 3 Python Playwright browser smoke tests), 6.65 seconds in the final run.
- Ruff lint and format checks passed for all 11 Python files; Python syntax compilation passed.
- The core browser journey passed with JavaScript disabled and font downloads blocked; mobile screenshots were visually inspected. The CSS/SVG heartbeat and dark/red design were also inspected in live Chrome at http://127.0.0.1:5000/.
- Legacy archive: all **33 source/config/test/doc files** matched `Desktop/Pulse-React-backup/MANIFEST.sha256`.
- SQL: both root file and original Git blob matched `46aa4fba570e2013e716d80757eb8f855c7debb9`; `Pulse.sql` was not modified or executed.
- No GitHub CI execution, push, merge, production deployment or real integration result is claimed.


## Script-free team-sync verification

- `git pull --ff-only origin main` completed to commit **54fcf11**, with local Python work and both README versions preserved.
- All **35 Python tests passed** (32 service/route/mapping/theme/script-free checks and 3 browser smoke tests), 10.43 seconds. Core tests run with scripts disabled.
- Ruff lint/format checks passed for all 13 Python files; syntax compilation passed.
- Added checks verify no authored JS/JSX/TS files or script/event-handler tags in application directories, a working Python manual-area form, and a conservative mapping proposal for the notebook review table. Python browser tests no longer contain JavaScript evaluate expressions.
- No notebook execution, model performance result, Oracle runtime connection, production identity security, GitHub CI result or hardware integration is claimed.
# Oracle activation follow-up — 24 October 2026

| Test ID | Feature | Steps | Expected result | Actual result | Status |
| --- | --- | --- | --- | --- | --- |
| ORA-01 | Private backend authentication | Request client-credentials token from Python | HTTP 200 without logging secrets | HTTP 200; credential file ignored by Git | Pass |
| ORA-02 | Anonymous access | Open patient API without a token | No records disclosed | HTTP 401 in browser and Python | Pass |
| ORA-03 | Source data loading | Authenticated GETs for all three resources | Successful database rows | HTTP 403; PATIENT and dashboard views missing while Maham updates | Blocked |
| ORA-04 | Honest website error | Open Staff → Oracle patients | Explicit failure; no synthetic replacement rows | Browser showed configured connection and resource failure; no patient rows substituted | Pass |
| ORA-05 | Completed source integration | After Maham finishes, refresh and compare rows/readings/alerts with SQL | Matching source records and nulls | Awaiting completed schema and live retest | Not executed |

The API/client setup changes ORDS metadata only. Maham's source SQL and Elysha's notebook remain unchanged. These checks do not establish real user authentication or live wristband transmission.
