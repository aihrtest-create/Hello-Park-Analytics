# Hello Park Analytics — Панель отчётов и аналитики

Добро пожаловать в проект **Hello Park Analytics**! Это приложение предназначено для автоматической генерации отчетов в формате Excel (`.xlsx`), вытягивая сырые данные из базы **InfluxDB** через публичный API **Grafana** (`stat.hello.io`).

---

## 📂 Структура проекта

Код проекта разделен на логические папки для поддержания чистоты репозитория:

### 1. Веб-интерфейс и бэкенд
Служит для интерактивной генерации отчетов пользователем через веб-браузер.
* **[backend/](file:///Users/dima/Desktop/My%20project/Hello%20Park%20Data/backend/)** — Серверная часть приложения на Python (Flask).
  * **[app.py](file:///Users/dima/Desktop/My%20project/Hello%20Park%20Data/backend/app.py)** — Главный роутер, принимает HTTP-запросы от интерфейса и вызывает генераторы отчетов.
  * **[reports/](file:///Users/dima/Desktop/My%20project/Hello%20Park%20Data/backend/reports/)** — Модули генерации конкретных типов отчетов:
    * **[common.py](file:///Users/dima/Desktop/My%20project/Hello%20Park%20Data/backend/reports/common.py)** — Общая конфигурация (токен Grafana, адреса API, список активных парков и логика сдвига часовых поясов UTC+3).
    * **[avatars.py](file:///Users/dima/Desktop/My%20project/Hello%20Park%20Data/backend/reports/avatars.py)** — Генерация отчета «Создание аватаров» (по дням, с формулами автоматического расчета Activation Rate в Excel).
    * **[conversion.py](file:///Users/dima/Desktop/My%20project/Hello%20Park%20Data/backend/reports/conversion.py)** — Генерация отчета «Конверсия: Аватар -> Первое задание».
    * **[playtime.py](file:///Users/dima/Desktop/My%20project/Hello%20Park%20Data/backend/reports/playtime.py)** — Генерация отчета «Игровое время» в часах по играм и темам (зонам).
    * **[sessions.py](file:///Users/dima/Desktop/My%20project/Hello%20Park%20Data/backend/reports/sessions.py)** — Генерация отчета «Игровые сессии» по играм и темам (зонам).
* **[frontend/](file:///Users/dima/Desktop/My%20project/Hello%20Park%20Data/frontend/)** — Клиентская часть веб-панели (Vanilla HTML, CSS, JS).
  * **[index.html](file:///Users/dima/Desktop/My%20project/Hello%20Park%20Data/frontend/index.html)** — Разметка страницы (дизайн в современном стиле Glassmorphism).
  * **[script.js](file:///Users/dima/Desktop/My%20project/Hello%20Park%20Data/frontend/script.js)** — Скрипты взаимодействия с API бэкенда (выбор парков, динамические календари для выбора дней, месяцев или произвольных интервалов дат).
  * **[style.css](file:///Users/dima/Desktop/My%20project/Hello%20Park%20Data/frontend/style.css)** — Стили оформления.

### 2. Скрипты для локального анализа
* **[scripts/](file:///Users/dima/Desktop/My%20project/Hello%20Park%20Data/scripts/)** — Вспомогательные скрипты Python, используемые для точечных локальных расчетов, выгрузок сырых данных, анализа LFL (Like-for-Like), канибализации и других разовых аналитических задач.

### 3. Примеры отчетов и шаблоны
* **[examples/](file:///Users/dima/Desktop/My%20project/Hello%20Park%20Data/examples/)** — Готовые файлы экспортированных отчетов (Excel и PDF), сырые дампы JSON/CSV, а также графические логотипы, используемые в PDF-отчетах.

### 4. Архив
* **[archive/](file:///Users/dima/Desktop/My%20project/Hello%20Park%20Data/archive/)** — Устаревшие версии файлов (v3-v7 генераторов PDF), старые тестовые скрипты и заметки по Grafana/InfluxDB.

---

## 🚀 Как запустить проект

### Локальный запуск
1. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
2. Запустите Flask-сервер:
   ```bash
   python3 -m backend.app
   ```
3. Откройте в браузере: **`http://localhost:5001`** *(порт 5001 выбран для бесконфликтной работы на macOS, где порт 5000 занят системным приемником AirPlay)*.

### Продакшн и деплой
Проект развернут на сервере по адресу:
👉 **[https://party.hello-park.io/analytics/](https://party.hello-park.io/analytics/)**

* **Деплой:** Осуществляется автоматически при пуше изменений в ветку `main` репозитория GitHub (`git push origin main`). Никаких сторонних VPS (включая Timeweb) не используется.

---

## 🛠 Добавление нового отчета (Памятка разработчику)

Чтобы расширить возможности панели и добавить новый отчет:
1. **Напишите логику**: Создайте новый файл-генератор в папке `backend/reports/имя_отчета.py` (за основу можно взять существующие отчеты, например `sessions.py`).
2. **Зарегистрируйте в API**: В файле `backend/app.py` импортируйте вашу функцию и добавьте новое условие (`elif report_type == "имя_отчета":`) в обработчик `/api/generate`.
3. **Обновите UI**: В файле `frontend/index.html` добавьте новую радио-кнопку типа `<input type="radio" name="reportType" value="имя_отчета">` с иконкой и текстовым описанием.
