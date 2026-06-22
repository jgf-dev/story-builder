import datetime
import re


def parse_nifty_date(date_str, reference_date=None):
    """
    Parses Nifty date strings which can be in two formats:
    - Standard Unix ls older file format: 'Dec  4  2025' -> MMM DD YYYY
    - Standard Unix ls recent file format: 'Jun  6 08:55' or 'May 12 19:52' -> MMM DD HH:MM (no year)

    If the year is missing, it is inferred based on the reference_date (defaulting to today).
    If the inferred date would be in the future relative to the reference_date, it is
    assumed to be from the previous year.
    """
    if not date_str:
        return None

    if not reference_date:
        reference_date = datetime.datetime.now()

    date_str = " ".join(date_str.strip().split())  # Normalize whitespace

    # Try parsing with year (MMM DD YYYY)
    for fmt in ("%b %d %Y", "%B %d %Y"):
        try:
            dt = datetime.datetime.strptime(date_str, fmt)
            return dt.date()
        except ValueError:
            continue

    # Try parsing with time (MMM DD HH:MM)
    for fmt in ("%b %d %H:%M", "%B %d %H:%M"):
        try:
            dt = datetime.datetime.strptime(date_str, fmt)
            # Impute current year
            year = reference_date.year
            dt = dt.replace(year=year)
            # If the date is in the future, it belongs to the previous year
            if dt > reference_date:
                dt = dt.replace(year=year - 1)
            return dt.date()
        except ValueError:
            continue

    # Fallback to try matching just month and day if time parsing failed
    # (e.g. sometimes it might just be 'Jun 6')
    try:
        # Match 'MMM DD'
        match = re.match(r"^([a-zA-Z]+)\s+(\d+)$", date_str)
        if match:
            mon, day = match.groups()
            dt = datetime.datetime.strptime(f"{mon} {day}", "%b %d")
            year = reference_date.year
            dt = dt.replace(year=year)
            if dt > reference_date:
                dt = dt.replace(year=year - 1)
            return dt.date()
    except ValueError:
        pass

    print(f"Warning: Could not parse date string '{date_str}'")
    return None
