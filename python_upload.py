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

Списъкът поддържа два формата на ред:
  1) само локален път (относителен или абсолютен)
     пример: reports/2025/10/sales.csv
     => ще качи под същия относителен път в --remote-dir

  2) локален път -> отдалечен относителен път
     пример: out/report.pdf -> clientA/2025/report.pdf
     => ще качи като --remote-dir/clientA/2025/report.pdf
"""

import argparse
import os
import ssl
import sys
from ftplib import FTP, FTP_TLS, error_perm
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple, Optional


# === Цветове за по-добра визуализация в терминала ===
class Color:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    RESET = "\033[0m"


def colorize(text, color):
    """Връща текст с цвят (ако терминалът поддържа ANSI)."""
    if sys.stdout.isatty():
        return f"{color}{text}{Color.RESET}"
    return text


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Качване на файлове по FTP/FTPS от списък.")
    p.add_argument("--server", default="1.8.1.8", help="FTP сървър (host/IP)")
    p.add_argument("--port", type=int, default=21, help="FTP порт (21 за explicit TLS)")
    p.add_argument("--user", default="admin", help="FTP потребител")
    p.add_argument("--password", default="admin_pass", help="FTP парола")
    p.add_argument("--remote-dir", default="", help="Отдалечена базова директория (root по подразбиране)")
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


def parse_mapping(entry: str) -> Tuple[str, Optional[str]]:
    """
    Връща (local_path_str, remote_rel_str|None).
    Ако редът съдържа " -> ", приема се мапинг: локален -> отдалечен относителен път.
    Иначе remote_rel е None и ще се ползва локалният относителен път като отдалечен.
    """
    arrow = " -> "
    if arrow in entry:
        left, right = entry.split(arrow, 1)
        return left.strip(), right.strip()
    return entry, None


def join_remote(base: str, rel: str) -> str:
    if not base:
        return rel.lstrip("/")
    return f"{base.rstrip('/')}/{rel.lstrip('/')}"


def ensure_remote_dirs(ftp: FTP, remote_path: str) -> None:
    """
    Създава рекурсивно отдалечените директории за дадения remote_path (ако липсват).
    Не сменя окончателно работната директория.
    """
    # Разделяме на директория и файл
    remote_dir = remote_path.replace("\\", "/")
    if "/" in remote_dir:
        remote_dir = remote_dir.rsplit("/", 1)[0]
    else:
        return  # няма директория за създаване

    if not remote_dir:
        return

    # Запомняме текущата cwd
    try:
        cur = ftp.pwd()
    except Exception:
        cur = None

    # Ходим по компонентите
    parts = [p for p in remote_dir.split("/") if p and p != "."]
    for i, part in enumerate(parts):
        try:
            ftp.cwd(part)
        except error_perm:
            # опит за MKD, после cwd
            try:
                ftp.mkd(part)
            except error_perm:
                # възможно е вече да съществува или да няма права
                pass
            ftp.cwd(part)

    # Връщаме се обратно
    if cur is not None:
        ftp.cwd(cur)


def remote_timestamp_utc(ftp: FTP, remote_path: str) -> float:
    """
    Връща последна модификация на отдалечен файл като UNIX timestamp (UTC).
    Работи и когато remote_path е в поддиректория (чрез временен cwd).
    Хвърля error_perm ако файлът липсва или MDTM не е наличен.
    """
    remote_path = remote_path.replace("\\", "/")
    dirpart, name = (remote_path.rsplit("/", 1) + [""])[:2] if "/" in remote_path else ("", remote_path)

    cur = ftp.pwd()
    try:
        if dirpart:
            ftp.cwd(dirpart)
        resp = ftp.sendcmd(f"MDTM {name}")
        parts = resp.split()
        if len(parts) < 2:
            raise error_perm(f"Bad MDTM response: {resp}")
        ts_str = parts[1]
        # RFC 3659 MDTM в UTC: YYYYMMDDHHMMSS[.sss]
        ts_str = ts_str.split(".")[0]
        dt = datetime.strptime(ts_str, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        return dt.timestamp()
    finally:
        try:
            ftp.cwd(cur)
        except Exception:
            pass


def ensure_cwd(ftp: FTP, remote_dir: str) -> None:
    if not remote_dir:
        return
    try:
        ftp.cwd(remote_dir)
    except error_perm:
        # Ако базовата директория я няма – опит за създаване по веригата.
        parts = [p for p in remote_dir.replace("\\", "/").split("/") if p]
        cur = ftp.pwd()
        try:
            for part in parts:
                try:
                    ftp.cwd(part)
                except error_perm:
                    try:
                        ftp.mkd(part)
                    except error_perm:
                        pass
                    ftp.cwd(part)
        finally:
            ftp.cwd(cur)


def connect_ftp(args) -> FTP:
    if args.tls:
        # Explicit FTPS (AUTH TLS)
        context = ssl.create_default_context()
        if args.insecure:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        ftp = FTP_TLS(context=context, timeout=args.timeout)
        ftp.connect(host=args.server, port=args.port, timeout=args.timeout)
        # Уверяваме се за UTF-8
        ftp.encoding = "utf-8"
        ftp.auth()         # upgrade control connection
        ftp.login(user=args.user, passwd=args.password)
        try:
            ftp.sendcmd("OPTS UTF8 ON")
        except Exception:
            pass
        ftp.prot_p()       # secure data channel
    else:
        ftp = FTP(timeout=args.timeout)
        ftp.connect(host=args.server, port=args.port, timeout=args.timeout)
        # Уверяваме се за UTF-8
        ftp.encoding = "utf-8"
        ftp.login(user=args.user, passwd=args.password)
        try:
            ftp.sendcmd("OPTS UTF8 ON")
        except Exception:
            pass

    if args.passive:
        ftp.set_pasv(True)
    return ftp


def main() -> None:
    args = parse_args()

    entries = read_list(args.filelist)
    if not entries:
        print("Списъкът за качване е празен. Нищо за правене.")
        return

    ftp = connect_ftp(args)
    # ако има базова отдалечена директория – увери се, че съществува
    ensure_cwd(ftp, args.remote_dir)

    total = 0
    uploaded = 0
    skipped = 0
    failed = 0

    print()
    print("📤  Започвам качването...")
    print("=" * 90)
    print(f"{'ФАЙЛ':60} | {'РАЗМЕР':>10} | {'ДЕЙСТВИЕ'}")
    print("-" * 90)

    for entry in entries:
        total += 1
        local_str, remote_rel_override = parse_mapping(entry)

        # Локален път (приемаме, че е каквото е изредено – може да е относителен)
        local_path = Path(local_str).expanduser().resolve()

        if not local_path.exists() or not local_path.is_file():
            print(colorize(f"{local_str:60} | {'-':>10} | ❌ Пропуснат (не съществува файл)", Color.RED))
            failed += 1
            continue

        # Отдалечен относителен път:
        # - ако има мапинг „->“, ползваме дясната страна
        # - иначе запазваме относителната структура от списъка
        if remote_rel_override:
            remote_rel = remote_rel_override.replace("\\", "/")
        else:
            # използваме това, което е написано в списъка (без да режем базовото име)
            # ако локалният ред е даден абсолютен, ще вземем относително спрямо cwd
            # за да запазим структурата, взимаме оригиналния текст от списъка:
            original_rel = local_str.replace("\\", "/")
            # ако е абсолютен, го свеждаме до относителен спрямо текущата директория
            if os.path.isabs(original_rel):
                try:
                    original_rel = os.path.relpath(original_rel, os.getcwd()).replace("\\", "/")
                except Exception:
                    # fallback: само базовото име
                    original_rel = Path(original_rel).name
            remote_rel = original_rel

        remote_path = join_remote(args.remote_dir, remote_rel)

        local_mtime = os.path.getmtime(local_path)
        size_bytes = os.path.getsize(local_path)

        # Решение дали да качим
        if args.force:
            action = "UPLOAD (force)"
        else:
            try:
                r_mtime = remote_timestamp_utc(ftp, remote_path)
                action = "UPLOAD (local is newer)" if local_mtime > r_mtime else "SKIP (remote up-to-date/newer)"
            except error_perm:
                action = "UPLOAD (remote missing)"

        # Подобрен изход:
        if "UPLOAD" in action:
            print(colorize(f"{remote_rel:60} | {size_bytes:10,d} | ⬆️  {action}", Color.CYAN))
            if not args.dry_run:
                try:
                    ensure_remote_dirs(ftp, remote_path)
                    with open(local_path, "rb") as fh:
                        # storbinary работи с пълен (относителен спрямо cwd) път
                        ftp.storbinary(f"STOR {remote_path}", fh)
                    uploaded += 1
                    print(colorize(f"{'':60} | {'':10} | ✅ Качен успешно", Color.GREEN))
                except Exception as e:
                    failed += 1
                    print(colorize(f"{'':60} | {'':10} | ❌ Грешка при качване: {e}", Color.RED))
            else:
                print(colorize(f"{'':60} | {'':10} | 🧪 Dry-run (няма качване)", Color.YELLOW))
        else:
            print(colorize(f"{remote_rel:60} | {size_bytes:10,d} | ⏩ {action}", Color.YELLOW))
            skipped += 1

    ftp.quit()
    print("=" * 90)
    print()
    print("📊  Резюме:")
    print(f"  Общо файлове:   {total}")
    print(f"  ✅ Качени:       {uploaded}")
    print(f"  ⏩ Пропуснати:   {skipped}")
    print(f"  ❌ Грешки:       {failed}")
    print()
    print("Готово.")


if __name__ == "__main__":
    main()
