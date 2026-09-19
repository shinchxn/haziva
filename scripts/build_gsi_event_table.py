from pathlib import Path
import re
import pandas as pd

INPUT = Path("data/processed/landslide/inventory/wayanad_gsi_landslide_inventory.csv")
OUTPUT = Path("data/processed/landslide/inventory/wayanad_gsi_event_table.csv")

MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2,
    "mar": 3, "march": 3, "apr": 4, "april": 4,
    "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

def clean_day(value):
    return int(re.sub(r"(st|nd|rd|th)$", "", str(value), flags=re.I))

def parse_history(history):
    h = str(history).strip()

    if not h:
        return None, None, None, "EMPTY", "LOW"

    ambiguous_patterns = [
        r"\band\b",
        r"\+",
        r"reactivat",
        r"re-?activat",
        r"initiated",
        r"submerged",
        r"crack developed",
    ]

    if any(re.search(p, h, flags=re.I) for p in ambiguous_patterns):
        years = re.findall(r"\b(?:19|20)\d{2}\b", h)
        year = int(years[0]) if years else None
        return None, None, year, "AMBIGUOUS", "LOW"

    m = re.fullmatch(r"\s*(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})\s*", h)
    if m:
        day, month, year = map(int, m.groups())
        try:
            d = pd.Timestamp(year=year, month=month, day=day)
            return d.date().isoformat(), d.date().isoformat(), year, "DAY", "HIGH"
        except ValueError:
            return None, None, year, "AMBIGUOUS", "LOW"

    m = re.fullmatch(
        r"\s*(\d{1,2}(?:st|nd|rd|th)?)\s+"
        r"([A-Za-z]+)[,\s-]+(\d{4})\s*",
        h,
        flags=re.I,
    )
    if m:
        day = clean_day(m.group(1))
        month_name = m.group(2).lower()
        year = int(m.group(3))
        if month_name in MONTHS:
            try:
                d = pd.Timestamp(year=year, month=MONTHS[month_name], day=day)
                return d.date().isoformat(), d.date().isoformat(), year, "DAY", "HIGH"
            except ValueError:
                pass

    m = re.fullmatch(r"\s*([A-Za-z]+)[-\s](\d{2}|\d{4})\s*", h, flags=re.I)
    if m:
        month_name = m.group(1).lower()
        year_text = m.group(2)
        if month_name in MONTHS:
            year = int(year_text)
            if len(year_text) == 2:
                year += 2000
            return None, None, year, "MONTH", "MEDIUM"

    m = re.fullmatch(r"\s*((?:19|20)\d{2})\s*", h)
    if m:
        year = int(m.group(1))
        return None, None, year, "YEAR", "MEDIUM"

    years = re.findall(r"\b(?:19|20)\d{2}\b", h)
    year = int(years[0]) if years else None
    return None, None, year, "AMBIGUOUS", "LOW"

def main():
    df = pd.read_csv(INPUT)
    parsed = df["History"].apply(parse_history)
    df["event_date"] = parsed.map(lambda x: x[0])
    df["event_date_end"] = parsed.map(lambda x: x[1])
    df["event_year"] = parsed.map(lambda x: x[2])
    df["date_precision"] = parsed.map(lambda x: x[3])
    df["temporal_confidence"] = parsed.map(lambda x: x[4])
    df["event_date_source"] = "GSI_History"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT, index=False)
    print("Output:", OUTPUT)
    print()
    print("Date precision:")
    print(df["date_precision"].value_counts(dropna=False).to_string())
    print()
    print("Temporal confidence:")
    print(df["temporal_confidence"].value_counts(dropna=False).to_string())
    print()
    print("Daily event dates:", df["event_date"].notna().sum())
    print("Unique daily dates:", df["event_date"].dropna().nunique())

if __name__ == "__main__":
    main()
