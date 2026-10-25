# Pulse - Wearable Patient Monitoring for A&E

Built at the AI IN HEALTHCARE HACKATHON.

## Our team

- Mohammed Sherif - Website
- Mostafa Issa - Hardware
- Maham Ali - Database
- Elysha Ruddock - AI

## The idea

Pulse helps patients and staff stay connected while patients wait in A&E. Patients choose a hospital, fill in an intake form, view their visits and chat with staff. Staff confirm arrival, assign a wristband and review readings or requests for help.

## Technology

| Part | Technology |
| --- | --- |
| Wristband | ESP32-WROOM-32, heart-rate and temperature sensors, LCD display and LiPo battery (team hardware prototype) |
| Database | Oracle Database, Oracle APEX and a protected read-only ORDS API |
| Website | Python 3.12+, Flask, Jinja2, HTML, CSS and SVG icons/charts; no application JavaScript |
| AI training | Python notebook, Jupyter/Google Colab, pandas, NumPy, scikit-learn and Matplotlib |
| Tests and checks | pytest, Python Playwright/Chromium, Ruff and GitHub Actions |
| Optional services | Garmin Personal API for the owner's synced heart rate; Postcodes.io for postcode districts; Google Maps directions links |

## What works now

Patient Home, My visits, postcode search, intake forms, staff check-in, demo band management, human Chat and admin profiles/activity. Staff Home is a summary; Patients has clearly labelled Demo workflow and Oracle records tabs.

Oracle records use the same names and IDs as Maham's stored demonstration data. The separate demo workflow uses fictional fixtures such as Alex and Jamie, plus forms you enter. It does not save forms or chats to Oracle yet. Heart rate and skin temperature are the supported measurements. Real hardware transmission and AI inference still need integration.

Demo role buttons are not secure accounts. Demo records survive refresh but reset when you reset/restart the app. Separate browsers do not share demo records. Hospital counts are simulated; selecting a hospital is not a booking or notification to a real hospital. Private credentials are never included in GitHub.

More details: [Integration](docs/INTEGRATION.md), [checks](docs/manual-testing.md) and [developer commands](docs/development-guide.md). Maham's SQL and Elysha's notebook are preserved. Do not run the SQL setup just to start the website.

## How to run the website

1. Install **Python 3.12 or newer** from [python.org](https://www.python.org/downloads/). On Windows, tick **Add Python to PATH**.
2. Download this project and open its folder in VS Code. Choose **Terminal > New Terminal**. VS Code is optional.
3. Install the requirements:

```powershell
python -m pip install -r requirements.txt
```

4. Start the website:

```powershell
python app.py
```

5. Open **http://127.0.0.1:5000/** and choose **Demo patient**, **Demo staff** or **Demo admin**. Keep the terminal open. Press **Ctrl + C** to stop it. The same commands work on Mac/Linux.

Try **Hospitals > LS6 > choose a hospital > submit intake > My visits**. Switch roles in the same browser to demonstrate staff check-in and Chat replies. Core demo features need no database key. Oracle and Garmin require private local configuration.
