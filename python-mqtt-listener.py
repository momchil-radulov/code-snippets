#!/usr/bin/env python3
"""Lightweight MQTT microservice that syncs device stg_list to Postgres settings tables.

Environment variables:
    MQTT_SETTINGS_HOST (default: 127.0.0.1)
    MQTT_SETTINGS_PORT (default: 1883)
    MQTT_SETTINGS_USERNAME
    MQTT_SETTINGS_PASSWORD
    MQTT_SETTINGS_CLIENT_ID (default: settings-listener)
    MQTT_SETTINGS_TOPIC (default: +/+/out)
    MQTT_SETTINGS_QOS (default: 1)
    MQTT_SETTINGS_KEEPALIVE (default: 60)

    SETTINGS_DB_DSN (default: postgresql://iotuser:iotpass@localhost:5432/iotdb)
    SETTINGS_DB_POOL_MIN (default: 1)
    SETTINGS_DB_POOL_MAX (default: 5)

    LOG_LEVEL (default: INFO)


requirements.txt
    paho-mqtt
    psycopg2-binary

"""

from __future__ import annotations

import json
import logging
import os
import signal
import sys
from contextlib import contextmanager
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import paho.mqtt.client as mqtt
from psycopg2 import pool
from psycopg2.extras import execute_values

# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------

MQTT_SEPARATORS: Tuple[str, str] = (",", ":")
START_REQUEST_PAYLOAD = json.dumps({"type": "req", "req": "stg_list"}, separators=MQTT_SEPARATORS)


