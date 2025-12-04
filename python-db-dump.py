#!/usr/bin/env python3
import argparse
import subprocess
import sqlite3
import sys
import os


def run_cmd(cmd: list[str], capture_output=False, env=None):
    """Run shell command safely, optionally returning output."""
    try:
        if capture_output:
            return subprocess.check_output(cmd, text=True, env=env)
        subprocess.check_call(cmd, env=env)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed: {' '.join(cmd)}")
        print(e)
        sys.exit(1)


def format_insert(table: str, cols: list[str], vals: list[str], mysql=False):
    """
    Returns formatted SQL INSERT block.
    cols stay on one line, values go multiline.
    """
    if mysql:
        quote_table = f"`{table}`"
    else:
        quote_table = f'"{table}"'

    return (
        f"INSERT INTO {quote_table} ({', '.join(cols)})\n"
        f"VALUES (\n"
        f"    {',\n    '.join([repr(v) for v in vals])}\n"
        f");\n"
    )


# =========================================================
#   MySQL
# =========================================================
def dump_mysql(args):
    print("[INFO] Dumping MySQL structure...")

    dump_cmd = ["mysqldump", "-u", args.user]
    if args.password:
        dump_cmd.append(f"-p{args.password}")
    if args.host:
        dump_cmd += ["-h", args.host]
    dump_cmd += ["--no-data", args.db]

    with open(args.out, "w") as f:
        subprocess.run(dump_cmd, stdout=f, check=True)

    print("[INFO] Listing MySQL tables...")

    table_query = f"""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = '{args.db}'
    """

    list_cmd = ["mysql", "-u", args.user]
    if args.password:
        list_cmd.append(f"-p{args.password}")
    if args.host:
        list_cmd += ["-h", args.host]
    list_cmd += ["-N", "-e", table_query]

    output = run_cmd(list_cmd, capture_output=True)
    tables = [t.strip() for t in output.splitlines() if t.strip()]

    with open(args.out, "a") as f:
        f.write("\n-- Last rows\n\n")

        for t in tables:
            print(f"[INFO] Querying: {t}")

            sql = f"SELECT * FROM `{t}` ORDER BY 1 DESC LIMIT {args.rows};"

            query_cmd = ["mysql", "-u", args.user]
            if args.password:
                query_cmd.append(f"-p{args.password}")
            if args.host:
                query_cmd += ["-h", args.host]
            query_cmd += [args.db, "-N", "-e", sql]

            res = run_cmd(query_cmd, capture_output=True)

            f.write(f"-- Table: {t}\n")

            if not res.strip():
                f.write("-- (No rows)\n\n")
                continue

            lines = res.splitlines()
            cols = lines[0].split("\t")

            for row in lines[1:]:
                vals = row.split("\t")
                block = format_insert(t, cols, vals, mysql=True)
                f.write(block)
            f.write("\n")


# =========================================================
#   PostgreSQL
# =========================================================
def dump_pgsql(args):
    print("[INFO] Dumping PostgreSQL structure...")

    env = os.environ.copy()
    if args.password:
        env["PGPASSWORD"] = args.password

    dump_cmd = [
        "pg_dump", "-s",
        "-U", args.user,
        "-h", args.host,
        "-p", args.port,
        args.db,
    ]

    with open(args.out, "w") as f:
        subprocess.run(dump_cmd, stdout=f, check=True, env=env)

    print("[INFO] Listing PostgreSQL tables...")

    list_query = """
        SELECT tablename
        FROM pg_tables
        WHERE schemaname='public';
    """

    list_cmd = [
        "psql",
        "-U", args.user,
        "-h", args.host,
        "-p", args.port,
        "-d", args.db,
        "-t",
        "-c", list_query
    ]

    output = run_cmd(list_cmd, capture_output=True, env=env)
    tables = [t.strip() for t in output.splitlines() if t.strip()]

    with open(args.out, "a") as f:
        f.write("\n-- Last rows\n\n")

        for t in tables:
            print(f"[INFO] Querying: {t}")

            sql = f'SELECT * FROM "{t}" ORDER BY 1 DESC LIMIT {args.rows};'

            query_cmd = [
                "psql",
                "-U", args.user,
                "-h", args.host,
                "-p", args.port,
                "-d", args.db,
                "-t", "-A", "-F", "\t",
                "-c", sql
            ]

            res = run_cmd(query_cmd, capture_output=True, env=env)
            lines = res.splitlines()

            f.write(f"-- Table: {t}\n")

            if not lines or lines == [""]:
                f.write("-- (No rows)\n\n")
                continue

            cols = lines[0].split("\t")

            for row in lines[1:]:
                vals = row.split("\t")
                block = format_insert(t, cols, vals, mysql=False)
                f.write(block)
            f.write("\n")


# =========================================================
#   SQLite
# =========================================================
def dump_sqlite(args):
    conn = sqlite3.connect(args.sqlite_file)
    print("[INFO] Dumping SQLite structure...")

    schema_rows = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table'"
    ).fetchall()

    with open(args.out, "w") as f:
        for row in schema_rows:
            if row[0]:
                f.write(row[0] + ";\n")

        f.write("\n-- Last rows\n\n")

        tables = [
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        ]

        for t in tables:
            print(f"[INFO] Querying: {t}")

            rows = list(
                conn.execute(
                    f"SELECT * FROM {t} ORDER BY 1 DESC LIMIT {args.rows}"
                )
            )

            cols = [c[1] for c in conn.execute(f"PRAGMA table_info({t})")]

            f.write(f"-- Table: {t}\n")

            if not rows:
                f.write("-- (No rows)\n\n")
                continue

            for r in rows:
                block = format_insert(t, cols, list(r), mysql=False)
                f.write(block)
            f.write("\n")

    conn.close()


# =========================================================
#   MAIN
# =========================================================
def main():
    parser = argparse.ArgumentParser(
        description="Dump only structure + last N rows of all tables."
    )

    parser.add_argument("--type", required=True, choices=["mysql", "pgsql", "sqlite"])
    parser.add_argument("--db")
    parser.add_argument("--sqlite-file")
    parser.add_argument("--user")
    parser.add_argument("--password", default="")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", default="5432")
    parser.add_argument("--rows", type=int, required=True)
    parser.add_argument("--out", required=True)

    args = parser.parse_args()

    if args.type in ("mysql", "pgsql") and not args.db:
        print("[ERROR] --db is required for MySQL/PostgreSQL.")
        sys.exit(1)

    if args.type in ("mysql", "pgsql") and not args.user:
        print("[ERROR] --user is required for MySQL/PostgreSQL.")
        sys.exit(1)

    if args.type == "sqlite" and not args.sqlite_file:
        print("[ERROR] --sqlite-file is required for SQLite.")
        sys.exit(1)

    if args.type == "mysql":
        dump_mysql(args)
    elif args.type == "pgsql":
        dump_pgsql(args)
    elif args.type == "sqlite":
        dump_sqlite(args)


if __name__ == "__main__":
    main()


# how to use
# $ python python-db-dump.py --type pgsql --db iotdb --user postgres --host 127.0.0.1 --rows 10 --out iotdb_dump.sql
