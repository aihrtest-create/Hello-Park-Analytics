import requests
import pandas as pd
import json

# =========================================
# КОНФИГУРАЦИЯ
# =========================================
GRAFANA_URL = "https://stat.hello.io"
API_TOKEN = "YOUR_GRAFANA_API_TOKEN"
DATASOURCE_UID = "adg0kymjjbf28a"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# Март 2026: начало 1 марта 00:00 МСК, конец 1 апреля 00:00 МСК
START_DATE = "2026-02-28T21:00:00Z"
STOP_DATE = "2026-03-31T21:00:00Z"

def run_query(measurement, label):
    """Выполняет Flux-запрос, подсчитывающий уникальные id по паркам за месяц."""
    flux_query = f'''
    from(bucket: "Analytics_AvatarBD")
      |> range(start: {START_DATE}, stop: {STOP_DATE})
      |> filter(fn: (r) => r["_measurement"] == "{measurement}")
      |> filter(fn: (r) => exists r["id"])
      |> group(columns: ["park", "id"])
      |> limit(n: 1)
      |> group(columns: ["park"])
      |> count(column: "_value")
      |> yield(name: "{label}")
    '''

    payload = {
        "queries": [{
            "refId": "A",
            "datasource": {"type": "influxdb", "uid": DATASOURCE_UID},
            "query": flux_query,
            "hide": False
        }],
        "from": "0",
        "to": "9999999999999"
    }

    print(f"🔄 Запрашиваю {measurement}...")
    try:
        response = requests.post(f"{GRAFANA_URL}/api/ds/query", headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        results = {}
        frames = data.get("results", {}).get("A", {}).get("frames", [])
        for frame in frames:
            schema = frame.get("schema", {})
            park_name = "Unknown"
            
            for field in schema.get("fields", []):
                labels = field.get("labels", {})
                if "park" in labels:
                    park_name = labels["park"]
                    break
                    
            values_list = frame.get("data", {}).get("values", [])
            if len(values_list) > 0 and len(values_list[0]) > 0:
                count = values_list[0][0]  # count is the first field since group and count returns scalar per series
                results[park_name] = count
                
        return results
    except Exception as e:
        print(f"❌ Ошибка в {measurement}: {e}")
        return {}

print(f"📡 Подключение к {GRAFANA_URL} без VPN...")

# 1. Получаем созданные аватары
avatars_data = run_query("AvatarLinkedInHome", "avatars")

# 2. Получаем первое задание
tasks_data = run_query("AchievementCounted", "tasks")

# Объединяем парки (исключая OFFICE и неизвестные значения)
all_parks = sorted([p for p in set(avatars_data.keys()).union(set(tasks_data.keys())) if p != "OFFICE" and p != "Unknown"])

rows = []
for park in all_parks:
    avatars = avatars_data.get(park, 0)
    tasks = tasks_data.get(park, 0)
    
    # Считаем конверсию
    conversion = (tasks / avatars * 100) if avatars > 0 else 0
    
    rows.append({
        "Парк": park,
        "Создано аватаров": avatars,
        "Хотя бы одно задание": tasks,
        "Конверсия (%)": conversion
    })

# Добавляем строку ИТОГО
total_avatars = sum(avatars_data.values())
total_tasks = sum(tasks_data.values())
total_conversion = (total_tasks / total_avatars * 100) if total_avatars > 0 else 0

rows.append({
    "Парк": "ИТОГО",
    "Создано аватаров": total_avatars,
    "Хотя бы одно задание": total_tasks,
    "Конверсия (%)": total_conversion
})

df = pd.DataFrame(rows)

# Жестко заданный порядок парков согласно скриншоту
PARK_ORDER = [
    "AVIAPARK", "Atyrau", "BAKU", "BOGOTA-NUESTRO", "DUBAI", "Kaspiysk",
    "MEGA", "RIVIERA", "SAKHALIN", "SELIGERSKAYA", "SOCHI", "VLADIKAVKAZ"
]

# Настраиваем категориальный тип для точной сортировки
df_data = df.iloc[:-1].copy()
df_data["Парк"] = pd.Categorical(df_data["Парк"], categories=PARK_ORDER, ordered=True)
df_data = df_data.sort_values("Парк")

df_total = df.iloc[[-1]]
df_final = pd.concat([df_data, df_total], ignore_index=True)

# Округление конверсии для красивого вывода
df_final["Конверсия (%)"] = df_final["Конверсия (%)"].round(1)

# Сохраняем в Excel
output_file = "/Users/dima/Desktop/Hello Park Data/conversion_march_2026.xlsx"

from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter

with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    df_final.to_excel(writer, sheet_name="Конверсия 마рт 2026", index=False)
    ws = writer.sheets["Конверсия 마рт 2026"]
    
    # Стили
    orange = PatternFill("solid", fgColor="FF6B00")
    header_font = Font(bold=True, color="FFFFFF", size=11)
    center = Alignment(horizontal="center")
    
    gray = PatternFill("solid", fgColor="E0E0E0")
    bold_font = Font(bold=True)
    
    green = PatternFill("solid", fgColor="D5F5E3")
    
    # Форматируем заголовки
    for col in range(1, len(df_final.columns) + 1):
        cell = ws.cell(row=1, column=col)
        cell.fill = orange
        cell.font = header_font
        cell.alignment = center
        
    last_row = ws.max_row
    
    # Форматируем строку ИТОГО
    for col in range(1, len(df_final.columns) + 1):
        cell = ws.cell(row=last_row, column=col)
        cell.fill = gray
        cell.font = bold_font
        
    # Форматируем колонки конверсии (4 столбец)
    for row in range(2, last_row + 1):
        cell = ws.cell(row=row, column=4)
        cell.fill = green
        cell.number_format = '0.0"%"'
        
    # Ширина колонок
    ws.column_dimensions["A"].width = 20
    ws.column_dimensions["B"].width = 22
    ws.column_dimensions["C"].width = 25
    ws.column_dimensions["D"].width = 16

print(f"\n✅ Данные сохранены в {output_file}")
print("\nПревью данных:")
print(df_final.to_string())
