# Pulse presentation preparation — Flask version

## Current demo wording

Say: "I worked on the Python Flask website with HTML templates and CSS. Patients have Home, visit history, postcode search and Chat. Staff Home is a summary; the Patients workspace clearly separates the demo workflow from Oracle records. The Oracle tab reads the same names and IDs stored in Maham's database. Our web forms and conversations still use a separate demo service, so I do not claim those writes are integrated. We now display heart rate and skin temperature only. The Pulse animation is decorative. Codex helped implement and test the interface; I reviewed the workflows and integration boundaries."

Use Chat to choose care-team or administrative conversations. Admin has profile management, local activity and Chat; the separate Security page was removed. Earlier scripts below may use the previous navigation names or metric scope; this section supersedes them. Do not claim a fully deployed healthcare system, a live hardware feed, real patient authentication or model accuracy.

## Short explanation

Latest integration status: the protected read-only Oracle API and Python client now load stored demonstration patients, latest readings and alerts. Say "the website can read our Oracle demonstration data through a protected API; the patient workflow still uses a mock service." The updated reading table supplies heart rate and skin temperature, with SpO2 unavailable. This is not evidence of live wristband transmission, real user authentication or completed write/model integration. Garmin remains a separate owner preview.

The site now uses Python Flask for routes, validation, server-side demo records and page rendering. Jinja generates HTML and CSS supplies the black/red interface. Tests are written in Python using pytest and Playwright. No JavaScript is served. Python handles postcode search and approximate distances from a district centre. LS6 works without internet; other districts use Postcodes.io. Automatic browser GPS is unavailable.

## Mohammed's 45–60 second script

> I worked on the website interface for Pulse using Python Flask, HTML templates and CSS, with Codex helping me implement and review it. The patient can choose a hospital, submit symptoms, view visit information and contact human staff. Staff confirm arrival, assign a band, review new symptoms and reply. Waiting starts at confirmed arrival, not registration.
>
> I kept the interface separate from the demo data service and wrote Python tests for the important workflows. Our current readings, counts and model results are clearly labelled samples. Maham's database script is included, while the Oracle connection, Mostafa's hardware feed and Elysha's model still need integration. Staff remain responsible for clinical decisions.

Do not call the frontend language Python alone: say **Python Flask with server-rendered HTML/CSS**. Do not claim to have manually written every line, built teammates' components, connected a live model or secured real hospital access.

## Four-minute team pitch

| Time | Speaker | Content |
| --- | --- | --- |
| 0:00–0:25 | Mohammed | A&E waiting/communication problem and the Pulse idea; hand to Mostafa |
| 0:25–1:05 | Mostafa | Actual hardware/sensors/transmission demonstrated; state what is unfinished |
| 1:05–1:40 | Maham | Oracle schema/views and actual tested/deployed status; API/storage gap |
| 1:40–2:20 | Elysha | Actual model inputs/outputs/evidence; staff review, no invented accuracy |
| 2:20–3:15 | Mohammed | Website script with fast symptom/reply demonstration |
| 3:15–3:45 | Team | Intended band → backend/database → pages/model connection; current limits |
| 3:45–4:00 | Mohammed | Next integration/testing step; close without claiming measured outcomes |

Each owner must confirm their own work/status. The website repository does not establish hardware accuracy, database deployment or model performance. For two-minute Q&A, hand sensor questions to Mostafa, storage to Maham and model questions to Elysha.

## Fast demo

Start `python app.py`, open http://127.0.0.1:5000/.

1. Demo patient → Report new symptoms → enter a fictional change/onset → send.
2. Switch demo role → Demo staff → Symptoms to review → Alex Morgan.
3. Show original intake unchanged → Mark reviewed → Open conversation → reply.
4. Switch role → Demo patient → Messages → show the human reply.

Longer demonstration: register → search LS6 and compare the two Leeds hospitals with simulated waiting ranges → intake review/edit → staff check-in → PB-013 assignment → Devices/simulate readings → patient monitoring → symptoms/review/reply → close/release. Sam shows disconnected/stale; Casey shows missing wearable metrics. Refresh now keeps the Python demo; reset/restart clears it.

## Fallback

Install requirements and start/load locally before the pitch. Fixtures do not require Oracle, band, model, paid APIs or internet; optional fonts fall back to system fonts. Use LS6 postcode search when offline; skip other districts and external directions. Keep screenshots/recording in advance and disclose them as fallback, not a live integration. No offline healthcare functionality is claimed. Confirm the whole team's live integration readiness before presenting it as connected.

## Ten judge questions

| Question | Honest short answer | Confirm with |
| --- | --- | --- |
| What problem does Pulse address? | Patient updates and staff visibility during A&E waiting; no measured wait reduction claimed | Whole team for scope/outcome evidence |
| What did you contribute? | Python Flask website, templates/CSS, demo service boundary and Python tests, with Codex assistance | Team attribution for later changes |
| What languages did you use? | Python for routes/logic/tests; HTML/Jinja and CSS for the browser interface; no authored JavaScript | Repository facts; no teammate needed |
| How do four parts connect? | Intended authenticated server/API ties band, Oracle and model to the website; current site uses demo memory | Mostafa/Maham/Elysha and API owner |
| Is the database connected? | SQL source and Python JSON mappings exist, not a running Oracle connection | Maham/API owner |
| What do tests prove? | Demo workflows, Python routes and browser paths, not medical safety, real security or sensor/model accuracy | Each owner for their own checks |
| What if readings are missing/stale? | Unavailable or timestamped stale/disconnected, never assumed normal; demo freshness rule is not clinical | Mostafa/clinical adviser |
| How are new symptoms handled? | Append history/message/alert, require staff review, preserve intake; reassessment is pending | Elysha for real model reassessment, Maham for persistence |
| Is staff access secure? | Public demo switching is not authentication. CSRF/route guards are only basics; real identity/permissions remain | Production API/security owner |
| What is required before real use? | Agreed integration, safe data handling/retention, deployment, tested access/failures and appropriate clinical validation | All teammates and advisers |


## Optional admin demo

Show that admin has access management, activity, security and support instead of the clinical queue. Send a fictional portal question as patient, switch to admin to reply, then switch back. Explain: public demo roles are not real accounts; access activity records demo events only; support is server-memory data, and clinical messages remain with staff. Confirm backend identity/audit/support persistence ownership with the team.
