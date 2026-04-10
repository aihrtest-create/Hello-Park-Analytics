import requests
import json
from backend.reports.common import GRAFANA_URL, DATASOURCE_UID, HEADERS, get_month_boundaries

def query_flux(flux_query):
    payload = {
        "queries": [{"refId": "A", "datasource": {"uid": DATASOURCE_UID, "type": "influxdb"}, "query": flux_query, "hide": False}],
        "from": "0", "to": "9999999999999"
    }
    resp = requests.post(f"{GRAFANA_URL}/api/ds/query", headers=HEADERS, json=payload)
    resp.raise_for_status()
    frames = resp.json().get("results", {}).get("A", {}).get("frames", [])
    
    if not frames:
        print("No data (empty frames)")
        return
        
    print(f"Got {len(frames)} frames. Dumping first frame:")
    print("Schema:", json.dumps(frames[0].get("schema", {}), ensure_ascii=False))
    print("Values:", json.dumps(frames[0].get("data", {}).get("values", []), ensure_ascii=False))


if __name__ == "__main__":
    start_date, stop_date, _ = get_month_boundaries("2026-03")
    
    q_sessions_raw = f"""
    from(bucket: "Analytics_AvatarBD")
      |> range(start: {start_date}, stop: {stop_date})
      |> filter(fn: (r) => r["_measurement"] == "SessionStart")
      |> limit(n: 1)
    """
    print("Testing sessions RAW...")
    query_flux(q_sessions_raw)
    
    q_playtime_raw = f"""
    from(bucket: "Analytics_AvatarBD")
      |> range(start: {start_date}, stop: {stop_date})
      |> filter(fn: (r) => r["_measurement"] == "SessionEnd")
      |> limit(n: 1)
    """
    print("\nTesting playtime RAW...")
    query_flux(q_playtime_raw)
