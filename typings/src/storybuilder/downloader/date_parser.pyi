import re
from datetime import date, datetime


def parse_nifty_date(date_str: str, reference_date: datetime | None = None) -> date | None: ...
