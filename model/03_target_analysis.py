
from pathlib import Path

import pandas as pd

# --------------------------------------------------
# 1. LOAD DATASET
# --------------------------------------------------

DATASET_PATH = Path(__file__).parent / "synthetic_ae_patient_dataset_v2.csv"

df = pd.read_csv(DATASET_PATH)

TARGET = "urgent_reassessment_required"

print("=" * 60)
print("ER BAND - TARGET ANALYSIS")
print("=" * 60)

print(f"\nDataset records: {len(df)}")
print(f"Dataset columns: {len(df.columns)}")

# --------------------------------------------------
# 2. CHECK TARGET LABELS
# --------------------------------------------------

print("\n--- 1. TARGET DISTRIBUTION ---")

print(df[TARGET].value_counts(dropna=False).sort_index())

print("\nTarget percentages:")

print(
    (df[TARGET].value_counts(normalize=True, dropna=False) * 100)
    .sort_index()
    .round(2)
)

# --------------------------------------------------
# 3. COMPARE NUMERIC FEATURES
# --------------------------------------------------

print("\n--- 2. NUMERIC FEATURE COMPARISON ---")

numeric_features = [
    column
    for column in df.select_dtypes(include="number").columns
    if column not in [
        TARGET,
        "patient_id",
        "reassessment_within_30_min",
    ]
]

comparison = df.groupby(TARGET)[numeric_features].median().T

comparison.columns = [
    f"Target_{column}_median" for column in comparison.columns
]

print(comparison.to_string())

# --------------------------------------------------
# 4. CHECK CATEGORICAL FEATURES
# --------------------------------------------------

print("\n--- 3. CATEGORICAL FEATURE ASSOCIATIONS ---")

categorical_features = [
    "sex",
    "chief_complaint",
    "arrival_mode",
    "consciousness_level",
    "triage_category",
]

for column in categorical_features:

    if column not in df.columns:
        continue

    print(f"\n{column}:")

    rates = (
        df.groupby(column, dropna=False)[TARGET]
        .agg(["count", "mean"])
        .rename(columns={
            "count": "number_of_patients",
            "mean": "urgent_reassessment_rate",
        })
    )

    rates["urgent_reassessment_rate"] = (
        rates["urgent_reassessment_rate"] * 100
    ).round(2)

    print(rates.to_string())

# --------------------------------------------------
# 5. CHECK SYNTHETIC LABEL INFORMATION
# --------------------------------------------------

print("\n--- 4. DATASET LABEL NOTES ---")

if "synthetic_data_only" in df.columns:
    print("\nSynthetic data flag:")
    print(df["synthetic_data_only"].value_counts(dropna=False))

if "label_generation_note" in df.columns:
    print("\nLabel generation notes:")
    print(df["label_generation_note"].value_counts(dropna=False))

# --------------------------------------------------
# 6. CHECK MISSING VALUES
# --------------------------------------------------

print("\n--- 5. MISSING VALUES ---")

missing = df.isnull().sum()
missing = missing[missing > 0]

if missing.empty:
    print("No missing values found.")
else:
    print(missing.sort_values(ascending=False).to_string())

print("\n" + "=" * 60)
print("TARGET ANALYSIS COMPLETE")
print("=" * 60)
