# Garmin: local account-owner readings

Devices now has **Show Garmin readings** as well as a separate API-access check. The readings page requests the owner's daily heart-rate and SpO2 data from Garmin Connect, maps documented fields, shows measurement time/age, daily minimum/maximum/resting heart rate and a history graph. It refreshes every 30 seconds while open. This is latest synced cloud data, not a direct/live sensor stream. The watch must sync to Garmin Connect; old samples remain old even after a new fetch. Temperature is unavailable because no temperature endpoint has been configured.

## One-time private setup

1. Ask the owner to revoke the key shared in chat/screenshots and create a replacement.
2. Open `.secrets/garmin-personal-api-key` in this project and paste only the key on one line. Save it. This file is ignored by Git; never send or commit it. The local file is configured on this laptop and is not uploaded.
3. Open **Demo patient** or **Demo staff -> Devices -> Show Garmin readings**. Choose the same calendar date as the owner's Garmin app. Sync the watch in Garmin Connect if new samples do not appear.
4. Use **Stop and clear Garmin preview** when finished. Closing the page stops page polling; the Stop button also clears stored preview values/token memory. Reset/restart clears the browser preview too.

The optional server environment variable GARMIN_PERSONAL_API_KEY overrides the file, including if explicitly empty. Avoid putting keys in command-line arguments/history. Keys are never entered in web forms. A key saved only in chat is not configured in the server: it must be placed directly in this local file or server environment to avoid copying it into logged commands.

## Data and secret handling

The owner preview is separate from fictional patient visits. It is not associated with the demo patient's identity or sent to Oracle, messages or the AI model. Only local loopback requests using patient/staff demo roles can open it; admin is rejected. This is an owner-controlled laptop demonstration, not a production multi-user authorization system. Do not expose it publicly or behind a public reverse proxy: real authenticated consent/ownership enforcement is required first.

The key goes only to Garmin's fixed HTTPS token endpoint. The bearer goes only to two fixed official measurement endpoints; redirects are refused. Token expiry is checked for cache freshness; there is no claim that decoding expiry independently verifies a JWT signature. The separate access check discards its returned token. Readings polling reuses a bearer in server memory until expiry/key change/clear, and creates no disk cache. No key/token is returned to HTML, cookies, fixtures, access logs or support messages. Vendor error bodies are not shown.

Only the mapped measurements/statistics and timestamps are held in this browser's server-memory service, outside synthetic snapshots. Raw profile identifiers and responses are not stored. Failed refreshes keep earlier samples with their original measurement times and show an error. Missing metrics are unavailable, never zero/normal. A prototype 15-minute stale label is not a clinical threshold. No patient routing, diagnosis or model decision is derived from Garmin data.

The .secrets directory, common Garmin credential/cache filenames and local environment files are Git-ignored. Exclude them from review ZIPs. Git ignore is not encryption: protect the laptop/file access too. Do not capture real health data or secrets in test screenshots or presentation recordings without the owner's agreement.

## Implementation and verification

- pulse/garmin.py: secret loading, token exchange, temporary in-memory bearer reuse and two read-only resource requests.
- pulse/garmin_mapping.py: descriptor-based heartRateValues mapping; latestSpO2 with its UTC timestamp; supplied daily min/max/resting fields. Null/gap/future samples are handled explicitly.
- pulse/__init__.py: local-only start/read/stop routes; minimum 30-second request spacing per browser workspace; no automatic polling on ordinary forms.
- templates/garmin_readings.html: native HTML refresh, sourced cards, sample ages/statistics/history and Stop/Clear. No authored JavaScript.
- tests/test_garmin.py and tests/test_garmin_readings.py: fictional credential/HTTP doubles only. Browser fixtures disable real configuration; simulated transport tests do not establish live account access.

Latest real verification: the exact credential supplied as text was configured only in the ignored local secret file. Garmin's token, heart-rate and SpO2 endpoints all returned HTTP 200. Timestamped heart-rate samples and daily statistics were available; no timestamped SpO2 sample was supplied. The running website rendered the real preview successfully in an isolated local verification session, which was then cleared. No credential/token/raw health values were printed, and no personal-data screenshot or export was saved. Earlier HTTP 401 results were caused by screenshot transcription errors, not proof that the owner's key was invalid.

A Personal API key represents one person's own Garmin account. Every patient connecting their own watch needs the appropriate multi-user Garmin programme and real authenticated account/consent linking. Database persistence and a deliberate owner-to-visit relationship remain team decisions; never silently populate a fictional patient with someone else's readings.

Official sources checked 24 October 2026:

- [Garmin Personal API instructions](https://developer.garmin.com/gc-developer-program/personal/personal-api/)
- [Personal API FAQ](https://developer.garmin.com/gc-developer-program/personal/personal-faq/)
- [Garmin official OpenAPI schemas](https://developer.garmin.com/gc-developer-program/personal/swagger-docs/)
- [Garmin's official Python client](https://github.com/garmin/connect-personal-api-python)
