import requests
import pandas as pd
from datetime import datetime
import json

# Конфигурация
GRAFANA_URL = "http://10.0.110.11:3000"
API_TOKEN = "YOUR_GRAFANA_API_TOKEN"
DATASOURCE_UID = "adg0kymjjbf28a"  # UID из твоего JSON

# Заголовки для авторизации
headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Flux запрос для получения привязанных аватаров по дням и паркам
flux_query = '''
from(bucket: "Analytics_AvatarBD")
  |> range(start: 2025-12-31T21:00:00Z, stop: 2026-01-31T21:00:00Z)
  |> filter(fn: (r) => r["_measurement"] == "AvatarLinkedInHome")
  |> group(columns: ["park"])
  |> aggregateWindow(every: 1d, fn: count, createEmpty: false)
  |> yield(name: "avatars_by_day")
'''

# Запрос к Grafana DS Proxy API
payload = {
    "queries": [
        {
            "refId": "A",
            "datasource": {
                "type": "influxdb",
                "uid": DATASOURCE_UID
            },
            "query": flux_query,
            "hide": False,
            "intervalMs": 86400000,
            "maxDataPoints": 1000
        }
    ],
    "from": "1704067200000",  # 2026-01-01
    "to": "1706745600000"      # 2026-02-01
}

print("Отправляю запрос к Grafana API...")
print(f"URL: {GRAFANA_URL}/api/ds/query")

try:
    response = requests.post(
        f"{GRAFANA_URL}/api/ds/query",
        headers=headers,
        json=payload,
        timeout=30
    )
    
    print(f"Статус: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        # Сохраняем сырой ответ для анализа
        with open("raw_response.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("Сырой ответ сохранён в raw_response.json")
        
        # Парсим результаты
        results = []
        
        if "results" in data and "A" in data["results"]:
            frames = data["results"]["A"].get("frames", [])
            
            for frame in frames:
                schema = frame.get("schema", {})
                fields = schema.get("fields", [])
                data_values = frame.get("data", {}).get("values", [])
                
                # Получаем имя парка из labels
                park_name = "Unknown"
                for field in fields:
                    labels = field.get("labels", {})
                    if "park" in labels:
                        park_name = labels["park"]
                        break
                
                # Извлекаем время и значения
                if len(data_values) >= 2:
                    timestamps = data_values[0]
                    values = data_values[1]
                    
                    for ts, val in zip(timestamps, values):
                        # Конвертируем timestamp в дату
                        if isinstance(ts, (int, float)):
                            dt = datetime.fromtimestamp(ts / 1000)
                        else:
                            dt = pd.to_datetime(ts)
                        
                        # Сдвигаем на 1 день назад (данные приходят со сдвигом)
                        from datetime import timedelta
                        dt = dt - timedelta(days=1)
                        
                        results.append({
                            "Дата": dt.strftime("%Y-%m-%d"),
                            "Парк": park_name,
                            "Привязано аватаров": val
                        })
        
        if results:
            df = pd.DataFrame(results)
            
            # Pivot таблица: даты по строкам, парки по столбцам
            pivot_df = df.pivot_table(
                index="Дата", 
                columns="Парк", 
                values="Привязано аватаров",
                aggfunc="sum"
            ).fillna(0).astype(int)
            
            # Фильтруем только январь 2026
            pivot_df = pivot_df[pivot_df.index.str.startswith("2026-01")]
            
            # Добавляем итого по строкам (за день)
            pivot_df["ИТОГО"] = pivot_df.sum(axis=1)
            
            # Добавляем итого по паркам (внизу)
            totals = pivot_df.sum(axis=0)
            totals.name = "ИТОГО по парку"
            pivot_df = pd.concat([pivot_df, totals.to_frame().T])
            
            # Сохраняем в Excel
            output_file = "avatars_linked_january_2026.xlsx"
            pivot_df.to_excel(output_file)
            print(f"\n✅ Данные сохранены в {output_file}")
            print(f"\nПревью данных:")
            print(pivot_df.head(10))
            print(f"\n... всего {len(pivot_df)} дней")
        else:
            print("⚠️ Данные не найдены в ответе")
            print("Структура ответа:")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
    
    else:
        print(f"❌ Ошибка: {response.status_code}")
        print(response.text)

except requests.exceptions.ConnectionError:
    print("❌ Не удалось подключиться к Grafana")
    print("Убедись что VPN включен и адрес правильный")
except Exception as e:
    print(f"❌ Ошибка: {e}")
