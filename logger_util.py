# logger_util.py
import json
import datetime
from pathlib import Path

LOG_FILE = Path("debate_log.txt")

def log_event(event_type, payload):
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "type": event_type,
        "payload": payload
    }
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
