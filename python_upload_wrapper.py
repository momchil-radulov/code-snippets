#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
upload_wrapper.py
------------------
Python обвивка за uploader.py:
 - пуска dry-run
 - пита за потвърждение
 - после качва реално
 - поддържа .env / профили / CLI аргументи
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from dotenv import load_dotenv  # pip install python-dotenv

# === Настройки по подразбиране ===
DEFAULTS = {
    "SERVER": "192.168.1.10",
    "PORT": "21",
    "USER": "admin",
    "PASSWORD": "secret",
    "REMOTE_DIR": "",
    "FILELIST": "files2upload.txt",
    "TIMEOUT": "30",
    "TLS": "false",
    "INSECURE": "false",
    "PASSIVE": "false",
    "FORCE": "false",
}

# === Утилити ===
def str2bool(v: str) -> bool:
    return v.lower() in ("1", "true", "yes", "y", "on")


def color(txt, c):
    COLORS = {
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "blue": "\033[94m",
        "dim": "\033[2m",
        "reset": "\033[0m",
    }
    return f"{COLORS.get(c, '')}{txt}{COLORS['reset']}"


# === Аргументи ===
p = argparse.ArgumentParser(description="Python wrapper за uploader.py с dry-run и потвърждение.")
p.add_argument("--server", default=None)
p.add_argument("--port", default=None)
p.add_argument("--user", default=None)
p.add_argument("--password", default=None)
p.add_argument("--remote-dir", default=None)
p.add_argument("--filelist", default=None)
p.add_argument("--timeout", default=None)
p.add_argument("--tls", action="store_true")
p.add_argument("--insecure", action="store_true")
p.add_argument("--passive", action="store_true")
p.add_argument("--force", action="store_true")
p.add_argument("--no-confirm", action="store_true")
p.add_argument("--profile", help="име на профил от ./profiles/PROFILE.env")
p.add_argument("--python", default="python3", help="команда за Python (default: python3)")
args = p.parse_args()

# === Зареждане на .env ===
base_dir = Path(__file__).resolve().parent
dotenv_path = base_dir / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)

# === Зареждане на профил, ако има ===
if args.profile:
    prof = base_dir / "profiles" / f"{args.profile}.env"
    if not prof.exists():
        sys.exit(color(f"Профилът {prof} не е намерен!", "red"))
    load_dotenv(prof)
    print(color(f"Зареден профил: {args.profile}", "dim"))

# === Попълни параметрите ===
cfg = {}
for key, default in DEFAULTS.items():
    env_val = os.getenv(key)
    arg_val = getattr(args, key.lower(), None)
    cfg[key] = arg_val or env_val or default

# флагове
cfg["TLS"] = args.tls or str2bool(os.getenv("TLS", cfg["TLS"]))
cfg["INSECURE"] = args.insecure or str2bool(os.getenv("INSECURE", cfg["INSECURE"]))
cfg["PASSIVE"] = args.passive or str2bool(os.getenv("PASSIVE", cfg["PASSIVE"]))
cfg["FORCE"] = args.force or str2bool(os.getenv("FORCE", cfg["FORCE"]))
no_confirm = args.no_confirm or str2bool(os.getenv("NO_CONFIRM", "false"))

# === Проверки ===
uploader_py = os.getenv("UPLOADER_PY", str(base_dir / "uploader.py"))
if not Path(uploader_py).exists():
    sys.exit(color(f"Не е намерен uploader.py: {uploader_py}", "red"))

filelist = cfg["FILELIST"]
if not Path(filelist).exists():
    sys.exit(color(f"Липсва файл със списък: {filelist}", "red"))

# === Сглоби аргументите за uploader.py ===
cmd_base = [
    args.python, uploader_py,
    "--server", cfg["SERVER"],
    "--port", cfg["PORT"],
    "--user", cfg["USER"],
    "--password", cfg["PASSWORD"],
    "--filelist", cfg["FILELIST"],
    "--timeout", cfg["TIMEOUT"],
]
if cfg["REMOTE_DIR"]:
    cmd_base += ["--remote-dir", cfg["REMOTE_DIR"]]
if cfg["TLS"]:
    cmd_base += ["--tls"]
if cfg["INSECURE"]:
    cmd_base += ["--insecure"]
if cfg["PASSIVE"]:
    cmd_base += ["--passive"]
if cfg["FORCE"]:
    cmd_base += ["--force"]

# === 1️⃣ Dry-run ===
print(color("▶ Dry-run (без качване):", "yellow"))
dry_cmd = cmd_base + ["--dry-run"]
print(color(" ".join(dry_cmd), "dim"))
dry_rc = subprocess.call(dry_cmd)
if dry_rc != 0:
    sys.exit(color(f"Dry-run завърши с грешка ({dry_rc}).", "red"))

# === 2️⃣ Потвърждение ===
if not no_confirm:
    print()
    try:
        ans = input(color("Да кача ли реално? [y/N] ", "blue")).strip().lower()
    except EOFError:
        ans = "n"
    if ans not in ("y", "yes"):
        print(color("Отказано от потребителя.", "dim"))
        sys.exit(0)

# === 3️⃣ Реално качване ===
print(color("▶ Стартирам реално качване:", "green"))
rc = subprocess.call(cmd_base)
if rc != 0:
    sys.exit(color(f"Качването завърши с грешка ({rc}).", "red"))

print(color("Готово ✅", "green"))

# How to use #
exit(0)

pip install python-dotenv
chmod +x upload_wrapper.py

[profiles/prod.env]
SERVER=1.2.3.3 OR ftp.example.com
USER=user-name
PASSWORD=user-password
REMOTE_DIR=incoming/your-project-name
TLS=true
INSECURE=true
PASSIVE=true
/ [profiles/prod.env]

./upload_wrapper.py --profile prod
./upload_wrapper.py --server 192.168.1.10 --user admin --password secret
