import os
import calendar
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
    load_dotenv(dotenv_path="../server/.env")
    load_dotenv(dotenv_path="./server/.env")
except ImportError:
    pass

GRAFANA_URL = "https://stat.hello.io"
DATASOURCE_UID = "adg0kymjjbf28a"

def get_api_token():
    token = (
        os.environ.get("GRAFANA_API_TOKEN") or
        os.environ.get("API_TOKEN") or
        os.environ.get("GRAFANA_TOKEN") or
        ""
    ).strip().strip('"').strip("'")
    return token




def get_headers():
    return {
        "Authorization": f"Bearer {get_api_token()}",
        "Content-Type": "application/json"
    }

class DynamicHeaders(dict):
    def __getitem__(self, key):
        return get_headers()[key]
    def get(self, key, default=None):
        return get_headers().get(key, default)
    def items(self):
        return get_headers().items()
    def keys(self):
        return get_headers().keys()
    def values(self):
        return get_headers().values()
    def __iter__(self):
        return iter(get_headers())
    def __len__(self):
        return len(get_headers())
    def copy(self):
        return get_headers()

HEADERS = DynamicHeaders()


PARK_ORDER = [
    "AVIAPARK", "Atyrau", "BAKU", "BOGOTA-NUESTRO", "DUBAI", "KASPIYSK",
    "MEGA", "OMAN", "RIVIERA", "SAKHALIN", "SELIGERSKAYA", "SOCHI", "VLADIKAVKAZ", "VORONEZH"
]

def normalize_park_name(park: str) -> str:
    if not park:
        return "Unknown"
    if park == "Kaspiysk":
        return "KASPIYSK"
    if park == "Seligerskaya":
        return "SELIGERSKAYA"
    if park == "BOGOTA NUESTRO":
        return "BOGOTA-NUESTRO"
    return park

def expand_selected_parks(selected_parks: list) -> list:
    expanded = set(selected_parks)
    if "KASPIYSK" in expanded or "Kaspiysk" in expanded:
        expanded.add("KASPIYSK")
        expanded.add("Kaspiysk")
    if "SELIGERSKAYA" in expanded or "Seligerskaya" in expanded:
        expanded.add("SELIGERSKAYA")
        expanded.add("Seligerskaya")
    if "BOGOTA-NUESTRO" in expanded or "BOGOTA NUESTRO" in expanded:
        expanded.add("BOGOTA-NUESTRO")
        expanded.add("BOGOTA NUESTRO")
    return list(expanded)


def get_time_boundaries(date_val: str, period_type: str):
    """
    Returns start_date, stop_date based on period (day, month, year, custom) with MSK timezone offset.
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
    elif period_type == "custom":
        # date_val: "YYYY-MM-DD_to_YYYY-MM-DD"
        start_str, stop_str = date_val.split("_to_")
        year_s, month_s, day_s = map(int, start_str.split("-"))
        dt_s = datetime(year_s, month_s, day_s)
        import datetime as dt_lib
        prev_s = dt_s - dt_lib.timedelta(days=1)
        
        start_date = f"{prev_s.year}-{prev_s.month:02d}-{prev_s.day:02d}T21:00:00Z"
        stop_date = f"{stop_str}T21:00:00Z"
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
