#!/usr/bin/env python3
"""Подменя публичните сертификати след проверка и архивиране.

Изисква Python 3 и командата openssl, без допълнителни Python пакети.
С --check само проверява файловете, без да ги променя.
"""

import argparse
from datetime import datetime
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


# Директория на проекта, определена спрямо местоположението на скрипта.
PROJECT_DIR = Path(__file__).resolve().parent.parent

# Засега с предимство: текущата директория, от която е стартиран Python.
PROJECT_DIR = Path.cwd()

CERTIFICATES_DIR = PROJECT_DIR / "doc/sert"

# Всяка двойка е: (нов сертификат, място за поставяне).
CERTIFICATES = [
    (
        CERTIFICATES_DIR / "MPI/MPI-live.cer",
        PROJECT_DIR / "application/config/live/MPI-live.cer",
    ),
    (
        CERTIFICATES_DIR / "MPI/MPI-dev.cer",
        PROJECT_DIR / "application/config/live/MPI-dev.cer",
    ),
]


def read_certificate(path, *options):
    """Изпълнява OpenSSL и връща резултата като текст."""
    result = subprocess.run(
        ["openssl", "x509", "-in", str(path), "-noout", *options],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Неуспешна проверка на {path}: {details}")
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true", help="Само проверка, без подмяна."
    )
    args = parser.parse_args()

    if shutil.which("openssl") is None:
        raise RuntimeError("Не е намерена командата openssl.")

    # 1. Проверяваме и двете двойки, преди да променим който и да е файл.
    for source, target in CERTIFICATES:
        read_certificate(source, "-checkend", "0")
        new_key = read_certificate(source, "-pubkey")
        old_key = read_certificate(target, "-pubkey")
        if new_key != old_key:
            raise RuntimeError(f"Публичните ключове не съвпадат: {target}")
        print(f"OK: {target.relative_to(PROJECT_DIR)}")

    if args.check:
        print("Проверката е успешна. Няма променени файлове.")
        return

    # 2. Архивираме старите сертификати в отделна, уникална директория.
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = Path(tempfile.mkdtemp(
        prefix=f"backup-{timestamp}-", dir=CERTIFICATES_DIR
    ))
    for source, target in CERTIFICATES:
        shutil.copy2(target, backup_dir / target.name)
    print(f"Архив: {backup_dir}")

    # 3. Копираме новите сертификати, запазвайки правата на целевите файлове.
    for source, target in CERTIFICATES:
        shutil.copyfile(source, target)
        if source.read_bytes() != target.read_bytes():
            raise RuntimeError(f"Копирането не е потвърдено: {target}")
        print(f"Подменен: {target.relative_to(PROJECT_DIR)}")

    print("Готово. Качи двата обновени .cer файла на съответните сървъри.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError) as error:
        print(f"Грешка: {error}", file=sys.stderr)
        sys.exit(1)
