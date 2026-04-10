import requests
import json
from backend.reports.common import GRAFANA_URL, DATASOURCE_UID, HEADERS

def query_flux(flux_query):
    payload = {
        "queries": [{"refId": "A", "datasource": {"uid": DATASOURCE_UID, "type": "influxdb"}, "query": flux_query, "hide": False}],
        "from": "0", "to": "9999999999999"
    }
    resp = requests.post(f"{GRAFANA_URL}/api/ds/query", headers=HEADERS, json=payload)
    resp.raise_for_status()
    frames = resp.json().get("results", {}).get("A", {}).get("frames", [])
    
    if not frames:
        return "No data"
        
    for frame in frames:
        print("Schema:", json.dumps(frame.get("schema", {}), ensure_ascii=False, indent=2))
        print("Values:", json.dumps(frame.get("data", {}).get("values", []), ensure_ascii=False, indent=2))

if __name__ == "__main__":

    q_sessionEnd = """
    from(bucket: "Analytics_AvatarBD")
      |> range(start: -30d)
      |> filter(fn: (r) => r["_measurement"] == "SessionEnd")
      |> limit(n: 1)
    """
    print("Testing SessionEnd...")
    query_flux(q_sessionEnd)
    
    q_other = """
    from(bucket: "Analytics_AvatarBD")
      |> range(start: -30d)
      |> filter(fn: (r) => r["_measurement"] == "AchievementCounted")
      |> limit(n: 1)
    """
    print("Testing AchievementCounted...")
    query_flux(q_other)
