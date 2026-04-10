import requests
import pandas as pd
import json
from datetime import datetime, timedelta

# =========================================
# КОНФИГУРАЦИЯ
# =========================================
GRAFANA_URL = "http://10.0.110.11:3000"
API_TOKEN = "YOUR_GRAFANA_API_TOKEN"
DATASOURCE_UID = "adg0kymjjbf28a"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# =========================================
# Февраль 2026 (МСК → UTC: -3ч)
# =========================================
flux_query = '''
from(bucket: "Analytics_AvatarBD")
  |> range(start: 2026-01-31T21:00:00Z, stop: 2026-02-28T21:00:00Z)
  |> filter(fn: (r) => r["_measurement"] == "AvatarLinkedInHome")
  |> group(columns: ["park"])
  |> aggregateWindow(every: 1d, fn: count, createEmpty: false)
  |> yield(name: "avatars_by_day")
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

print("🔄 Запрашиваю данные по привязанным аватарам за февраль 2026...")
print(f"   URL: {GRAFANA_URL}")
print()

try:
    response = requests.post(
        f"{GRAFANA_URL}/api/ds/query",
        headers=headers,
        json=payload,
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        
        results = []
        frames = data.get("results", {}).get("A", {}).get("frames", [])
        
        print(f"   Получено фреймов: {len(frames)}")
        
        for frame in frames:
            schema = frame.get("schema", {})
            frame_data = frame.get("data", {})
            
            # Определяем парк из labels
            park_name = "Unknown"
            fields = schema.get("fields", [])
            for field in fields:
                labels = field.get("labels", {})
                if "park" in labels:
                    park_name = labels["park"]
                    break
            
            values_list = frame_data.get("values", [])
            if len(values_list) >= 2:
                timestamps = values_list[0]
                values = values_list[1]
                
                if timestamps and values:
                    for ts, val in zip(timestamps, values):
                        # Конвертируем timestamp в дату
                        if isinstance(ts, (int, float)):
                            dt = datetime.fromtimestamp(ts / 1000)
                        else:
                            dt = pd.to_datetime(ts)
                        
                        # Корректируем на московское время (+3 часа)
                        dt = dt + timedelta(hours=3)
                        
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
            
            # Фильтруем только февраль 2026
            pivot_df = pivot_df[pivot_df.index.str.startswith("2026-02")]
            
            # Добавляем итого по строкам (за день)
            pivot_df["ИТОГО"] = pivot_df.sum(axis=1)
            
            # Добавляем итого по паркам (внизу)
            totals = pivot_df.sum(axis=0)
            totals.name = "ИТОГО по парку"
            pivot_df = pd.concat([pivot_df, totals.to_frame().T])
            
            # Сохраняем в Excel
            output_file = "/Users/dima/Downloads/avatars_february_2026.xlsx"
            
            from openpyxl.styles import PatternFill, Font, Alignment
            from openpyxl.utils import get_column_letter
            
            with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
                pivot_df.to_excel(writer, sheet_name="Февраль")
                ws = writer.sheets["Февраль"]
                
                last_data_row = ws.max_row  # строка ИТОГО по парку
                last_col = ws.max_column
                
                # Форматирование заголовков
                orange = PatternFill("solid", fgColor="FF6B00")
                for cell in ws[1]:
                    cell.fill = orange
                    cell.font = Font(bold=True, color="FFFFFF", size=11)
                    cell.alignment = Alignment(horizontal="center")
                
                # Строка ИТОГО — серый фон
                gray = PatternFill("solid", fgColor="E0E0E0")
                for cell in ws[last_data_row]:
                    cell.fill = gray
                    cell.font = Font(bold=True)
                
                # --- Кол-во проданных билетов (пустая, для ручного заполнения) ---
                билеты_row = last_data_row + 2
                ws.cell(билеты_row, 1, "Кол-во проданных \nбилетов")
                ws.cell(билеты_row, 1).font = Font(bold=True)
                ws.cell(билеты_row, 1).alignment = Alignment(wrap_text=True)
                # Формула ИТОГО по билетам
                col_b = get_column_letter(2)
                col_last_park = get_column_letter(last_col - 1)
                col_итого = get_column_letter(last_col)
                ws.cell(билеты_row, last_col).value = f"=SUM({col_b}{билеты_row}:{col_last_park}{билеты_row})"
                ws.cell(билеты_row, last_col).font = Font(bold=True)
                
                # Жёлтый фон для строки билетов
                yellow = PatternFill("solid", fgColor="FFF2CC")
                for col in range(1, last_col + 1):
                    ws.cell(билеты_row, col).fill = yellow
                
                # --- Activation rate ---
                rate_row = билеты_row + 2
                ws.cell(rate_row, 1, "Activation rate")
                ws.cell(rate_row, 1).font = Font(bold=True)
                for col in range(2, last_col):  # для каждого парка (без ИТОГО)
                    cl = get_column_letter(col)
                    ws.cell(rate_row, col).value = f"={cl}{last_data_row}/{cl}{билеты_row}*100"
                    ws.cell(rate_row, col).number_format = '0.0'
                
                green = PatternFill("solid", fgColor="D5F5E3")
                for col in range(1, last_col + 1):
                    ws.cell(rate_row, col).fill = green
                
                # --- Activation rate средняя ---
                avg_row = rate_row + 3
                ws.cell(avg_row, 1, "Activation rate\nсредняя")
                ws.cell(avg_row, 1).font = Font(bold=True)
                ws.cell(avg_row, 1).alignment = Alignment(wrap_text=True)
                first_park = get_column_letter(2)
                ws.cell(avg_row, 2).value = f"=({col_итого}{last_data_row}-{first_park}{last_data_row})/{col_итого}{билеты_row}"
                ws.cell(avg_row, 2).number_format = '0.00'
                
                # Автоширина колонок
                for col_cells in ws.columns:
                    max_len = max(len(str(c.value or "")) for c in col_cells) + 3
                    ws.column_dimensions[col_cells[0].column_letter].width = min(max_len, 20)
                ws.column_dimensions["A"].width = 22
            
            print(f"\n✅ Данные сохранены в {output_file}")
            print(f"\nПревью данных:")
            print(pivot_df.to_string())
            print(f"\n... всего {len(pivot_df) - 1} дней")
            print()
            print("💡 Заполни строку 'Кол-во проданных билетов' (жёлтая) —")
            print("   Activation rate посчитается автоматически!")
        else:
            print("⚠️ Данные не найдены в ответе")
            print("Структура ответа:")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
    
    else:
        print(f"❌ Ошибка: {response.status_code}")
        print(response.text[:500])

except requests.exceptions.ConnectionError:
    print("❌ Не удалось подключиться к Grafana")
    print("Убедись что VPN включен и адрес правильный")
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
