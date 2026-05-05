#!/usr/bin/env python3
# python3 -m pip install paho-mqtt
# chmod +x mqtt_log_replay.py
# how to use: /mqtt_log_replay.py file.log --filter 'iot/dev123' --seconds 2 --dry-run
import argparse
import json
import sys
import time

import paho.mqtt.client as mqtt


def parse_args():
    parser = argparse.ArgumentParser(
        description="Replay MQTT messages from mqtt_log.py log file using paho-mqtt"
    )

    parser.add_argument("log_file", help="Лог файлът за replay")

    parser.add_argument(
        "-s", "--seconds",
        type=float,
        default=1.0,
        help="Пауза между съобщенията, default: 1.0"
    )

    parser.add_argument(
        "-f", "--filter",
        default="",
        help="Част от topic-а. Ако е подадено, праща само topic-и, които го съдържат"
    )

    parser.add_argument("--host", default="127.0.0.1", help="MQTT host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT port")
    parser.add_argument("--qos", type=int, default=0, choices=[0, 1, 2], help="MQTT QoS")
    parser.add_argument("--retain", action="store_true", help="Publish with retain flag")

    parser.add_argument("--username", default=None, help="MQTT username")
    parser.add_argument("--password", default=None, help="MQTT password")

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Само показва, без да публикува"
    )

    return parser.parse_args()


def parse_header(line: str):
    """
    Очаква:
    iot/dev123/out : 2026-05-05T12:34:56.123456+00:00
    """

    if " : " not in line:
        return None, None

    topic, received_at = line.split(" : ", 1)
    topic = topic.strip()
    received_at = received_at.strip()

    if not topic:
        return None, None

    return topic, received_at


def read_messages(log_file):
    """
    Чете двойки:
    topic : timestamp
    JSON payload

    Празните редове се пропускат.
    """

    with open(log_file, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    i = 0

    while i < len(lines):
        header = lines[i].strip()

        if not header:
            i += 1
            continue

        topic, received_at = parse_header(header)

        if topic is None:
            i += 1
            continue

        if i + 1 >= len(lines):
            break

        payload = lines[i + 1].strip()

        try:
            json.loads(payload)
        except json.JSONDecodeError:
            print(f"[SKIP] invalid JSON after topic={topic}", file=sys.stderr)
            i += 2
            continue

        yield topic, received_at, payload

        i += 2


def connect_mqtt(args):
    client = mqtt.Client()

    if args.username:
        client.username_pw_set(args.username, args.password)

    print(f"Connecting to MQTT {args.host}:{args.port} ...", file=sys.stderr)

    client.connect(args.host, args.port, keepalive=60)
    client.loop_start()

    return client


def main():
    args = parse_args()

    client = None

    if not args.dry_run:
        client = connect_mqtt(args)

    sent = 0
    skipped = 0
    errors = 0

    try:
        for topic, received_at, payload in read_messages(args.log_file):
            if args.filter and args.filter not in topic:
                skipped += 1
                continue

            print(f"{topic} : {received_at}")
            print(payload)
            print()

            if not args.dry_run:
                info = client.publish(
                    topic,
                    payload=payload,
                    qos=args.qos,
                    retain=args.retain
                )

                # wait_for_publish е полезно особено при qos 1/2
                info.wait_for_publish()

                if info.rc != mqtt.MQTT_ERR_SUCCESS:
                    print(
                        f"[ERROR] publish failed topic={topic} rc={info.rc}",
                        file=sys.stderr
                    )
                    errors += 1
                else:
                    sent += 1
            else:
                sent += 1

            time.sleep(args.seconds)

    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)

    finally:
        if client is not None:
            client.loop_stop()
            client.disconnect()

    print(
        f"Done. sent={sent}, skipped={skipped}, errors={errors}",
        file=sys.stderr
    )


if __name__ == "__main__":
    main()
