# Flask migration record

## What changed

The active website has moved from React/Vite to Python Flask with server-rendered Jinja HTML and the existing black/red CSS. Core workflows, fixtures, Oracle JSON mappings and tests are now Python. No Node/npm command is required for the Flask application. The active application has no authored JavaScript files or script tags; Python browser tests disable JavaScript entirely. Hospital area selection is a Python form, with automatic location/distances unavailable.

Use this presentation description: **“I used Python Flask for the website logic and backend, Jinja HTML templates and CSS for the interface, and Python for testing.”** HTML and CSS do not become Python. The decorative heartbeat uses CSS/SVG and is not ECG data.

## Preservation

- Branch: `feature/pulse-flask`; later fast-forwarded to the team commit `54fcf11` with `git pull --ff-only origin main`. No merge commit or push was made.
- The Desktop folder `Pulse-React-backup` holds the previous source, tests, package manifest/lock, Vite/Playwright/ESLint configuration, README and documentation, outside the active project.
- `Pulse-React-backup/MANIFEST.sha256` records those files for verification. They are preserved unchanged and are not part of the active runtime.
- Maham's root `Pulse.sql` remains byte-for-byte unchanged; no schema or database was created/executed.
- Old generated node_modules, dist and .vite folders were removed after the script-free team sync. The source backup remains separate on the Desktop.

The archive is a recoverable source snapshot, not a Git commit checkpoint. To try the old version separately, open a terminal in the Desktop `Pulse-React-backup` folder, install Node dependencies there with `npm.cmd ci`, then use its old README. Do not mix the two versions' startup commands.

## Behaviour changes you must understand

- Pages are real Flask GET routes and actions are server-side POSTs. Standard forms reload/redirect; filters have an Apply filters button.
- In-memory demo state is on the Python server, keyed to a browser cookie. Refresh retains it; same-browser tabs share it. Reset or server restart clears it. Different browsers/devices have separate demo instances.
- There is a local Python server now, but Oracle, physical sensors, live hospital data and Elysha's model are still unconnected.
- Python request guards restrict demo actions by selected role/visit and use CSRF tokens. Public role entry remains available, so this is not secure authentication. Admin profiles remain simulated.
- New symptom review/reply, band assignment/closure, stale/missing data and staff-assisted no-email registration are retained. Conversations are opened from patient details as a separate Flask page.
- No npm build is needed. Python syntax, Ruff and pytest replace JS lint/build/unit commands. Python Playwright is the single browser test tool.

## Current structure

- `app.py`: local entry point, http://127.0.0.1:5000/.
- `pulse/__init__.py`: Flask app factory, routes, form validation/guards and rendering.
- `pulse/services.py`: replaceable mock workflow service, process lock, pending-only assessment seam.
- `pulse/fixtures.py`: synthetic data.
- `pulse/display.py`: waiting/freshness/graph calculations.
- `pulse/oracle_mapping.py`: actual Oracle-view JSON conversion preparation, not a DB client.
- `templates/`: login, registration, intake/review, hospitals, patient, staff/details, messages/symptoms, alerts, devices, admin and reusable macros/base.
- `static/`: CSS and SVG icons/favicon only; no JavaScript.
- `tests/`: Python service/display/mapping, Flask route, theme contrast and Playwright browser tests.
- `requirements*.txt`, `pyproject.toml`: Python dependencies/tool settings.
- `.github/workflows/ci.yml`: Python checks and Chromium tests; no deployment and no GitHub result claimed.

## Checks and limits

See `manual-testing.md` for checks actually run. Manual checks across every real browser/device, screen reader, production deployment, secure multi-user sessions, Oracle transactions, hardware ingestion and model performance remain untested. The Python migration cannot establish any clinical/security validation.
