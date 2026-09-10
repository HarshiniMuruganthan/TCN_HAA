import pandas as pd
import os

# -----------------------------
# 1. Load the raw dataset
# -----------------------------
input_file = "data/raw/aqi-data.xlsx"

df = pd.read_excel(input_file)

print("Original shape:", df.shape)

# -----------------------------
# 2. Convert date column
# -----------------------------
df["date"] = pd.to_datetime(df["date"], errors="coerce")

# -----------------------------
# 3. Remove duplicate rows
# -----------------------------
df = df.drop_duplicates()

# -----------------------------
# 4. Check missing values
# -----------------------------
print("\nMissing values:")
print(df.isnull().sum())

# Remove rows with invalid dates
df = df.dropna(subset=["date"])

# -----------------------------
# 5. Sort by date
# -----------------------------
df = df.sort_values("date")

# -----------------------------
# 6. Reset index
# -----------------------------
df = df.reset_index(drop=True)

# -----------------------------
# 7. Save processed dataset
# -----------------------------
output_file = "../data/processed/cleaned_aqi.csv"

os.makedirs("../data/processed", exist_ok=True)

df.to_csv(output_file, index=False)

# -----------------------------
# 8. Display result
# -----------------------------
print("\nCleaned shape:", df.shape)

print("\nFirst 5 rows:")
print(df.head())

print("\nCleaned dataset saved to:")
print(output_file)