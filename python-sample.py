#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Settings Sync Service (MQTT → SQLite3)

Цели:
- Минимални зависимости (само paho-mqtt)
- Стабилен запис в SQLite (WAL, busy_timeout, транзакции)
- Ясна схема: devices, settings, setting_types, setting_type_settings
- Обработка на MQTT:
    * type=start → изисква stg_list (публикува {"type":"req","req":"stg_list"} към <prefix>/<device>/in)
    * type=req, req=stg_list → синхронизира към БД
- Периодична задача: на всеки N секунди заявява stg_list за всички известни устройства
- Сигурно спиране (SIGINT/SIGTERM)

Инсталация:
    python3 -m venv .venv && . .venv/bin/activate
    pip install -r requirements.txt

Стартиране (пример):
    export MQTT_HOST=127.0.0.1
    export MQTT_PORT=1883
    export MQTT_TOPIC="+/+/out"
    export SQLITE_PATH="./iot_settings.db"
    export RESYNC_INTERVAL_SEC=300
    python mqtt_settings_sync_sqlite.py --log-level=DEBUG
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import signal
import sqlite3
import sys
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple

import paho.mqtt.client as mqtt


# -----------------------------
# Конфигурация
# -----------------------------

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass(frozen=True)
class MQTTConfig:
    host: str = "127.0.0.1"
    port: int = 1883
    username: str = ""
    password: str = ""
    client_id: str = "settings-sync-sqlite"
    topic: str = "+/+/out"
    qos: int = 1
    keepalive: int = 60
    reconnect_min: int = 1
    reconnect_max: int = 30

    def validate(self) -> None:
        if not (0 <= self.qos <= 2):
            raise ValueError("Invalid MQTT QoS (0..2)")
        parts = self.topic.split("/")
        if len(parts) < 3 or parts[-1] != "out":
            raise ValueError('MQTT topic must end with "out" and have at least 3 parts (e.g. "+/+/out")')


@dataclass(frozen=True)
class DBConfig:
    path: str = "./iot_settings.db"
    timeout_sec: int = 10          # sqlite busy timeout
    wal: bool = True               # включи WAL за по-добра конкурентност

    def validate(self) -> None:
        if not self.path:
            raise ValueError("SQLite path required")
        if self.timeout_sec < 1:
            raise ValueError("timeout_sec must be >= 1")


@dataclass(frozen=True)
class AppConfig:
    mqtt: MQTTConfig
    db: DBConfig
    log_level: LogLevel = LogLevel.INFO
    dry_run: bool = False
    resync_interval_sec: int = 300  # периодична заявка за всички устройства

    @staticmethod
    def from_env_and_args(argv: Optional[Sequence[str]] = None) -> "AppConfig":
        parser = argparse.ArgumentParser(description="Settings Sync (MQTT → SQLite3)")
        parser.add_argument("--mqtt-host", default=os.getenv("MQTT_HOST", "127.0.0.1"))
        parser.add_argument("--mqtt-port", type=int, default=int(os.getenv("MQTT_PORT", "1883")))
        parser.add_argument("--mqtt-username", default=os.getenv("MQTT_USERNAME", ""))
        parser.add_argument("--mqtt-password", default=os.getenv("MQTT_PASSWORD", ""))
        parser.add_argument("--mqtt-client-id", default=os.getenv("MQTT_CLIENT_ID", "settings-sync-sqlite"))
        parser.add_argument("--mqtt-topic", default=os.getenv("MQTT_TOPIC", "+/+/out"))
        parser.add_argument("--mqtt-qos", type=int, default=int(os.getenv("MQTT_QOS", "1")))
        parser.add_argument("--mqtt-keepalive", type=int, default=int(os.getenv("MQTT_KEEPALIVE", "60")))
        parser.add_argument("--mqtt-reconnect-min", type=int, default=int(os.getenv("MQTT_RECONNECT_MIN", "1")))
        parser.add_argument("--mqtt-reconnect-max", type=int, default=int(os.getenv("MQTT_RECONNECT_MAX", "30")))

        parser.add_argument("--sqlite-path", default=os.getenv("SQLITE_PATH", "./iot_settings.db"))
        parser.add_argument("--sqlite-timeout-sec", type=int, default=int(os.getenv("SQLITE_TIMEOUT_SEC", "10")))
        parser.add_argument("--sqlite-wal", action="store_true", default=os.getenv("SQLITE_WAL", "true").lower() in ("1", "true", "yes"))

        parser.add_argument("--resync-interval-sec", type=int, default=int(os.getenv("RESYNC_INTERVAL_SEC", "300")))
        parser.add_argument("--dry-run", action="store_true", default=os.getenv("DRY_RUN", "false").lower() in ("1", "true", "yes"))
        parser.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"))
        args = parser.parse_args(argv)

        mqtt = MQTTConfig(
            host=args.mqtt_host,
            port=args.mqtt_port,
            username=args.mqtt_username,
            password=args.mqtt_password,
            client_id=args.mqtt_client_id,
            topic=args.mqtt_topic,
            qos=args.mqtt_qos,
            keepalive=args.mqtt_keepalive,
            reconnect_min=args.mqtt_reconnect_min,
            reconnect_max=args.mqtt_reconnect_max,
        )
        db = DBConfig(
            path=args.sqlite_path,
            timeout_sec=args.sqlite_timeout_sec,
            wal=bool(args.sqlite_wal),
        )
        level_str = (args.log_level or "INFO").upper()
        level = LogLevel[level_str] if level_str in LogLevel.__members__ else LogLevel.INFO

        cfg = AppConfig(
            mqtt=mqtt,
            db=db,
            log_level=level,
            dry_run=bool(args.dry_run),
            resync_interval_sec=max(10, int(args.resync_interval_sec)),
        )
        mqtt.validate(); db.validate()
        return cfg


