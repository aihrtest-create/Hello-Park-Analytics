from backend.reports.sessions import generate_sessions
from backend.reports.playtime import generate_playtime
import traceback

print("Testing Sessions:")
try:
    generate_sessions("2026-03", "/tmp/sessions.xlsx")
    print("Sessions success!")
except Exception as e:
    traceback.print_exc()

print("\nTesting Playtime:")
try:
    generate_playtime("2026-03", "/tmp/playtime.xlsx")
    print("Playtime success!")
except Exception as e:
    traceback.print_exc()
