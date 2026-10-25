# Running and checking Pulse (Python)

Install Python 3.12+ and open a terminal in this project folder. Node/npm are not needed for the active Flask app.

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000/. Keep the terminal running. Ctrl+C stops it. VS Code is optional.

For an isolated Windows environment (recommended for development):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe app.py
```

On Mac/Linux use `.venv/bin/python` instead. Commands below assume your terminal's `python` points to the environment with the requirements installed; alternatively use that full environment path.

## Python checks

```powershell
python -m pip install -r requirements-dev.txt
python -m ruff check app.py pulse tests
python -m ruff format --check app.py pulse tests
python -m compileall -q app.py pulse
python -m pytest -q -m "not browser"
```

Browser tests (Python Playwright; install Chromium once):

```powershell
python -m playwright install chromium --only-shell
python -m pytest -q -m browser
```

Or run `python -m pytest -q` for both suites after Chromium is installed. Tests run once and exit. No JS build is required. CI uses Python 3.12, pip, Ruff, syntax compilation, pytest and Python Playwright; it has not run on GitHub and no deployment is configured.

## Demo scenarios and limits

To test the updated patient flow: choose Demo patient, open Hospitals, search LS6 and click **Start a new visit here**. The already checked-in demo visit stays unchanged. Review/edit/submit the new intake, then open **My visits** to see both records and their forms. Use **View visit** to reopen either dashboard. Staff can search the new reference and confirm its arrival. A closed visit's form remains in history; **Plan another visit** starts a separate draft. Normal patient registration still works and starts its own history.

The intentional message-failure button is under **Demo testing tools**. It causes one expected failed submission so retry can be demonstrated. It is not part of normal messaging.

- Alex Morgan / P-2041: connected band, synthetic recommendation awaiting staff review.
- Jamie Parker / P-2042: awaiting band, pending assessment.
- Sam Taylor / P-2043: disconnected/stale band, failed assessment.
- Robin Lee / P-2044: awaiting arrival; no waiting clock yet.
- Casey Jordan / P-2045: simulated Fitbit heart rate; missing temperature/SpO2.

Use the same browser to switch roles. Server memory survives refresh; Reset demo or restarting Flask clears it. Separate browsers have isolated state and no shared multi-user backend. Bands generate readings only through the simulator action. Disconnected devices retain old readings. A 15-minute freshness label is an illustrative UI setting, not a clinical rule.

The core and LS6 postcode search work without internet; other postcode districts use Postcodes.io. Optional fonts and external directions also use internet. All application logic/tests are Python, with HTML/CSS rendered by Flask. No JavaScript is served. Hospitals accepts LS6 or a full UK postcode, uses only its district and sorts the supported catalogue within 30 miles by approximate straight-line distance. Browser GPS is unavailable. No offline care mode exists.

If `python` is not found, install Python and enable its PATH option, then reopen your terminal. The launcher here is `python` (the `py` launcher was unavailable). If port 5000 is occupied, stop the other local server or run `python -m flask --app app run --port 5001` and use that printed URL. This is Flask's local development server, not a production deployment.

The old React source is outside this project at `C:\Users\moham\OneDrive\Desktop\Pulse-React-backup`; its Node commands do not describe Flask. Maham's SQL remains unchanged and should not be executed just to start the demo.


## Admin/support demonstration

Choose Demo admin: inspect Admin overview, Staff & admin access, Login activity, Security and Support inbox. There are no clinical patient pages in this role. Create a fictional profile, choose Staff or Admin and activate/deactivate it. These records do not change public demo entry permissions.

Choose Demo patient, open Admin support, enter a subject/message and send. Switch to Demo admin in the same browser, open Support inbox, select the thread, mark read and reply. Switch back to patient to see the reply. Admin can also start a new staff conversation; switch to Demo staff and use Admin support to reply. For medical care use the existing patient/staff Messages inbox. Support is not an urgent-care channel and does not synchronise across separate browsers.

## Garmin check

Garmin is optional: the synthetic core works without a key. Follow garmin-setup.md for an owner-controlled local replacement key. Devices -> Check Garmin API access tests token exchange only. All automated Garmin tests use fictional credentials and HTTP doubles; browser tests disable real Garmin configuration. .secrets/ and credential/cache files must be excluded from Git and review ZIPs.

## Garmin readings update (supersedes access-check-only notes above)

The local owner preview now requests documented daily heart-rate and SpO2 data, maps timestamped samples/daily HR statistics, and polls every 30 seconds through a native HTML refresh. Temperature remains unavailable; no direct live-watch connection is claimed. Values remain separate from synthetic visits and Oracle/model data. The readings client caches bearer tokens only in server memory; Stop/Clear removes them. Local loopback and patient/staff demo role checks apply, but real authenticated ownership/consent is still required before any public/multi-user use. Real owner HR/statistics and the website preview have now been verified after exact-text key configuration; token/HR/SpO2 endpoints returned HTTP 200, but no timestamped SpO2 sample was supplied. Automated tests continue to use synthetic HTTP responses. See garmin-setup.md for current instructions, schemas, mapping and limitations.

Latest Garmin access result: exact-text credential corrected the screenshot transcription. Authentication and both measurement endpoints returned HTTP 200; owner HR/statistics rendered on the running site. The credential remains in the ignored local secret file only; no secret, raw measurement values or personal-data screenshots were added to source. No push/merge.