# -----------------------------
# Логване / помощни
# -----------------------------

def setup_logging(level: LogLevel) -> None:
    logging.basicConfig(
        level=level.value,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())


def anonymize_device_id(device_id: str) -> str:
    return f"device-{hashlib.sha256(device_id.encode('utf-8')).hexdigest()[:8]}"


def parse_topic(topic: str) -> Optional[Tuple[str, str, str]]:
    parts = topic.split("/")
    if len(parts) < 3 or parts[-1] != "out":
        return None
    return parts[0], parts[1], parts[-1]


def parse_payload(payload: bytes) -> Optional[Dict[str, Any]]:
    try:
        t = payload.decode("utf-8").strip()
        if not t:
            return None
        data = json.loads(t)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


# -----------------------------
# SQLite Мениджър
# -----------------------------

class SQLiteManager:
    """
    Мениджър за SQLite с:
    - WAL (по избор)
    - busy_timeout
    - транзакции (context manager)
    - schema bootstrap (idempotent)
    """

    def __init__(self, path: str, timeout_sec: int = 10, wal: bool = True, dry_run: bool = False) -> None:
        self.path = path
        self.timeout = timeout_sec
        self.wal = wal
        self.dry_run = dry_run
        self.log = logging.getLogger("sqlite")
        self._bootstrap()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=self.timeout, isolation_level=None, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        # pragma
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys = ON")
        cur.execute(f"PRAGMA busy_timeout = {self.timeout * 1000}")
        if self.wal:
            # WAL е по-добър за конкурентен достъп
            cur.execute("PRAGMA journal_mode = WAL")
        cur.close()
        return conn

    def _bootstrap(self) -> None:
        with self.transaction() as cur:
            # базова схема (минимална)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL UNIQUE,
                    last_prefix TEXT,
                    firmware INTEGER,
                    device_type_signature TEXT,
                    seen_at TEXT NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY,
                    name TEXT
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS setting_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL UNIQUE,
                    device_type_signature TEXT,
                    firmware INTEGER,
                    name_bg TEXT,
                    name_en TEXT,
                    updated_at TEXT NOT NULL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS setting_type_settings (
                    type_id INTEGER NOT NULL,
                    setting_id INTEGER NOT NULL,
                    PRIMARY KEY (type_id, setting_id),
                    FOREIGN KEY (type_id) REFERENCES setting_types(id) ON DELETE CASCADE,
                    FOREIGN KEY (setting_id) REFERENCES settings(id) ON DELETE CASCADE
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_devices_device_id ON devices(device_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_sts_type_id ON setting_type_settings(type_id)")
        self.log.info("SQLite schema ensured at %s", os.path.abspath(self.path))

    # --- транзакции

    def transaction(self):
        """
        Контекст-мениджър за транзакция (BEGIN IMMEDIATE → COMMIT/ROLLBACK).
        """
        conn = self._connect()
        cur = conn.cursor()
        try:
            cur.execute("BEGIN IMMEDIATE")
            yield cur
            if self.dry_run:
                conn.rollback()
            else:
                conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    # --- домейн операции

    def upsert_device_seen(self, device_id: str, prefix: str) -> None:
        with self.transaction() as cur:
            cur.execute(
                "INSERT INTO devices(device_id, last_prefix, seen_at) VALUES (?, ?, ?) "
                "ON CONFLICT(device_id) DO UPDATE SET last_prefix=excluded.last_prefix, seen_at=excluded.seen_at",
                (device_id, prefix, now_iso()),
            )

    def get_device(self, device_id: str) -> Optional[sqlite3.Row]:
        with self.transaction() as cur:
            cur.execute("SELECT * FROM devices WHERE device_id=?", (device_id,))
            row = cur.fetchone()
            return row

    def update_device_fw_sig(self, device_id: str, firmware: Optional[int], signature: Optional[str]) -> None:
        with self.transaction() as cur:
            cur.execute(
                "UPDATE devices SET firmware = COALESCE(?, firmware), device_type_signature = COALESCE(?, device_type_signature) WHERE device_id=?",
                (firmware, signature, device_id),
            )

    def upsert_setting_type(self, signature: str, firmware: int) -> int:
        code = f"{(signature or '').strip()}_{int(firmware or 0)}"
        name = f"{(signature or '').upper()} firmware {int(firmware or 0)}"
        with self.transaction() as cur:
            cur.execute(
                "INSERT INTO setting_types(code, device_type_signature, firmware, name_bg, name_en, updated_at) "
                "VALUES(?,?,?,?,?,?) "
                "ON CONFLICT(code) DO UPDATE SET device_type_signature=excluded.device_type_signature, "
                "firmware=excluded.firmware, updated_at=excluded.updated_at",
                (code, signature or "", int(firmware or 0), name, name, now_iso()),
            )
            # вземи id
            cur.execute("SELECT id FROM setting_types WHERE code=?", (code,))
            rid = cur.fetchone()["id"]
            return int(rid)

    def fetch_existing_settings(self, ids: Sequence[int]) -> List[int]:
        if not ids:
            return []
        placeholders = ",".join("?" for _ in ids)
        q = f"SELECT id FROM settings WHERE id IN ({placeholders})"
        with self.transaction() as cur:
            cur.execute(q, list(ids))
            return [int(r["id"]) for r in cur.fetchall()]

    def get_current_links(self, setting_type_id: int) -> List[int]:
        with self.transaction() as cur:
            cur.execute("SELECT setting_id FROM setting_type_settings WHERE type_id=?", (setting_type_id,))
            return [int(r["setting_id"]) for r in cur.fetchall()]

    def delete_links(self, setting_type_id: int, to_remove: Sequence[int]) -> int:
        if not to_remove:
            return 0
        placeholders = ",".join("?" for _ in to_remove)
        q = f"DELETE FROM setting_type_settings WHERE type_id=? AND setting_id IN ({placeholders})"
        with self.transaction() as cur:
            cur.execute(q, (setting_type_id, *list(to_remove)))
            return cur.rowcount or 0

    def insert_links(self, setting_type_id: int, to_add: Sequence[int]) -> int:
        rows = [(setting_type_id, sid) for sid in set(to_add)]
        if not rows:
            return 0
        with self.transaction() as cur:
            cur.executemany("INSERT OR IGNORE INTO setting_type_settings(type_id, setting_id) VALUES(?,?)", rows)
            return cur.rowcount or 0

    def list_all_devices(self) -> List[sqlite3.Row]:
        with self.transaction() as cur:
            cur.execute("SELECT device_id, COALESCE(last_prefix,'') AS last_prefix FROM devices ORDER BY device_id")
            return cur.fetchall()


# -----------------------------
# Синк логика
# -----------------------------

class SettingsSync:
    def __init__(self, db: SQLiteManager) -> None:
        self.db = db
        self.log = logging.getLogger("sync")
        self.metrics = {"processed": 0, "missing": 0, "errors": 0}

    @staticmethod
    def normalize_ids(raw: Any) -> List[int]:
        if not isinstance(raw, list):
            return []
        out: List[int] = []
        for x in raw:
            try:
                v = int(x)
                if v > 0:
                    out.append(v)
            except Exception:
                continue
        return sorted(set(out))

    def process_stg_list(self, device_id: str, prefix: str, raw_ids: Any, firmware: Optional[int] = None, signature: Optional[str] = None) -> Dict[str, Any]:
        t0 = time.time()
        res = {"device": anonymize_device_id(device_id), "processed": 0, "missing": 0, "added": 0, "removed": 0, "ok": False, "ms": 0}
        try:
            ids = self.normalize_ids(raw_ids)
            # запомни последен prefix + seen_at
            self.db.upsert_device_seen(device_id, prefix)
            # обнови известни firmware/signature, ако са подадени в payload-a
            if firmware is not None or signature is not None:
                self.db.update_device_fw_sig(device_id, firmware, signature)

            # ако нямаме локално firmware/signature, вземи от devices реда
            dev = self.db.get_device(device_id)
            sig = (signature if signature is not None else (dev["device_type_signature"] if dev else "")) or ""
            fw = int(firmware if firmware is not None else (dev["firmware"] if dev and dev["firmware"] is not None else 0))

            if not ids:
                res["ok"] = True
                res["ms"] = int((time.time() - t0) * 1000)
                return res

            st_id = self.db.upsert_setting_type(sig, fw)
            existing = set(self.db.fetch_existing_settings(ids))
            missing = set(ids) - existing
            current = set(self.db.get_current_links(st_id))

            added = self.db.insert_links(st_id, existing - current)
            removed = self.db.delete_links(st_id, current - existing)

            res.update(
                processed=len(existing),
                missing=len(missing),
                added=added,
                removed=removed,
                ok=True,
                ms=int((time.time() - t0) * 1000),
            )
            self.metrics["processed"] += res["processed"]
            self.metrics["missing"] += res["missing"]
            if missing:
                self.log.debug("Missing settings for %s: %s", res["device"], sorted(missing))
            self.log.info("Sync %s processed=%d missing=%d add=%d del=%d",
                          res["device"], res["processed"], res["missing"], res["added"], res["removed"])
            return res
        except Exception:
            self.metrics["errors"] += 1
            logging.getLogger("sync").exception("process_stg_list error for %s", device_id)
            return res


# -----------------------------
# MQTT
# -----------------------------

class MQTTService:
    def __init__(self, cfg: MQTTConfig, sync: SettingsSync) -> None:
        self.cfg = cfg
        self.sync = sync
        self.log = logging.getLogger("mqtt")

        self.client = mqtt.Client(client_id=self.cfg.client_id, protocol=mqtt.MQTTv311, clean_session=True)
        if self.cfg.username:
            self.client.username_pw_set(self.cfg.username, self.cfg.password)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_log = self._on_log
        self.client.reconnect_delay_set(self.cfg.reconnect_min, self.cfg.reconnect_max)

        self._req_stg_list_payload = json.dumps({"type": "req", "req": "stg_list"}, separators=(",", ":"))
        self._connected = False

    def start(self) -> None:
        self.log.info("Connecting MQTT %s:%d ...", self.cfg.host, self.cfg.port)
        self.client.connect(self.cfg.host, self.cfg.port, keepalive=self.cfg.keepalive)
        self.client.loop_start()

    def stop(self) -> None:
        try:
            self.client.loop_stop()
        finally:
            try:
                self.client.disconnect()
            except Exception:
                pass

    def is_connected(self) -> bool:
        return self._connected

    # --- callbacks

    def _on_connect(self, client: mqtt.Client, userdata: Any, flags: Dict[str, Any], rc: int) -> None:
        self._connected = (rc == 0)
        if self._connected:
            self.log.info("MQTT connected, subscribe %s (qos=%d)", self.cfg.topic, self.cfg.qos)
            client.subscribe(self.cfg.topic, qos=self.cfg.qos)
        else:
            self.log.error("MQTT connect failed rc=%d", rc)

    def _on_disconnect(self, client: mqtt.Client, userdata: Any, rc: int) -> None:
        self._connected = False
        if rc != 0:
            self.log.warning("MQTT unexpected disconnect rc=%d", rc)
        else:
            self.log.info("MQTT disconnected")

    def _on_log(self, client: mqtt.Client, userdata: Any, level: int, buf: str) -> None:
        if level == mqtt.MQTT_LOG_ERR:
            self.log.error("MQTT: %s", buf)
        elif level == mqtt.MQTT_LOG_WARNING:
            self.log.warning("MQTT: %s", buf)
        else:
            logging.getLogger("mqtt.trace").debug(buf)

    def _on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        try:
            parsed = parse_topic(msg.topic)
            if not parsed:
                return
            prefix, device, _ = parsed
            data = parse_payload(msg.payload)
            if not data:
                return

            # отбележи, че сме видели устройство
            # (ще запишем seen_at и последен prefix)
            self.sync.db.upsert_device_seen(device, prefix)

            mtype = str(data.get("type") or "")
            if mtype == "start":
                # изискваме списък настройки от устройството
                in_topic = f"{prefix}/{device}/in"
                r = client.publish(in_topic, self._req_stg_list_payload, qos=self.cfg.qos)
                if r.rc == mqtt.MQTT_ERR_SUCCESS:
                    self.log.info("Requested stg_list from %s", anonymize_device_id(device))
                else:
                    self.log.error("Publish error rc=%s to %s", r.rc, in_topic)
                return

            if mtype == "req" and str(data.get("req") or "") == "stg_list":
                # опитваме да извадим firmware/signature ако ги връща устройството
                firmware = None
                signature = None
                if isinstance(data.get("firmware"), int):
                    firmware = int(data.get("firmware"))
                if isinstance(data.get("signature"), str):
                    signature = str(data.get("signature"))

                res = self.sync.process_stg_list(device, prefix, data.get("stg_list", []), firmware, signature)
                if not res.get("ok"):
                    self.log.error("Sync failed for %s", res.get("device"))
                return
        except Exception:
            self.log.exception("on_message error for topic=%s", msg.topic)

    # --- helpers

    def request_stg_list(self, prefix: str, device: str) -> bool:
        in_topic = f"{prefix}/{device}/in"
        r = self.client.publish(in_topic, self._req_stg_list_payload, qos=self.cfg.qos)
        ok = (r.rc == mqtt.MQTT_ERR_SUCCESS)
        if ok:
            self.log.debug("Periodic request stg_list → %s", in_topic)
        else:
            self.log.warning("Periodic publish failed rc=%s → %s", r.rc, in_topic)
        return ok


# -----------------------------
# Периодична задача
# -----------------------------

class PeriodicRequester(threading.Thread):
    """
    На всеки interval_sec заявява stg_list към всички известни устройства.
    """
    daemon = True

    def __init__(self, db: SQLiteManager, mqtt: MQTTService, interval_sec: int) -> None:
        super().__init__(name="periodic-requester")
        self.db = db
        self.mqtt = mqtt
        self.interval = max(10, int(interval_sec))
        self._stop = threading.Event()
        self.log = logging.getLogger("periodic")

    def stop(self) -> None:
        self._stop.set()

    def run(self) -> None:
        self.log.info("Periodic requester started (interval=%ds)", self.interval)
        # първо леко отлагане за да се върже MQTT
        time.sleep(2.0)
        while not self._stop.is_set():
            try:
                if self.mqtt.is_connected():
                    devices = self.db.list_all_devices()
                    for row in devices:
                        device = row["device_id"]
                        prefix = row["last_prefix"] or ""
                        if not prefix:
                            continue
                        self.mqtt.request_stg_list(prefix, device)
                else:
                    self.log.debug("MQTT not connected yet")
            except Exception:
                self.log.exception("Periodic requester error")
            finally:
                self._stop.wait(self.interval)
        self.log.info("Periodic requester stopped")


# -----------------------------
# Приложение
# -----------------------------

class App:
    def __init__(self, cfg: AppConfig) -> None:
        self.cfg = cfg
        self.log = logging.getLogger("app")

        self.db = SQLiteManager(cfg.db.path, cfg.db.timeout_sec, cfg.db.wal, cfg.dry_run)
        self.sync = SettingsSync(self.db)
        self.mqtt = MQTTService(cfg.mqtt, self.sync)
        self.periodic = PeriodicRequester(self.db, self.mqtt, cfg.resync_interval_sec)

        self._stop_event = threading.Event()

    def start(self) -> None:
        self._install_signals()
        self.mqtt.start()
        self.periodic.start()
        try:
            while not self._stop_event.is_set():
                time.sleep(0.5)
        finally:
            self.stop()

    def stop(self) -> None:
        self.log.info("Stopping ...")
        try:
            self.periodic.stop()
            self.periodic.join(timeout=3.0)
        except Exception:
            pass
        try:
            self.mqtt.stop()
        except Exception:
            pass
        self.log.info("Stopped")

    def _install_signals(self) -> None:
        def handle(sig, _frame):
            self.log.info("Signal %s → shutdown", sig)
            self._stop_event.set()
        signal.signal(signal.SIGINT, handle)
        signal.signal(signal.SIGTERM, handle)


# -----------------------------
# main
# -----------------------------

def main(argv: Optional[Sequence[str]] = None) -> int:
    cfg = AppConfig.from_env_and_args(argv)
    setup_logging(cfg.log_level)
    # подробен MQTT trace само при DEBUG
    logging.getLogger("mqtt.trace").setLevel(logging.DEBUG if cfg.log_level == LogLevel.DEBUG else logging.WARNING)

    app = App(cfg)
    try:
        app.start()
        return 0
    except KeyboardInterrupt:
        logging.getLogger("app").info("Keyboard interrupt")
        return 0
    except Exception as exc:
        logging.getLogger("app").exception("Fatal: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
