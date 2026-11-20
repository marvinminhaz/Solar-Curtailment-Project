import os
import re
import pandas as pd
import pdfplumber


# Ordered patterns with safe boundaries to prevent substring collisions (e.g., 'daman' vs 'andaman')
STATE_PATTERNS = [
    (r"\bchandigarh\b", "Chandigarh"),
    (r"\bdelhi\b", "Delhi"),
    (r"\bharyana\b", "Haryana"),
    (r"\bhimachal\b", "Himachal Pradesh"),
    (r"(?:jammu|j\s*&\s*k|ladakh)", "Jammu and Kashmir"),
    (r"\bpunjab\b", "Punjab"),
    (r"\brajasthan\b", "Rajasthan"),
    (r"\buttarakhand\b", "Uttarakhand"),
    (r"\buttar(?:\s+pradesh)?\b", "Uttar Pradesh"),
    (r"\bchhattisgarh\b", "Chhattisgarh"),
    (r"\bgujarat\b", "Gujarat"),
    (r"\bmadhya(?:\s+pradesh)?\b", "Madhya Pradesh"),
    (r"\bmaharashtra\b", "Maharashtra"),
    (r"(?:dadra|\bdaman\b|d\s*&\s*n\s*haveli)", "Dadra and Nagar Haveli and Daman and Diu"),
    (r"\bgoa\b", "Goa"),
    (r"\bandhra\b", "Andhra Pradesh"),
    (r"\btelangana\b", "Telangana"),
    (r"\bkarnataka\b", "Karnataka"),
    (r"\bkerala\b", "Kerala"),
    (r"\btamil\b", "Tamil Nadu"),
    (r"\bpuducherry\b", "Puducherry"),
    (r"\blakshadweep\b", "Lakshadweep"),
    (r"\bbihar\b", "Bihar"),
    (r"\bdvc\b", "DVC"),
    (r"\bjharkhand\b", "Jharkhand"),
    (r"\bodisha\b", "Odisha"),
    (r"\bbengal\b", "West Bengal"),
    (r"\bsikkim\b", "Sikkim"),
    (r"\bandaman\b", "Andaman and Nicobar"),
    (r"\barunachal\b", "Arunachal Pradesh"),
    (r"\bassam\b", "Assam"),
    (r"\bmanipur\b", "Manipur"),
    (r"\bmeghalaya\b", "Meghalaya"),
    (r"\bmizoram\b", "Mizoram"),
    (r"\bnagaland\b", "Nagaland"),
    (r"\btripura\b", "Tripura"),
]

EXCLUDE_TERMS = (
    "region",
    "all india",
    "total",
    "system",
    "others",
    "eastern",
    "western",
    "northern",
    "southern",
)


def match_label(text: str):
    text_lower = text.lower()
    if any(term in text_lower for term in EXCLUDE_TERMS):
        return "EXCLUDE"
    for pattern, canonical_name in STATE_PATTERNS:
        if re.search(pattern, text_lower):
            return canonical_name
    return None


def clean_mw(val: str):
    if not val:
        return None
    s = str(val).strip()
    # Fix CEA typos where a thousands comma is printed as a period (e.g., '16.174' -> '16174')
    s = re.sub(r"(?<=\d)\.(?=\d{3}\b)", "", s)
    s = re.sub(r"[^\d.]", "", s)
    try:
        return float(s) if s else None
    except ValueError:
        return None


def group_into_lines(words, y_tol: float = 3.5):
    """Group word dicts into horizontal visual lines sorted top-to-bottom, left-to-right."""
    lines = []
    for w in sorted(words, key=lambda x: (x["top"], x["x0"])):
        if lines and abs(w["top"] - lines[-1][0]["top"]) <= y_tol:
            lines[-1].append(w)
        else:
            lines.append([w])
    for line in lines:
        line.sort(key=lambda x: x["x0"])
    return lines


