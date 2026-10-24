# Pulse - Wearable Patient Monitoring for A&E

Built at AI IN HEALTHCARE HACKATHON 

Collaborators:
- Elysha Ruddock
- Mohammed Sherif
- Mostafa Issa
- Maham Ali

The problem

Patients can wait in NHS A&E waiting rooms for hours after triage. Their condition can get worse during that time without any one noticing, due to staff not been able to watch everyone in a busy waiting room. 

Our solution

Each patient is given a wristband when they're triaged. The band continuously records:
- Heart rate
- Blood oxygen(spO2)
- Respiratory rate
- Skin temperature
- Falls

Tech stack 
| Part | Technology |
|---|---|
Wristband |ESP32-WROOM-32, Accelerometer MPU-6050, Oximeter & heart rate sensor, Fever Click Board MIKROE-2554, Wristband, LCD Display, Small 3.7V LiPo-300
| Database | Oracle (built in Oracle APEX) | 
| Website | 
Dashboard

The readings go to a live dashboard that staff can watch. The system:
- Combines wristband data with staff observations to calculate an early warning score.
- Raises an alert when a patient crosses a threshold.
- allows staff to acknowledge and resolve alerts while keeping a record of who responded and when.

Features

- Live overview of every patient in the department, colour coded by triage category.
- Latest vitals for each patient.
- Trend charts so staff can see whether a patient is getting worse.
- Alerts sorted by severity.
- Logins with different roles (Doctor, nurse, patient, admin, receptionist)

Demo Logins

| Role | Email | Password |
|---|---|---|
| Nurse | priya.patel@demo-nhs.test | priya1 |
| Doctor | sarah.whitfield@demo-nhs.test | sarah1 |
| Nurse in Charge | michael.grant@demo-nhs.test | michael1 |
| Admin | rachel.adams@demo-nhs.test | rachel1 |

Demo scenario

The demo data covers one simulated shift with 14 patients.
Things to look for:

