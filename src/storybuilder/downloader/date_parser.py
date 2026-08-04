import re
from datetime import date, datetime


def _adjust_year(dt: datetime, reference_date: datetime) -> datetime:
	year = reference_date.year
	dt = dt.replace(year=year)
	if dt > reference_date:
		dt = dt.replace(year=year - 1)
	return dt


def _parse_with_year(date_str: str) -> date | None:
	for fmt in ("%b %d %Y", "%B %d %Y"):
		try:
			dt = datetime.strptime(date_str, fmt)
			return dt.date()
		except ValueError:
			continue
	return None


def _parse_with_time(date_str: str, reference_date: datetime) -> date | None:
	for fmt in ("%b %d %H:%M", "%B %d %H:%M"):
		try:
			dt = datetime.strptime(date_str, fmt)
			return _adjust_year(dt, reference_date).date()
		except ValueError:
			continue
	return None


def _parse_fallback(date_str: str, reference_date: datetime) -> date | None:
	try:
		match = re.match(r"^([a-zA-Z]+)\s+(\d+)$", date_str)
		if match:
			mon, day = match.groups()
			dt = datetime.strptime(f"{mon} {day}", "%b %d")
			return _adjust_year(dt, reference_date).date()
	except ValueError:
		pass
	return None


def parse_nifty_date(date_str: str, reference_date: datetime | None = None) -> date | None:
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
		reference_date = datetime.now()

	date_str = " ".join(date_str.strip().split())  # Normalize whitespace

	result = _parse_with_year(date_str)
	if result:
		return result

	result = _parse_with_time(date_str, reference_date)
	if result:
		return result

	result = _parse_fallback(date_str, reference_date)
	if result:
		return result

	print(f"Warning: Could not parse date string '{date_str}'")
	return None
