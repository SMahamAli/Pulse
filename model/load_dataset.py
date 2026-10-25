
import pandas as pd
from pathlib import Path

# Find the dataset in the project folder
dataset_path = Path("synthetic_ae_patient_dataset_v2.csv")

# Load the dataset
df = pd.read_csv(dataset_path)

# Display basic information
print("Dataset loaded successfully!")
print("Number of patients:", len(df))
print("Number of columns:", len(df.columns))

print("\nColumn names:")
print(df.columns.tolist())

print("\nFirst 5 patients:")
print(df.head())

print("\nMissing values:")
print(df.isnull().sum())
