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
| AI training | Python, pandas, NumPy, scikit-learn, Matplotlib and Google Colab |
| Tests and checks | pytest, Python Playwright/Chromium, Ruff and GitHub Actions |

## How to run the website

1. Install **Python 3.12 or newer** from [python.org](https://www.python.org/downloads/). On Windows, tick **Add Python to PATH**.
2. On GitHub, choose **Code > Download ZIP**. Right-click the downloaded ZIP and choose **Extract All**. Do not run it inside the ZIP.
3. In VS Code, choose **File > Open Folder**. Open the extracted folder that contains **app.py** and **requirements.txt**, usually **Pulse-main**. If you only see another Pulse-main folder inside, open that inner folder. Choose **Terminal > New Terminal**.
4. Check that your terminal is in the correct folder:

```powershell
dir app.py, requirements.txt
```

Both files must appear. If you see **No such file** or **Cannot find path**, reopen the correct folder using step 3 and open a new terminal. On Mac/Linux, use `ls app.py requirements.txt`.

5. Install the requirements:

```powershell
python -m pip install -r requirements.txt
```

6. Start the website:

```powershell
python app.py
```

7. Open **http://127.0.0.1:5000/** and choose **Demo patient**, **Demo staff** or **Demo admin**. Keep the terminal open. Press **Ctrl + C** to stop it. Each laptop must run its own copy; GitHub does not host the running website. On Mac/Linux, use `python3` if `python` is unavailable.

For **Demo staff > AI research**, first run `python -m pip install -r requirements-ai.txt`. Then choose **Prepare research model**, select a synthetic example and run its prediction. This uses Elysha's model and synthetic dataset, separately from live patients.
