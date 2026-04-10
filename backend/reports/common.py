import os
import calendar
from datetime import datetime

GRAFANA_URL = "https://stat.hello.io"
API_TOKEN = "YOUR_GRAFANA_API_TOKEN"
DATASOURCE_UID = "adg0kymjjbf28a"

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Жестко заданный порядок парков согласно скриншоту
PARK_ORDER = [
    "AVIAPARK", "Atyrau", "BAKU", "BOGOTA-NUESTRO", "DUBAI", "Kaspiysk",
    "MEGA", "RIVIERA", "SAKHALIN", "SELIGERSKAYA", "SOCHI", "VLADIKAVKAZ"
]

def get_time_boundaries(date_val: str, period_type: str):
    """
    Returns start_date, stop_date based on period (day, month, year) with MSK timezone offset.
    """
    if period_type == "day":
        # date_val: "YYYY-MM-DD"
        year, month, day = map(int, date_val.split("-"))
        dt = datetime(year, month, day)
        # Previous day 21:00 UTC
        import datetime as dt_lib
        prev = dt - dt_lib.timedelta(days=1)
        start_date = f"{prev.year}-{prev.month:02d}-{prev.day:02d}T21:00:00Z"
        stop_date = f"{year}-{month:02d}-{day:02d}T21:00:00Z"
        return start_date, stop_date, date_val
    elif period_type == "year":
        # date_val: "YYYY"
        year = int(date_val)
        start_date = f"{year-1}-12-31T21:00:00Z"
        stop_date = f"{year}-12-31T21:00:00Z"
        return start_date, stop_date, date_val
    else:
        # Default to month logic "YYYY-MM"
        year, month = map(int, date_val.split("-"))
        if month == 1:
            start_date = f"{year-1}-12-31T21:00:00Z"
        else:
            last_day_prev = calendar.monthrange(year, month - 1)[1]
            start_date = f"{year}-{month-1:02d}-{last_day_prev:02d}T21:00:00Z"
            
        last_day = calendar.monthrange(year, month)[1]
        stop_date = f"{year}-{month:02d}-{last_day:02d}T21:00:00Z"
        return start_date, stop_date, date_val

