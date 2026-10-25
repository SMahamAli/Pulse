# Pulse website overview

Latest AI addition: **Staff > AI research** prepares Elysha's newly added Random Forest script and runs actual inference on its held-out synthetic test rows. `pulse/assessment.py` is the website adapter, not a second model. Install `requirements-ai.txt` for this preview. Preparation is cached until restart. Patient/Oracle records are not model inputs yet because required clinical fields and identity mapping still need team agreement. The earlier notebook now lives at `model/AI_Training_backup.ipynb`.

Pulse helps A&E patients share information while waiting and gives staff a place to review visits, readings and requests. Mohammed owns the website, Mostafa the hardware, Maham the Oracle database and Elysha the AI research.

## Screens

| Role | Navigation | Purpose |
| --- | --- | --- |
| Patient | Home, My visits, Hospitals, Chat, Devices | Current visit, earlier forms, postcode search, human conversations and device information |
| Staff | Home, Patients, Chat, Devices, Alerts | Shift summary, patient workflows, conversations, band inventory and review items |
| Admin | Home, Staff & admin access, Login activity, Chat | Demo profile management, recorded demo activity and portal support |

Home and My visits have different jobs. Staff Home contains summary counts and review links, without duplicating the patient table. Patients contains two explicitly labelled source tabs: Demo workflow and Oracle records. The separate Security page was removed; existing request/role/CSRF protections remain. Contextual back links lead to the parent workspace without requiring JavaScript.

Chat is one entry point. Patients choose care staff or administration; staff choose patient conversations or administration; admins choose patient support or staff. Care messages stay linked to visits and preserve symptom-review rules. Administrative support does not give admins access to clinical patient details. An admin can contact a demo patient using a known portal reference. This is human messaging, not an AI chatbot.

## Technology and design

Python Flask serves Jinja HTML templates and CSS, with SVG icons/charts. No application JavaScript is served. The charcoal/red Pulse design includes a decorative heartbeat, accessible status text, focus indicators, subtle card transitions, reduced-motion support and a pause control. The waveform is not a measured heartbeat.

pytest checks services and routes. Python Playwright exercises the browser with JavaScript disabled. Ruff checks Python, and GitHub Actions is configured for checks without deployment.

## Data flow and provenance

- Demo forms call Python routes, then DemoService in pulse/services.py. Synthetic records live in pulse/fixtures.py; templates do not import fixtures. A stable patientId owns separate visit references. Selecting a hospital reuses a draft or starts a new visit without changing past forms/arrival/device assignments.
- Patient history contains the selected hospital, status and original intake. Form submission is planned attendance, not physical check-in. Waiting starts only at staff-confirmed arrival. Closing releases the band.
- Oracle records come through pulse/oracle.py and the protected read-only ORDS API, then pulse/oracle_mapping.py maps names/IDs/fields. The checked dataset returned 11 current patients, 11 readings and 10 alerts. Names and IDs were compared with the raw Oracle source and matched. These are stored demonstration records, not a verified live sensor feed.
- Alex/Jamie and the other workflow patients are separate fictional fixtures. They are not claimed to be the same people as the Oracle patients. Forms, chat and staff demo mutations are not yet written to Oracle.
- Heart rate and skin temperature are supported. The team removed oxygen saturation from cards, forms, fixtures, mappers, API output and Garmin requests. Maham's original repository SQL and Elysha's notebook were preserved.
- Optional Garmin owner preview reads synced heart-rate samples/statistics on the server. It does not pair a watch or assign that owner's data to a fictional patient. Other wearable integrations remain unavailable.

## Integration responsibilities and limitations

Maham owns schema changes. The website's GET handler selects supported readings through active assignments; it does not repair/replace her invalid legacy latest-vitals view. Mostafa and the backend owner must agree authenticated ingestion, assignment IDs, units, timestamps and connection evidence. Elysha must supply an agreed inference interface and actual model results; a notebook is not a deployed model. Clinical staff decisions stay separate from model suggestions.

Demo role entry is public, not real authentication. Private Oracle/Garmin credentials stay outside Git. Oracle preview is loopback-only until real identity and permissions are implemented. Demo state survives refresh but reset/restart clears it; separate browsers do not share demo records. Live crowding, durable form/chat writes, hardware ingestion, AI inference, production identity/deployment and clinical/privacy review remain unfinished. Fewer waiting people do not guarantee faster or suitable care.

See README.md for simple run steps, manual-testing.md for executed checks, and INTEGRATION.md for the remaining contracts. Local passes are not evidence that GitHub CI has run.
