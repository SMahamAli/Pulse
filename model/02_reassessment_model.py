
from pathlib import Path

import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


# ============================================================
# ER Band - Urgent Reassessment Prediction Model
# Research prototype using synthetic data only
# ============================================================

print("\n=== 1. LOAD DATASET ===")

DATASET_PATH = (
    Path(__file__).parent / "synthetic_ae_patient_dataset_v2.csv"
)

TARGET = "urgent_reassessment_required"

if not DATASET_PATH.exists():
    raise FileNotFoundError(
        f"Dataset not found: {DATASET_PATH}"
    )

df = pd.read_csv(DATASET_PATH)

print(f"Records loaded: {len(df)}")

if TARGET not in df.columns:
    raise ValueError(f"Missing target column: {TARGET}")

# Remove rows where the answer we want to predict is missing.
df = df.dropna(subset=[TARGET]).copy()

# Ensure the target contains only the expected binary labels.
if not set(df[TARGET].unique()).issubset({0, 1}):
    raise ValueError(
        f"Expected target labels 0 and 1, found: "
        f"{sorted(df[TARGET].unique())}"
    )

# ============================================================
# 2. SELECT INPUT FEATURES
# ============================================================

print("\n=== 2. PREPARE FEATURES ===")

# Exclude identifiers, the target, related outcome fields,
# and synthetic-data documentation from model inputs.
excluded_columns = [
    "patient_id",
    TARGET,
    "reassessment_within_30_min",
    "synthetic_data_only",
    "label_generation_note",
]

X = df.drop(
    columns=excluded_columns,
    errors="ignore",
)

y = df[TARGET].astype(int)

# Detect numeric and categorical input columns.
numeric_features = X.select_dtypes(
    include=["number"]
).columns.tolist()

categorical_features = X.select_dtypes(
    include=["object", "category", "bool"]
).columns.tolist()

print("Numeric features:", numeric_features)
print("Categorical features:", categorical_features)
print("\nTarget distribution:")
print(y.value_counts().sort_index().rename(
    index={0: "No urgent reassessment", 1: "Urgent reassessment"}
))

if y.nunique() != 2:
    raise ValueError("Training requires both target classes (0 and 1).")

# ============================================================
# 3. SPLIT TRAINING AND TEST DATA
# ============================================================

print("\n=== 3. SPLIT DATA ===")

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y,
)

print(f"Training records: {len(X_train)}")
print(f"Test records: {len(X_test)}")
print(f"Positive cases in test set: {int(y_test.sum())}")

# ============================================================
# 4. PREPROCESS MISSING VALUES AND CATEGORIES
# ============================================================

numeric_pipeline = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="median")),
    ]
)

categorical_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="most_frequent"),
        ),
        (
            "encoder",
            OneHotEncoder(handle_unknown="ignore"),
        ),
    ]
)

preprocessor = ColumnTransformer(
    transformers=[
        ("numeric", numeric_pipeline, numeric_features),
        (
            "categorical",
            categorical_pipeline,
            categorical_features,
        ),
    ],
)

# ============================================================
# 5. BUILD AND TRAIN THE MODEL
# ============================================================

print("\n=== 4. TRAIN MODEL ===")

model = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        (
            "classifier",
            RandomForestClassifier(
                n_estimators=300,
                class_weight="balanced",
                random_state=42,
                min_samples_leaf=2,
                n_jobs=-1,
            ),
        ),
    ]
)

model.fit(X_train, y_train)

print("Model training complete.")

# ============================================================
# 6. EVALUATE ON UNSEEN TEST RECORDS
# ============================================================

print("\n=== 5. EVALUATE MODEL ===")

y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:, 1]

print(f"Accuracy:          {accuracy_score(y_test, y_pred):.3f}")
print(
    f"Balanced accuracy: "
    f"{balanced_accuracy_score(y_test, y_pred):.3f}"
)

print("\nClassification report:")
print(
    classification_report(
        y_test,
        y_pred,
        labels=[0, 1],
        target_names=[
            "No urgent reassessment",
            "Urgent reassessment",
        ],
        zero_division=0,
    )
)

print("Confusion matrix (rows = actual, columns = predicted):")
print(confusion_matrix(y_test, y_pred, labels=[0, 1]))

if y_test.nunique() == 2:
    print(f"\nROC-AUC: {roc_auc_score(y_test, y_prob):.3f}")
else:
    print("\nROC-AUC unavailable: test set contains only one class.")

print("\n=== EXPERIMENT COMPLETE ===")
print(
    "Research prototype only. Synthetic labels do not establish "
    "clinical validity."
)