def demand_data_extractor(
    pdf_dir: str = "../data/raw/cea/Demand",
    output_file: str = '../data/raw/cea/cea_csv/cea_monthly_peak_demand.csv',
):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    all_records = []
    pdf_files = sorted(f for f in os.listdir(pdf_dir) if f.endswith(".pdf"))
    print(f"Found {len(pdf_files)} PDF files to process.")

    for filename in pdf_files:
        date_match = re.search(r"(\d{4})-(\d{2})", filename)
        if not date_match:
            continue
        year, month = int(date_match.group(1)), int(date_match.group(2))

        with pdfplumber.open(os.path.join(pdf_dir, filename)) as pdf:
            words = pdf.pages[0].extract_words(keep_blank_chars=False)

        # Left column (x0 < 190): collect state/region labels and stop at 'All India'
        label_lines = group_into_lines([w for w in words if w["x0"] < 190])
        labels = []
        y_table_end = float("inf")

        for line in label_lines:
            y_lbl = line[0]["top"]
            text = " ".join(w["text"] for w in line)
            if "all india" in text.lower():
                y_table_end = y_lbl - 2.0
                break
            matched = match_label(text)
            if matched:
                labels.append((y_lbl, matched))

        # Right columns (x0 >= 190): extract numeric rows inside the main table body
        num_lines = group_into_lines(
            [w for w in words if w["x0"] >= 190 and 125 < w["top"] < y_table_end]
        )
        for line in num_lines:
            y_num = line[0]["top"]
            nums = [val for w in line if (val := clean_mw(w["text"])) is not None]
            if len(nums) < 2:
                continue

            # Pair with closest vertical label within 11.5 pt (handles wrapped bilingual cells)
            nearby = [(abs(y_lbl - y_num), lbl) for y_lbl, lbl in labels if abs(y_lbl - y_num) <= 11.5]
            if not nearby:
                continue
            nearby.sort(key=lambda x: x[0])
            state_name = nearby[0][1]

            if state_name == "EXCLUDE":
                continue

            peak_demand = nums[0]
            peak_met = nums[1]
            # In Jan-Mar & May 2015 CEA reports, column 2 was 'Demand not Met (MW)' instead of 'Peak Met (MW)'
            if peak_met < 0.5 * peak_demand:
                peak_met = peak_demand - peak_met

            all_records.append({
                "state": state_name,
                "year": year,
                "month": month,
                "peak_demand_mw": peak_demand,
                "peak_met_mw": peak_met,
                "source_file": filename,
            })

    raw_df = pd.DataFrame(all_records)
    assert not raw_df.empty, f"No records extracted from {pdf_dir}"

    # Sum pre-2020 Daman & Diu + Dadra & Nagar Haveli rows; take first match for all other states
    dnh_mask = raw_df["state"] == "Dadra and Nagar Haveli and Daman and Diu"
    dnh_df = (
        raw_df[dnh_mask]
        .groupby(["state", "year", "month"], as_index=False)
        .agg({"peak_demand_mw": "sum", "peak_met_mw": "sum", "source_file": "first"})
    )
    other_df = raw_df[~dnh_mask].drop_duplicates(subset=["state", "year", "month"])

    df = (
        pd.concat([other_df, dnh_df], ignore_index=True)
        .sort_values(by=["state", "year", "month"])
        .reset_index(drop=True)
    )

    # Built-in data integrity assertions
    audit = (
        df.groupby("state")["peak_demand_mw"]
        .agg(count="count", min="min", median="median", max="max")
        .assign(max_to_median=lambda x: (x["max"] / x["median"]).round(2))
    )
    outliers = audit[audit["max_to_median"] > 2.2]
    assert outliers.empty, f"Unexpected demand outliers detected:\n{outliers}"
    assert df.loc[df["state"] == "Uttar Pradesh", "peak_demand_mw"].max() > 25000, "UP peak demand too low!"
    assert df.loc[df["state"] == "Goa", "peak_demand_mw"].max() < 2000, "Goa peak demand too high!"

    print("\n--- Extraction Summary ---")
    print(f"Total observations extracted: {len(df)}")
    print(f"Unique states captured: {df['state'].nunique()}")
    print(f"Date range: {df['year'].min()}-{df['month'].min():02d} to {df['year'].max()}-{df['month'].max():02d}")

    df.to_csv(output_file, index=False)
    print(f"Saved clean demand data to {output_file}")
    return df