
from pathlib import Path
import pandas as pd

# ==========================================
# ER Band - A&E Dataset Quality Checks
# ==========================================

# Locate the dataset
DATASET_PATH = Path(__file__).parent / "synthetic_ae_patient_dataset_v2.csv"

# If your CSV is directly inside the model folder instead,
# change the line above to:
# DATASET_PATH = Path(__file__).parent / "synthetic_ae_patient_dataset_v2.csv"

TARGET = "urgent_reassessment_required"

# 1. Load dataset
print("\n=== 1. LOAD DATASET ===")

if not DATASET_PATH.exists():
    raise FileNotFoundError(
        f"Dataset not found at: {DATASET_PATH}\n"
        "Check that the CSV is in the correct folder."
    )

df = pd.read_csv(DATASET_PATH)

print(f"Rows (records): {df.shape[0]}")
print(f"Columns (features and other fields): {df.shape[1]}")

if df.empty:
    raise ValueError("The dataset is empty.")

# 2. Inspect columns and data types
print("\n=== 2. COLUMN NAMES AND DATA TYPES ===")
print(df.dtypes.to_string())

# 3. Check missing values
print("\n=== 3. MISSING VALUES ===")
missing = df.isnull().sum()
missing_report = pd.DataFrame({
    "missing_count": missing,
    "missing_percent": (missing / len(df) * 100).round(2)
})
print(missing_report[missing_report["missing_count"] > 0])

if missing.sum() == 0:
    print("No missing values found.")

# 4. Check duplicate records
print("\n=== 4. DUPLICATE RECORDS ===")
print("Fully duplicated rows:", df.duplicated().sum())

if "patient_id" in df.columns:
    print("Duplicate patient IDs:", df["patient_id"].duplicated().sum())

# 5. Check target label
print("\n=== 5. TARGET LABEL CHECK ===")

if TARGET not in df.columns:
    raise ValueError(
        f"Target column '{TARGET}' was not found. "
        f"Available columns: {df.columns.tolist()}"
    )

print("Target values:")
print(df[TARGET].value_counts(dropna=False).to_string())

print("\nTarget percentages:")
print(
    (df[TARGET].value_counts(normalize=True, dropna=False) * 100)
    .round(2)
    .to_string()
)

# 6. Check important numerical fields
print("\n=== 6. NUMERICAL SUMMARY ===")

numeric_columns = [
    "age",
    "heart_rate_bpm",
    "systolic_bp_mmHg",
    "diastolic_bp_mmHg",
    "respiratory_rate_bpm",
    "spo2_percent",
    "temperature_c",
    "pain_score_0_10",
]

available_numeric = [
    column for column in numeric_columns if column in df.columns
]

print(df[available_numeric].describe().round(2).to_string())

# 7. Check categorical values
print("\n=== 7. CATEGORICAL VALUES ===")

for column in [
    "sex",
    "chief_complaint",
    "arrival_mode",
    "triage_category",
    "consciousness_level",
]:
    if column in df.columns:
        print(f"\n{column}:")
        print(df[column].value_counts(dropna=False).to_string())

# 8. Check whether labels are missing
print("\n=== 8. TRAINING READINESS ===")

missing_targets = df[TARGET].isna().sum()
print("Rows with missing target labels:", missing_targets)

if missing_targets > 0:
    print("WARNING: Missing target labels need investigation.")
else:
    print("All records have a target label.")

# 9. Synthetic-data warning
if "synthetic_data_only" in df.columns:
    print("\nSynthetic-data marker:")
    print(df["synthetic_data_only"].value_counts(dropna=False))

if "label_generation_note" in df.columns:
    print("\nLabel-generation notes:")
    print(df["label_generation_note"].value_counts(dropna=False))

print("\n=== QUALITY CHECKS COMPLETE ===")
