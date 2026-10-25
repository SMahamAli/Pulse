"""Proposed JSON boundary for Elysha's notebook review table, not a model implementation.

Dataset stay IDs are deliberately not treated as live Pulse patient/visit IDs.
No duration experiment is converted into an A&E remaining-wait prediction.
"""

from .oracle_mapping import number


def map_notebook_review(row):
    heart_rate = number(row.get("heartrate"))
    stay = row.get("stay_id")
    return {
        "datasetStayId": str(stay) if stay is not None else None,
        "observedAt": row.get("charttime"),
        "heartRate": heart_rate,
        "anomalyScore": number(row.get("anomaly_score")),
        "demoFlag": row.get("demo_flag") if isinstance(row.get("demo_flag"), bool) else None,
        "missingSensorData": bool(row.get("missing_sensor_data")) or heart_rate is None,
        "dashboardMessage": row.get("dashboard_message"),
        "source": "AI_Training.ipynb review-table proposal; not a live assessment",
    }