def env_str(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def setup_logging() -> None:
    level = env_str("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


# ---------------------------------------------------------------------------
# Database access layer
# ---------------------------------------------------------------------------


class DatabasePool:
    def __init__(self) -> None:
        dsn = env_str("SETTINGS_DB_DSN", "postgresql://iotuser:iotpass@localhost:5432/iotdb")
        min_conn = env_int("SETTINGS_DB_POOL_MIN", 1)
        max_conn = env_int("SETTINGS_DB_POOL_MAX", 5)
        if min_conn > max_conn:
            max_conn = min_conn
        self._pool = pool.SimpleConnectionPool(min_conn, max_conn, dsn=dsn)

    @contextmanager
    def connection(self):  # type: ignore[override]
        conn = self._pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._pool.putconn(conn)

    def close(self) -> None:
        self._pool.closeall()


# ---------------------------------------------------------------------------
# Core service
# ---------------------------------------------------------------------------


class SettingsSyncService:
    def __init__(self) -> None:
        self.log = logging.getLogger(self.__class__.__name__)
        self.db = DatabasePool()
        self.client = self._create_mqtt_client()
        self.topic = env_str("MQTT_SETTINGS_TOPIC", "+/+/out")
        self.qos = env_int("MQTT_SETTINGS_QOS", 1)
        self.keepalive = env_int("MQTT_SETTINGS_KEEPALIVE", 60)

    # MQTT setup ---------------------------------------------------------
    def _create_mqtt_client(self) -> mqtt.Client:
        client_id = env_str("MQTT_SETTINGS_CLIENT_ID", "settings-listener")
        clean_session = True
        client = mqtt.Client(client_id=client_id, clean_session=clean_session, protocol=mqtt.MQTTv311)

        username = env_str("MQTT_SETTINGS_USERNAME")
        password = env_str("MQTT_SETTINGS_PASSWORD")
        if username:
            client.username_pw_set(username, password or "")

        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_message = self._on_message
        client.reconnect_delay_set(min_delay=1, max_delay=60)
        return client

    def start(self) -> None:
        host = env_str("MQTT_SETTINGS_HOST", "127.0.0.1")
        port = env_int("MQTT_SETTINGS_PORT", 1883)
        self.log.info("Connecting to MQTT broker %s:%s", host, port)
        self.client.connect(host, port, keepalive=self.keepalive)
        try:
            self.client.loop_forever(retry_first_connection=True)
        except KeyboardInterrupt:
            self.log.info("Stopping service (Ctrl+C)")
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        try:
            self.client.loop_stop()
        except Exception:
            pass
        try:
            self.client.disconnect()
        except Exception:
            pass
        self.db.close()

    # MQTT callbacks -----------------------------------------------------
    def _on_connect(self, client: mqtt.Client, userdata: Any, flags: Dict[str, Any], rc: int) -> None:
        if rc != 0:
            self.log.error("MQTT connect failed rc=%s", rc)
            return
        client.subscribe(self.topic, qos=self.qos)
        self.log.info("Subscribed to %s", self.topic)

    def _on_disconnect(self, client: mqtt.Client, userdata: Any, rc: int) -> None:
        if rc != 0:
            self.log.warning("Unexpected MQTT disconnect rc=%s", rc)

    def _on_message(self, client: mqtt.Client, userdata: Any, message: mqtt.MQTTMessage) -> None:
        prefix, device, direction = self._parse_topic(message.topic)
        if not prefix or not device or direction != "out":
            return
        try:
            payload = json.loads(message.payload.decode("utf-8", errors="replace"))
        except Exception:
            self.log.debug("Non-JSON payload on %s", message.topic)
            return

        msg_type = payload.get("type")
        if msg_type == "start":
            self._handle_start(prefix, device)
        elif msg_type == "req" and payload.get("stg_list"):
            self._handle_stg_list(prefix, device, payload)

    # Message handlers ---------------------------------------------------
    def _handle_start(self, prefix: str, device: str) -> None:
        topic_in = f"{prefix}/{device}/in"
        result = self.client.publish(topic_in, START_REQUEST_PAYLOAD, qos=self.qos)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            self.log.info("Requested stg_list from %s", topic_in)
        else:
            self.log.error("Failed to publish stg_list request to %s rc=%s", topic_in, result.rc)

    def _handle_stg_list(self, prefix: str, device: str, payload: Dict[str, Any]) -> None:
        stg_ids = self._normalize_ids(payload.get("stg_list"))
        if not stg_ids:
            self.log.info("Empty stg_list for device %s", device)
            return
        try:
            self._sync_settings(prefix, device, stg_ids)
        except Exception as exc:
            self.log.exception("Failed to sync stg_list for %s: %s", device, exc)

    # Domain logic -------------------------------------------------------
    def _sync_settings(self, prefix: str, device: str, stg_ids: Sequence[int]) -> None:
        with self.db.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT d.id, d.firmware, dt.signature
                    FROM devices d
                    LEFT JOIN device_type dt ON dt.id = d.device_type_id
                    WHERE d.device_id = %s
                    LIMIT 1
                    """,
                    (device,),
                )
                row = cur.fetchone()
                if not row:
                    self.log.warning("Device %s not found in database", device)
                    return
                device_pk, firmware, signature = row
                signature = (signature or prefix or "").strip()
                if not signature:
                    self.log.warning("Cannot determine signature for device %s", device)
                    return
                if firmware is None:
                    self.log.warning("Device %s has no firmware value", device)
                    return

                setting_type_id = self._upsert_setting_type(cur, signature, firmware)
                available = self._existing_settings(cur, stg_ids)
                missing = sorted(set(stg_ids) - set(available))
                if missing:
                    self.log.warning("Missing settings for %s: %s", device, ",".join(map(str, missing)))
                if not available:
                    return

                self._sync_links(cur, setting_type_id, available)
                self.log.info(
                    "Synced %d settings for device %s (type_id=%s)",
                    len(available),
                    device,
                    setting_type_id,
                )

    def _upsert_setting_type(self, cur, signature: str, firmware: int) -> int:
        code = f"{signature}_{firmware}"
        name = f"{signature.upper()} firmware {firmware}"
        cur.execute(
            """
            INSERT INTO setting_types (code, device_type_signature, firmware, name_bg, name_en)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (code) DO UPDATE
                SET device_type_signature = EXCLUDED.device_type_signature,
                    firmware = EXCLUDED.firmware
            RETURNING id
            """,
            (code, signature, firmware, name, name),
        )
        setting_type_id = cur.fetchone()[0]
        return setting_type_id

    def _existing_settings(self, cur, stg_ids: Sequence[int]) -> List[int]:
        cur.execute(
            "SELECT id FROM settings WHERE id = ANY(%s)",
            (list(stg_ids),),
        )
        return [row[0] for row in cur.fetchall()]

    def _sync_links(self, cur, setting_type_id: int, setting_ids: Sequence[int]) -> None:
        cur.execute(
            "SELECT setting_id FROM setting_type_settings WHERE type_id = %s",
            (setting_type_id,),
        )
        existing = {row[0] for row in cur.fetchall()}
        desired = set(setting_ids)

        to_remove = sorted(existing - desired)
        if to_remove:
            cur.execute(
                "DELETE FROM setting_type_settings WHERE type_id = %s AND setting_id = ANY(%s)",
                (setting_type_id, to_remove),
            )

        to_add = sorted(desired - existing)
        if to_add:
            execute_values(
                cur,
                """
                INSERT INTO setting_type_settings (type_id, setting_id)
                VALUES %s
                ON CONFLICT DO NOTHING
                """,
                [(setting_type_id, sid) for sid in to_add],
            )

    # Utilities ----------------------------------------------------------
    @staticmethod
    def _parse_topic(topic: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        parts = topic.split("/")
        if len(parts) >= 3:
            return parts[0], parts[1], parts[2]
        return None, None, None

    @staticmethod
    def _normalize_ids(raw: Any) -> List[int]:
        ids: List[int] = []
        if not isinstance(raw, Iterable):
            return ids
        for item in raw:
            try:
                ids.append(int(item))
            except (TypeError, ValueError):
                continue
        ids.sort()
        return ids


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def main() -> int:
    setup_logging()
    service = SettingsSyncService()

    def handle_signal(signum, frame):  # type: ignore[unused-argument]
        service.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    service.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
