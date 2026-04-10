import subprocess
import time
import os
from dotenv import load_dotenv

load_dotenv()

CLI_PATH = os.getenv("PRITUNL_CLI_PATH", "/Applications/Pritunl.app/Contents/Resources/pritunl-client")
PROFILE_ID = os.getenv("PRITUNL_PROFILE_ID", "ginjhq29gglhftr5")
TARGET_HOST = "10.0.110.11"

def run_cli_command(args):
    """Выполняет команду pritunl-client и возвращает вывод."""
    try:
        result = subprocess.run([CLI_PATH] + args, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка Pritunl CLI: {e}")
        print(f"Вывод ошибки: {e.stderr}")
        return None

def is_connected():
    """Проверяет доступность Grafana через пинг."""
    try:
        # -c 1 (1 пакет), -W 1 (тайм-аут 1 сек)
        subprocess.run(["ping", "-c", "1", "-t", "2", TARGET_HOST], capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def connect():
    """Подключает VPN и ждет доступности хоста."""
    if is_connected():
        print(f"✅ VPN уже подключен (хост {TARGET_HOST} доступен)")
        return True

    print(f"🔄 Подключаю VPN Pritunl (ID: {PROFILE_ID})...")
    # Проверяем состояние
    output = run_cli_command(["list"])
    if output and PROFILE_ID in output:
        # Запускаем соединение
        run_cli_command(["start", PROFILE_ID])
        
        # Ждем готовности (до 30 секунд)
        for i in range(15):
            print(f"   Ожидание сети... ({i*2}с)")
            time.sleep(2)
            if is_connected():
                print(f"✅ VPN успешно подключен!")
                return True
        
        print("❌ Тайм-аут ожидания подключения VPN")
        return False
    else:
        print(f"❌ Профиль VPN с ID {PROFILE_ID} не найден в списке.")
        return False

def disconnect():
    """Отключает VPN."""
    print("🔄 Отключаю VPN...")
    run_cli_command(["stop", PROFILE_ID])
    time.sleep(2)
    if not is_connected():
        print("✅ VPN отключен.")
        return True
    return False

if __name__ == "__main__":
    # Тестовый запуск:
    if connect():
        print("Тест пройден: соединение установлено.")
        # disconnect() # Раскомментировать для теста отключения
