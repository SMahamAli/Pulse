# Pulse

Pulse helps patients and staff stay connected while patients wait in A&E. Patients can share symptoms and request help. Staff can view visit details, readings and messages.

**Technology:** Python, Flask, HTML and CSS. Python also runs the tests.

## Our Team

- Mohammed — Website
- Mostafa — Hardware
- Maham — Database
- Elysha — AI

## How to Run

Install **Python 3.12 or newer**. Extract the project ZIP, open its folder in VS Code (optional), then open **Terminal → New Terminal**.

### 1. Install the requirements

```powershell
python -m pip install -r requirements.txt
```

### 2. Start the website

```powershell
python app.py
```

Open **http://127.0.0.1:5000/** in your browser and choose a demo role. Keep the terminal open. Stop it with **Ctrl + C**.

### 3. Run the Python checks (optional)

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q -m "not browser"
python -m ruff check app.py pulse tests
```

## Demo Limitations

Data is fictional. Refresh keeps this browser's demo; **Reset demo** or restarting Flask clears it. Separate browsers do not synchronise. Demo roles are not real authentication. Oracle, hardware and AI integrations are not live yet. The core works without JavaScript; a small optional JavaScript helper requests browser location permission.

Details: [Integration](docs/INTEGRATION.md) · [Testing](docs/manual-testing.md) · [Migration](docs/migration.md). The previous React version is preserved in `legacy/react/`; Node.js/npm are not needed for this Flask version.
