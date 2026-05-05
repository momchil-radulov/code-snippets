#!/usr/bin/env python3
# how to use: mosquitto_sub -v -t "#" | ./mqtt_log.py
import sys
import json
from datetime import datetime, timezone


def generate_default_log_name():
    now = datetime.now()
    return now.strftime("mqtt_messages_%Y-%m-%d_%H-%M.log")


def get_log_file_name():
    if len(sys.argv) > 1:
        return sys.argv[1]
    return generate_default_log_name()


def decode_line(raw_line: bytes):
    """
    UTF-8 -> cp1251 -> cp1252
    """
    for encoding in ("utf-8", "cp1251", "cp1252"):
        try:
            return raw_line.decode(encoding)
        except UnicodeDecodeError:
            continue
    return None


# ===== ЛОГИКА ЗА STATUS МИНУТИ =====

START_TIME = datetime.now()
START_MINUTE = START_TIME.minute
NEXT_MINUTE = (START_MINUTE + 1) % 60
START_HOUR = START_TIME.hour
START_DATE = START_TIME.date()


def is_status_capture_minute() -> bool:
    now = datetime.now()

    # при стартиране: текущата + следващата минута
    if now.date() == START_DATE and now.hour == START_HOUR:
        if now.minute in (START_MINUTE, NEXT_MINUTE):
            return True

    # след това: само NEXT_MINUTE на всеки час
    return now.minute == NEXT_MINUTE


def should_accept(parsed: dict) -> bool:
    msg_type = parsed["message"].get("type")

    if msg_type in ("stat", "stats"):
        return is_status_capture_minute()

    return True


# ===== PARSE =====

def parse_mosquitto_line(line: str):
    line = line.strip()
    if not line:
        return None

    parts = line.split(maxsplit=1)
    if len(parts) != 2:
        return None

    topic, json_text = parts

    try:
        message = json.loads(json_text)
    except json.JSONDecodeError:
        return None

    return {
        "topic": topic,
        "message": message,
        "received_at": datetime.now(timezone.utc).isoformat()
    }


# ===== MAIN =====

def main():
    log_file_name = get_log_file_name()
    print(f"Logging to: {log_file_name}", file=sys.stderr)

    with open(log_file_name, "a", encoding="utf-8") as log_file:
        for raw_line in sys.stdin.buffer:
            line = decode_line(raw_line)

            if line is None:
                print("[SKIP] decode error", file=sys.stderr)
                continue

            parsed = parse_mosquitto_line(line)

            if parsed is None:
                continue

            if not should_accept(parsed):
                continue

            topic = parsed["topic"]
            message = parsed["message"]
            received_at = parsed["received_at"]

            message_json = json.dumps(message, ensure_ascii=False)
            header = f"{topic} : {received_at}"

            # екран
            print(header)
            print(message_json)
            print()

            # файл
            log_file.write(header + "\n")
            log_file.write(message_json + "\n\n")
            log_file.flush()


if __name__ == "__main__":
    main()
