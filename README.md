# Pulse - Wearable Patient Monitoring for A&E

Built at the AI IN HEALTHCARE HACKATHON.

## Our team

- Mohammed Sherif
- Mostafa Issa
- Maham Ali
- Elysha Ruddock

## The idea

Pulse helps patients and staff stay connected while patients wait in A&E. Patients choose a hospital, fill in an intake form, view their visits and chat with staff. Staff confirm arrival, assign a wristband and review readings or requests for help.

## Technology

| Part | Technology |
| --- | --- |
| Wristband | ESP32-WROOM-32, heart-rate and temperature sensors, LCD display and LiPo battery (team hardware prototype) |
| Database | Oracle Database, Oracle APEX and a protected read-only ORDS API |
| Website | Python 3.12+, Flask, Jinja2, HTML, CSS and SVG icons/charts |
| AI training | |
| Tests and checks | pytest, Python Playwright/Chromium, Ruff and GitHub Actions |

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
