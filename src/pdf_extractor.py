import os
import re
import pandas as pd
import pdfplumber

# 1. Directory containing downloaded PDFs
PDF_DIR = "../data/raw/cea/Demand"
OUTPUT_FILE = "data/raw/cea_monthly_peak_demand.csv"
os.makedirs("data/raw", exist_ok=True)

# 2. Canonical state mapping to clean Hindi/English text and aliases
STATE_LOOKUP = {
    "chandigarh": "Chandigarh",
    "delhi": "Delhi",
    "haryana": "Haryana",
    "himachal": "Himachal Pradesh",
    "jammu": "Jammu and Kashmir",
    "j&k": "Jammu and Kashmir",
    "punjab": "Punjab",
    "rajasthan": "Rajasthan",
    "uttar pradesh": "Uttar Pradesh",
    "uttarakhand": "Uttarakhand",
    "chhattisgarh": "Chhattisgarh",
    "gujarat": "Gujarat",
    "madhya pradesh": "Madhya Pradesh",
    "maharashtra": "Maharashtra",
    "dadra": "Dadra and Nagar Haveli and Daman and Diu",
    "daman": "Dadra and Nagar Haveli and Daman and Diu",
    "goa": "Goa",
    "andhra": "Andhra Pradesh",
    "telangana": "Telangana",
    "karnataka": "Karnataka",
    "kerala": "Kerala",
    "tamil nadu": "Tamil Nadu",
    "puducherry": "Puducherry",
    "lakshadweep": "Lakshadweep",
    "bihar": "Bihar",
    "dvc": "DVC",
    "jharkhand": "Jharkhand",
    "odisha": "Odisha",
    "west bengal": "West Bengal",
    "sikkim": "Sikkim",
    "andaman": "Andaman and Nicobar",
    "arunachal": "Arunachal Pradesh",
    "assam": "Assam",
    "manipur": "Manipur",
    "meghalaya": "Meghalaya",
    "mizoram": "Mizoram",
    "nagaland": "Nagaland",
    "tripura": "Tripura",
}

# Words indicating aggregate summary rows to exclude
EXCLUDE_TERMS = [
    "region",
    "all india",
    "total",
    "system",
    "others",
    "eastern",
    "western",
    "northern",
    "southern",
]


def match_state(text):
    text_lower = text.lower()
    if any(term in text_lower for term in EXCLUDE_TERMS):
        return None
    for key, canonical_name in STATE_LOOKUP.items():
        if key in text_lower:
            return canonical_name
    return None


def clean_number(val):
    if not val:
        return None
    # Remove commas, whitespace, and non-numeric characters (except decimal)
    clean_val = re.sub(r"[^\d.]", "", str(val).strip())
    try:
        return float(clean_val)
    except ValueError:
        return None


all_records = []
pdf_files = sorted([f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")])
print(f"Found {len(pdf_files)} PDF files to process.")

for filename in pdf_files:
    # Extract Year and Month from filename pattern 'PSP_Peak_YYYY-MM.pdf'
    date_match = re.search(r"(\d{4})-(\d{2})", filename)
    if not date_match:
        continue
    year = int(date_match.group(1))
    month = int(date_match.group(2))

    pdf_path = os.path.join(PDF_DIR, filename)

    with pdfplumber.open(pdf_path) as pdf:
        # Power supply position tables are always on page 1
        page = pdf.pages[0]
        tables = page.extract_tables()

        for table in tables:
            for row in table:
                if not row or len(row) < 3:
                    continue

                raw_state_cell = str(row[0]) if row[0] else ""
                raw_demand_cell = str(row[1]) if row[1] else ""
                raw_met_cell = str(row[2]) if row[2] else ""

                # Handle multi-line cells where rows were merged due to missing borders
                state_lines = [
                    s.strip() for s in raw_state_cell.split("\n") if s.strip()
                ]
                demand_lines = [
                    d.strip() for d in raw_demand_cell.split("\n") if d.strip()
                ]
                met_lines = [
                    m.strip() for m in raw_met_cell.split("\n") if m.strip()
                ]

                # If single row
                if len(state_lines) <= 1:
                    state_name = match_state(raw_state_cell)
                    peak_demand = clean_number(raw_demand_cell)
                    peak_met = clean_number(raw_met_cell)

                    if state_name and peak_demand is not None:
                        all_records.append({
                            "state": state_name,
                            "year": year,
                            "month": month,
                            "peak_demand_mw": peak_demand,
                            "peak_met_mw": peak_met,
                            "source_file": filename,
                        })

                # If multiple lines merged in the same row
                else:
                    for idx, line in enumerate(state_lines):
                        state_name = match_state(line)
                        if state_name and idx < len(demand_lines):
                            peak_demand = clean_number(demand_lines[idx])
                            peak_met = (
                                clean_number(met_lines[idx])
                                if idx < len(met_lines)
                                else None
                            )
                            if peak_demand is not None:
                                all_records.append({
                                    "state": state_name,
                                    "year": year,
                                    "month": month,
                                    "peak_demand_mw": peak_demand,
                                    "peak_met_mw": peak_met,
                                    "source_file": filename,
                                })

# 3. Create DataFrame and deduplicate
df = pd.DataFrame(all_records)
df = df.drop_duplicates(subset=["state", "year", "month"])
df = df.sort_values(by=["state", "year", "month"]).reset_index(drop=True)

print("\n--- Extraction Summary ---")
print(f"Total observations extracted: {len(df)}")
print(f"Unique states captured: {df['state'].nunique()}")
print(f"Date range: {df['year'].min()}-{df['month'].min():02d} to {df['year'].max()}-{df['month'].max():02d}")
print("\nSample records:")
print(df.head(10))

# 4. Save to processed raw location
df.to_csv(OUTPUT_FILE, index=False)
print(f"\nSaved clean demand data to {OUTPUT_FILE}")