import pandas as pd
import os
import glob

# ==========================================
# 1. Folder containing all raw Excel files
# ==========================================

input_folder = r"D:\AQI_Health-Risk-System\data\raw"

# Find all Excel files
files = glob.glob(os.path.join(input_folder, "*.xlsx"))

print("\n========== FILES FOUND ==========")

for file in files:
    print(os.path.basename(file))

print("\nTotal files:", len(files))


# ==========================================
# 2. Read each file
# ==========================================

all_data = []

for file in files:

    filename = os.path.basename(file).lower()

    print("\nReading:", os.path.basename(file))

    df = pd.read_excel(file)

    # ======================================
    # Identify city
    # ======================================

    if filename == "aqi-data.xlsx":
        city = "Chennai"

    elif "bangalore" in filename or "bengaluru" in filename:
        city = "Bengaluru"

    elif "coimbatore" in filename:
        city = "Coimbatore"

    elif "delhi" in filename:
        city = "Delhi"

    elif "hyderabad" in filename:
        city = "Hyderabad"

    elif "mumbai" in filename:
        city = "Mumbai"

    else:
        city = os.path.splitext(filename)[0]

    # Add city column
    df["city"] = city

    print("City:", city)
    print("Rows:", len(df))

    all_data.append(df)


# ==========================================
# 3. Combine all files
# ==========================================

combined = pd.concat(
    all_data,
    ignore_index=True
)


# ==========================================
# 4. Convert date
# ==========================================

combined["date"] = pd.to_datetime(
    combined["date"],
    errors="coerce"
)


# ==========================================
# 5. Remove invalid dates
# ==========================================

combined = combined.dropna(
    subset=["date"]
)


# ==========================================
# 6. Remove duplicate rows
# ==========================================

combined = combined.drop_duplicates()


# ==========================================
# 7. Sort by city and date
# ==========================================

combined = combined.sort_values(
    ["city", "date"]
)

combined = combined.reset_index(drop=True)


# ==========================================
# 8. Create processed folder
# ==========================================

output_folder = r"D:\AQI_Health-Risk-System\data\processed"

os.makedirs(
    output_folder,
    exist_ok=True
)


# ==========================================
# 9. Save combined dataset
# ==========================================

output_file = os.path.join(
    output_folder,
    "aqi_master.csv"
)

combined.to_csv(
    output_file,
    index=False
)


# ==========================================
# 10. Display result
# ==========================================

print("\n==========================================")
print("       COMBINED MASTER DATASET")
print("==========================================")

print("\nTotal rows:", len(combined))

print("Total columns:", len(combined.columns))


print("\nRows by city:")

print(
    combined["city"].value_counts()
)


print("\nColumns:")

print(
    combined.columns.tolist()
)


print("\nMissing values:")

print(
    combined.isnull().sum()
)


print("\nFirst 5 rows:")

print(
    combined.head()
)


print("\nLast 5 rows:")

print(
    combined.tail()
)


print("\n==========================================")
print("Master dataset saved to:")
print(output_file)
print("==========================================")