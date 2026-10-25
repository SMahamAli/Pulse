# Team synchronization — 24 October 2026

## Git actions actually completed

Fetched origin, inspected every added path and the upstream README, protected the local README and identical untracked SQL, then ran **git pull --ff-only origin main** on `feature/pulse-flask`. The branch fast-forwarded to **54fcf11**. There was no merge commit, push or automatic publishing. Local Python files were preserved.

There is one active README, at the project root. Earlier team text is preserved in `history/previous-website-notes.md` and `history/team-project-notes.md`, named as archived notes to avoid confusion. The root README combines the team's project title, event, full collaborator names and Oracle/APEX detail with the real Python/Flask run commands and accurate limits. The team's original text is preserved verbatim in its history copy.

## Actual new files and README changes

- **AI_Training.ipynb** added by the team: a Python 3 notebook with 22 code cells. All execution counts are null and there are no saved output blocks in this commit. It was inspected, not executed or modified.
- **Pulse.sql** remains the same Oracle schema/seed/views already inspected. Its blob is unchanged (`46aa4fba570e2013e716d80757eb8f855c7debb9`). Pull now tracks it normally.
- **README.md** adds project/hardware information, collaborator names, demo account rows and a draft data/privacy section. The upstream Website and AI Training stack entries were empty; the local README now identifies the actual Flask website and links the notebook. Upstream data/privacy text ends mid-sentence; the short local note states what is actually synthetic and what dataset is not included.
- No new deployed API, exported model, Oracle connection module or hardware transmitter source was present in this fetched tree. Hardware listed in the README is a team description, not hardware verified by website tests.

## What the notebook actually does

It uses pandas/NumPy and scikit-learn, with Google Colab file upload and Matplotlib plotting. It expects a separately uploaded MIMIC-IV-ED demo ZIP, using Colab paths. It explores ED-stay duration regressors, initial acuity classification and observation anomaly detection. Later cells create a sensor-aligned heart-rate/SpO2 anomaly table and graph. Train/test splits group records by patient.

The final review-table fields include **stay_id, charttime, heartrate, o2sat, anomaly_score, missing_sensor_data, dashboard_message**; the underlying review dataframe also carries a demo_flag. There is no Flask/FastAPI service or model-export call in the notebook. This commit provides no recorded training results, so no accuracy, clinical validity or completed runtime assessment is claimed.

`pulse/ai_mapping.py` is a tested **proposal** to translate a JSON row shaped like that review table. It is not imported into the live assessment path. Dataset stay IDs remain separate from Pulse visit IDs; missing metrics remain null. Scores are not confidence or urgency. It does not invent priority, diagnosis, routing or wait estimates.

## Decisions that need the team

1. **Model purpose:** Elysha should confirm which experiment is being delivered. Total/remaining ED stay to departure is not time until a clinician sees someone. Statistical anomaly is not clinical urgency. Do not put these values into the patient waiting estimate or treatment priority automatically.
2. **Model handoff:** agree model artifact/API, exact inputs/units/timezone, dataset-to-live visit identity, version, missing-data handling, failure states and review semantics. The website remains pending/synthetic until an actual result is supplied.
3. **Metrics:** upstream README/SQL include respiratory rate/falls/accelerometer, while the latest agreed website scope contains temperature, heart rate and SpO2 only. Mostafa/clinical/AI teammates must explicitly confirm changes before those extra features appear in the website.
4. **Authentication:** upstream SQL account rows are demo seed data. The website uses labelled public demo entry and does not accept those credentials as real accounts. Agree production identity/role enforcement separately.
5. **Persistence/backend:** Maham owns Oracle schema changes. Assign backend/API integration ownership and reconcile pre-arrival visits, messages, symptom history and real permissions. Flask web routes are not already an Oracle or hardware API.
6. **Privacy:** notebook research data and fictional SQL/web fixtures have different provenance. Do not copy uploaded research/patient data into frontend fixtures or claim all future data is fictional. No raw dataset was pulled or processed.

## No authored JavaScript in the active project

`static/location.js` was removed; templates have no script tags or event-handler attributes. Hospital area selection is a Python GET form. It is a display fallback, not geocoded search; browser location/distances are explicitly unavailable. CSS/SVG animate the heartbeat, and all application logic/tests are Python. HTML/CSS are still the browser interface languages.

The recoverable React snapshot was moved out of this project to **C:\Users\moham\OneDrive\Desktop\Pulse-React-backup** (34 files, including its SHA-256 manifest). Old generated node_modules, dist and .vite folders were removed from this project; they are not needed by Flask. Python Playwright's bundled third-party browser tooling is not authored application JavaScript. No Node/npm command is required.

## Final checks

All 35 Python tests, Ruff lint/format and syntax compilation passed. The Desktop backup still matches all 33 source hashes. Pulse.sql matches the upstream raw blob; AI_Training.ipynb matches the upstream Git-normalized blob (Windows checkout normalizes line endings). `git diff -- AI_Training.ipynb Pulse.sql` is empty: neither teammate file was edited. Flask responds at port 5000. No push or GitHub CI execution occurred.
