import requests
import os
import json
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

GRAFANA_URL = os.getenv("GRAFANA_URL")
API_TOKEN = os.getenv("API_TOKEN")
DATASOURCE_UID = os.getenv("DATASOURCE_UID")

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
}

def run_query(flux, start_str, end_str, label=""):
    """Отправляет Flux-запрос к Grafana API."""
    payload = {
        "queries": [{
            "refId": "A",
            "datasource": {"type": "influxdb", "uid": DATASOURCE_UID},
            "query": flux,
        }],
        "from": "0",  # Можно использовать 0, так как фильтр временного диапазона внутри Flux
        "to": "9999999999999",
    }
    try:
        response = requests.post(
            f"{GRAFANA_URL}/api/ds/query",
            headers=HEADERS,
            json=payload,
            timeout=120
        )
        if response.status_code != 200:
            print(f"    [HTTP {response.status_code}] {label}: {response.text[:200]}")
            return None
        return response.json()
    except Exception as e:
        print(f"    [Ошибка запроса] {label}: {e}")
        return None

def parse_results(data, group_by_field=None):
    """Парсит ответ от Grafana в удобный список словарей."""
    results = []
    try:
        frames = data.get("results", {}).get("A", {}).get("frames", [])
        for frame in frames:
            schema = frame.get("schema", {})
            data_values = frame.get("data", {})
            fields = schema.get("fields", [])
            
            # Извлекаем метаданные (labels)
            labels = {}
            for field in fields:
                labels.update(field.get("labels", {}))
            
            group_val = labels.get(group_by_field, "Unknown") if group_by_field else None
            
            values_list = data_values.get("values", [])
            if len(values_list) >= 2:
                timestamps = values_list[0]
                values = values_list[1]
                
                for ts, val in zip(timestamps, values):
                    # Конвертируем timestamp
                    if isinstance(ts, (int, float)):
                        dt = datetime.fromtimestamp(ts / 1000)
                    else:
                        dt = pd.to_datetime(ts)
                    
                    # Стандартная коррекция на МСК (+3 часа)
                    dt_msk = dt + timedelta(hours=3)
                    
                    item = {
                        "date": dt_msk.strftime("%Y-%m-%d"),
                        "value": val
                    }
                    if group_by_field:
                        item[group_by_field] = group_val
                    
                    # Если есть другие ярлыки (например, zone), добавим их
                    if "zone" in labels:
                        item["zone"] = labels["zone"]
                        
                    results.append(item)
    except Exception as e:
        print(f"    [Ошибка парсинга] {e}")
    return results
