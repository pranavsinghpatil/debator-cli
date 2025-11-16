# logger_util.py
import json
import datetime
from pathlib import Path

GLOBAL_LOG_FILE = Path("global_debate_log.txt")
DEBATE_LOG_FILE = None

def set_log_file(path):
    global DEBATE_LOG_FILE
    DEBATE_LOG_FILE = Path(path)
    # Clear the debate log file if it exists
    if DEBATE_LOG_FILE.exists():
        DEBATE_LOG_FILE.unlink()

def log_event(event_type, payload):
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "type": event_type,
        "payload": payload
    }
    # Write to global log file
    with GLOBAL_LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    # Write to debate-specific log file if set
    if DEBATE_LOG_FILE:
        with DEBATE_LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
