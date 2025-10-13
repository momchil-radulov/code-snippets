#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Качване на файлове по FTP/FTPS от списък (files2upload.txt).

Опции:
  --dry-run      : само показва какво БИХ качил (без реално качване)
  --force        : качва винаги, независимо от времето
  --tls          : explicit FTPS (AUTH TLS на порт 21) + защитен data channel (PROT P)
  --insecure     : при --tls изключва проверката на сертификата (само ако знаеш какво правиш)
  --passive      : включва PASV режим
"""

import argparse
import os
import ssl
from ftplib import FTP, FTP_TLS, error_perm
from datetime import datetime, timezone
from pathlib import Path
from typing import List


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Качване на файлове по FTP/FTPS от списък.")
    p.add_argument("--server", default="1.8.1.8", help="FTP сървър (host/IP)")
    p.add_argument("--port", type=int, default=21, help="FTP порт (21 за explicit TLS)")
    p.add_argument("--user", default="admin", help="FTP потребител")
    p.add_argument("--password", default="admin_pass", help="FTP парола")
    p.add_argument("--remote-dir", default="", help="Отдалечена директория (root по подразбиране)")
    p.add_argument("--filelist", default="files2upload.txt", help="Файл със списък за качване")
    p.add_argument("--dry-run", action="store_true", help="Пробен режим: без реално качване")
    p.add_argument("--force", action="store_true", help="Качва независимо от времето")
    p.add_argument("--tls", action="store_true", help="Включи explicit FTPS (AUTH TLS)")
    p.add_argument("--insecure", action="store_true",
                   help="(С --tls) Не валидирай TLS сертификата (self-signed и т.н.)")
    p.add_argument("--passive", action="store_true", help="Изрично включи PASV режим (ако е нужно)")
    p.add_argument("--timeout", type=int, default=30, help="Timeout за FTP връзката (сек.)")
    return p.parse_args()


def read_list(path: str) -> List[str]:
    lines: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            s = raw.strip()
            if not s:
                continue
            if s.startswith("#!exit"):
                print("Намерена команда '#!exit' → прекратявам четенето на списъка.")
                break
            if s.startswith("#"):
                continue
            lines.append(s)
    return lines


def remote_timestamp_utc(ftp, remote_path: str) -> float:
    """
    Връща последна модификация на отдалечен файл като UNIX timestamp (UTC).
    Хвърля error_perm ако файлът липсва или MDTM не е наличен.
    """
    resp = ftp.sendcmd(f"MDTM {remote_path}")
    parts = resp.split()
    if len(parts) < 2 or not parts[1].isdigit():
        raise error_perm(f"Bad MDTM response: {resp}")
    dt = datetime.strptime(parts[1], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    return dt.timestamp()


def ensure_cwd(ftp, remote_dir: str) -> None:
    if not remote_dir:
        return
    try:
        ftp.cwd(remote_dir)
    except error_perm as e:
        print(f"Внимание: неуспешно влизане в директория '{remote_dir}': {e}")
        print("Продължавам от текущата директория на сървъра.")


def connect_ftp(args):
    if args.tls:
        # Explicit FTPS (AUTH TLS)
        context = ssl.create_default_context()
        if args.insecure:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        ftp = FTP_TLS(context=context, timeout=args.timeout)
        ftp.connect(host=args.server, port=args.port, timeout=args.timeout)
        ftp.auth()         # upgrade control connection
        ftp.login(user=args.user, passwd=args.password)
        ftp.prot_p()       # secure data channel
    else:
        ftp = FTP(timeout=args.timeout)
        ftp.connect(host=args.server, port=args.port, timeout=args.timeout)
        ftp.login(user=args.user, passwd=args.password)

    if args.passive:
        ftp.set_pasv(True)
    return ftp


def main() -> None:
    args = parse_args()

    files = read_list(args.filelist)
    if not files:
        print("Списъкът за качване е празен. Нищо за правене.")
        return

    ftp = connect_ftp(args)
    ensure_cwd(ftp, args.remote_dir)

    for entry in files:
        local_path = Path(entry).expanduser().resolve()
        remote_name = entry.replace("\\", "/").split("/")[-1]
        remote_path = remote_name if not args.remote_dir else f"{args.remote_dir.rstrip('/')}/{remote_name}"

        if not local_path.exists() or not local_path.is_file():
            print(f" ! Пропускам (не съществува файл): {local_path}")
            continue

        local_mtime = os.path.getmtime(local_path)
        size_bytes = os.path.getsize(local_path)

        if args.force:
            action = "UPLOAD (force)"
        else:
            try:
                r_mtime = remote_timestamp_utc(ftp, remote_path)
                action = "UPLOAD (local is newer)" if local_mtime > r_mtime else "SKIP (remote up-to-date/newer)"
            except error_perm:
                action = "UPLOAD (remote missing)"

        print(f"- {remote_name} [{size_bytes} B] → {action}")

        if "UPLOAD" in action and not args.dry_run:
            with open(local_path, "rb") as fh:
                ftp.storbinary(f"STOR {remote_path}", fh)
            print("  uploaded")
        elif args.dry_run:
            print("  not uploaded, dry-run")
        else:
            print("  not uploaded")

    ftp.quit()
    print("Готово.")


if __name__ == "__main__":
    main()

# How to use
## python3 uploader.py --tls --server 1.8.1.8 --user admin --password admin_pass  # с TLS 
## python3 uploader.py --tls --insecure                                           # с TLS и self-signed сертификат (не валидирай)
