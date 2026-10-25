
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score,
    roc_auc_score,
)

# --------------------------------------------------
# 1. LOAD DATA
# --------------------------------------------------

DATASET_PATH = (
    Path(__file__).parent
    / "synthetic_ae_patient_dataset_v2.csv"
)

df = pd.read_csv(DATASET_PATH)

TARGET = "urgent_reassessment_required"

excluded_columns = [
    TARGET,
    "patient_id",
    "reassessment_within_30_min",
    "synthetic_data_only",
    "label_generation_note",
]

X = df.drop(columns=excluded_columns, errors="ignore")
y = df[TARGET].astype(int)

# --------------------------------------------------
# 2. SPLIT DATA
# --------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)

numeric_features = X_train.select_dtypes(
    include="number"
).columns.tolist()

categorical_features = X_train.select_dtypes(
    include=["object", "category", "str"]
).columns.tolist()

# --------------------------------------------------
# 3. BUILD THE SAME MODEL
# --------------------------------------------------

numeric_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
])

categorical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OneHotEncoder(handle_unknown="ignore")),
])

preprocessor = ColumnTransformer([
    ("numeric", numeric_pipeline, numeric_features),
    ("categorical", categorical_pipeline, categorical_features),
])

model = Pipeline([
    ("preprocessor", preprocessor),
    ("classifier", RandomForestClassifier(
        n_estimators=300,
        class_weight="balanced",
        random_state=42,
        min_samples_leaf=2,
        n_jobs=-1,
    )),
])

model.fit(X_train, y_train)

# --------------------------------------------------
# 4. EXAMINE PREDICTED PROBABILITIES
# --------------------------------------------------

probabilities = model.predict_proba(X_test)[:, 1]

results = pd.DataFrame({
    "actual": y_test.to_numpy(),
    "predicted_probability": probabilities,
})

print("=" * 60)
print("ER BAND - PROBABILITY ANALYSIS")
print("=" * 60)

print("\n--- 1. PROBABILITY SUMMARY ---")

print(
    results.groupby("actual")["predicted_probability"]
    .agg(["count", "mean", "median", "min", "max"])
    .round(4)
)

print("\n--- 2. RANKING PERFORMANCE ---")

print(
    "ROC-AUC:",
    round(roc_auc_score(y_test, probabilities), 3),
)

print(
    "Average precision:",
    round(average_precision_score(y_test, probabilities), 3),
)

# --------------------------------------------------
# 5. EXPLORE THRESHOLDS
# --------------------------------------------------

print("\n--- 3. EXPLORATORY THRESHOLD COMPARISON ---")
print("Thresholds are illustrative, not clinical cut-offs.")

for threshold in [0.05, 0.10, 0.15, 0.20, 0.30, 0.50]:

    predictions = (probabilities >= threshold).astype(int)

    true_positives = (
        (predictions == 1) & (y_test.to_numpy() == 1)
    ).sum()

    false_positives = (
        (predictions == 1) & (y_test.to_numpy() == 0)
    ).sum()

    false_negatives = (
        (predictions == 0) & (y_test.to_numpy() == 1)
    ).sum()

    predicted_positive = int(predictions.sum())

    recall = (
        true_positives / (true_positives + false_negatives)
        if true_positives + false_negatives else 0
    )

    precision = (
        true_positives / predicted_positive
        if predicted_positive else 0
    )

    print(f"\nThreshold: {threshold:.2f}")
    print(f"Patients flagged: {predicted_positive}")
    print(f"Urgent cases detected: {true_positives}")
    print(f"False alarms: {false_positives}")
    print(f"Urgent cases missed: {false_negatives}")
    print(f"Recall: {recall:.3f}")
    print(f"Precision: {precision:.3f}")

print("\n" + "=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)
