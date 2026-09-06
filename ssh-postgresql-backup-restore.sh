#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

# Defaults match core/db.py; environment variables can override these settings.
HOST_ALIAS="${HOST_ALIAS:-iothost}"
DB_NAME="${DB_NAME:-iotdb}"
DB_USER="${DB_USER:-iotuser}"
DB_PASSWORD="${DB_PASSWORD:-iotpass}"
LOCAL_DIR="${LOCAL_DIR:-$HOME/backups/iot}"
RETAIN_DAYS="${RETAIN_DAYS:-90}"
# Explicit local socket prevents PGHOST/PGSERVICE from redirecting a restore.
LOCAL_PGHOST="${LOCAL_PGHOST:-/var/run/postgresql}"
LOCAL_PGPORT="${LOCAL_PGPORT:-5432}"

MODE=backup
BACKUP_FILE=""
TEMP_FILE=""
STAGE_DB=""
STAGE_CREATED=0
CUTOVER_STARTED=0
PHASE="инициализация"

log() { printf '[*] %s\n' "$*"; }
die() { printf '[!] %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<EOF
Употреба:
  bash sh/db_backup.sh                         Нов бекъп от ${HOST_ALIAS}
  bash sh/db_backup.sh --restore               Нов бекъп, после локален restore
  bash sh/db_backup.sh --restore архив.sql.gz   Restore от файл, без нов бекъп
  bash sh/db_backup.sh --help

Архиви: ${LOCAL_DIR}; пазят се ${RETAIN_DAYS} дни (0 изключва ротацията).
Restore зарежда временна база и заменя ${DB_NAME} само след успешно зареждане.
При замяната активните връзки се прекъсват и старите локални данни се изтриват.
Настройва ${DB_USER} с LOGIN, парола и права върху потребителските схеми.

Настройки чрез environment: HOST_ALIAS, DB_NAME, DB_USER, DB_PASSWORD,
LOCAL_DIR, RETAIN_DAYS, LOCAL_PGHOST (локален socket), LOCAL_PGPORT.
Дампът трябва да е plain SQL от pg_dump без --create, компресиран с gzip.
EOF
}

admin_psql() {
  sudo -u postgres psql -X --no-password --set=ON_ERROR_STOP=1 \
    --host="$LOCAL_PGHOST" --port="$LOCAL_PGPORT" --username=postgres "$@"
}

connection_help() {
  printf '[!] Няма връзка с локалния PostgreSQL на %s:%s.\n' "$LOCAL_PGHOST" "$LOCAL_PGPORT" >&2
  if command -v pg_lsclusters >/dev/null; then
    printf '[*] Локални PostgreSQL cluster-и:\n' >&2
    pg_lsclusters >&2 || true
    printf '[!] Ако правилният cluster е спрян: sudo pg_ctlcluster <версия> <име> start\n' >&2
  fi
  printf '[!] За друг порт използвайте LOCAL_PGPORT=<порт>; за друг socket — LOCAL_PGHOST=<директория>.\n' >&2
  printf '[!] Портът трябва да съвпада и с URL адреса в core/db.py (по подразбиране localhost:5432).\n' >&2
  printf '[!] Възстановяването не е започнало; базите не са променени.\n' >&2
}

cleanup() {
  local status=$?
  trap - EXIT ERR
  set +e
  if [[ -n "$TEMP_FILE" ]]; then rm -f -- "$TEMP_FILE"; fi
  if (( CUTOVER_STARTED && status != 0 )); then
    # A failed rename transaction leaves the original name intact. Reopen it.
    if ! admin_psql --dbname=postgres --set=target="$DB_NAME" <<'SQL'
SELECT format('ALTER DATABASE %I ALLOW_CONNECTIONS true', datname)
FROM pg_database WHERE datname = :'target'
\gexec
SQL
    then
      printf '[!] Проверете ръчно ALLOW_CONNECTIONS на %s.\n' "$DB_NAME" >&2
    fi
  fi
  if (( STAGE_CREATED )); then
    if ! sudo -u postgres dropdb --host="$LOCAL_PGHOST" --port="$LOCAL_PGPORT" \
      --username=postgres --no-password --if-exists --force -- "$STAGE_DB"; then
      printf '[!] Не успях да премахна временната база %s.\n' "$STAGE_DB" >&2
    fi
  fi
  exit "$status"
}
trap cleanup EXIT
# Subshell errors propagate to the parent; report them only once there.
trap 'status=$?; if (( BASH_SUBSHELL == 0 )); then printf "[!] %s: грешка на ред %s (код %s).\n" "$PHASE" "$LINENO" "$status" >&2; fi; exit "$status"' ERR
trap 'exit 130' INT
trap 'exit 143' TERM

case "${1:-}" in
  --restore)
    (( $# <= 2 )) || die "Твърде много аргументи; вижте --help."
    MODE=restore
    if (( $# == 2 )); then
      [[ -n "$2" ]] || die "Празен път до архив."
      BACKUP_FILE="$2"
    fi
    ;;
  -h|--help) usage; exit 0 ;;
  "") (( $# == 0 )) || die "Невалиден празен аргумент." ;;
  *) die "Непознат аргумент: $1; вижте --help." ;;
esac

# Keep names safe for remote shell use and leave room for temporary DB suffixes.
[[ "$DB_NAME" =~ ^[a-z_][a-z0-9_]{0,31}$ ]] || die "Невалидно DB_NAME (до 32 символа)."
[[ "$DB_NAME" != postgres && "$DB_NAME" != template* ]] || die "Не може да се заменя системна база."
[[ "$DB_USER" =~ ^[a-z_][a-z0-9_]{0,62}$ && "$DB_USER" != postgres && "$DB_USER" != pg_* ]] || die "Невалидно DB_USER."
[[ "$HOST_ALIAS" != -* && -n "$HOST_ALIAS" ]] || die "Невалиден HOST_ALIAS."
[[ "$RETAIN_DAYS" =~ ^(0|[1-9][0-9]{0,4})$ ]] || die "RETAIN_DAYS трябва да е цяло число от 0 до 99999."
[[ "$LOCAL_PGHOST" == /* ]] || die "LOCAL_PGHOST трябва да е абсолютен път до локален socket."
[[ "$LOCAL_PGPORT" =~ ^[1-9][0-9]{0,4}$ ]] && (( LOCAL_PGPORT <= 65535 )) || die "Невалиден LOCAL_PGPORT."

for cmd in gzip flock mktemp; do
  command -v "$cmd" >/dev/null || die "Липсва необходимата команда: $cmd"
done
mkdir -p -- "$LOCAL_DIR"
LOCAL_DIR="$(cd "$LOCAL_DIR" && pwd -P)"
exec 9>"${LOCAL_DIR}/.${DB_NAME}.lock"
flock -n 9 || die "Вече работи backup/restore за ${DB_NAME} в ${LOCAL_DIR}."

if [[ "$MODE" == restore ]]; then
  if [[ -n "$BACKUP_FILE" ]]; then
    [[ -f "$BACKUP_FILE" && -r "$BACKUP_FILE" ]] || die "Архивът не може да се прочете: ${BACKUP_FILE}"
  fi
  PHASE="проверка на локалния PostgreSQL"
  command -v sudo >/dev/null || die "Липсва необходимата команда: sudo"
  log "Проверявам sudo и локалния PostgreSQL (${LOCAL_PGHOST}:${LOCAL_PGPORT})..."
  sudo -v
  sudo -u postgres sh -c '
    missing=0
    for cmd in psql dropdb createdb; do
      if ! command -v "$cmd" >/dev/null; then
        printf "[!] Липсва команда за postgres: %s\n" "$cmd" >&2
        missing=1
      fi
    done
    if [ "$missing" -ne 0 ]; then
      printf "[!] Проверете PATH на sudo. За Ubuntu/Debian: sudo apt install postgresql-client\n" >&2
    fi
    exit "$missing"
  '
  if server_version="$(admin_psql --dbname=postgres --tuples-only --no-align --command='SHOW server_version_num')"; then
    :
  else
    status=$?
    connection_help
    exit "$status"
  fi
  [[ "$server_version" =~ ^[0-9]+$ ]] && (( server_version >= 140000 )) \
    || die "За restore е необходим PostgreSQL 14 или по-нов."
fi

if [[ -z "$BACKUP_FILE" ]]; then
  PHASE="отдалечен бекъп"
  command -v ssh >/dev/null || die "Липсва необходимата команда: ssh"
  TEMP_FILE="$(mktemp "${LOCAL_DIR}/${DB_NAME}_$(date -u +%Y-%m-%dT%H-%M-%SZ)_XXXXXX.sql.gz.part")"
  BACKUP_FILE="${TEMP_FILE%.part}"
  log "Правя дамп на ${DB_NAME} от ${HOST_ALIAS} → ${BACKUP_FILE}"
  # Both pipelines must propagate errors: a gzip of a failed dump can be valid.
  # LC_ALL=C avoids remote locale warnings; SSH/sudo fail instead of prompting.
  ssh -T -o BatchMode=yes -o ConnectTimeout=15 \
    -o ServerAliveInterval=15 -o ServerAliveCountMax=3 "$HOST_ALIAS" \
    "LC_ALL=C bash -o pipefail -c 'sudo -n -u postgres pg_dump --no-owner --no-privileges --format=plain --dbname=$DB_NAME | gzip -c'" \
    > "$TEMP_FILE"
  gzip -t -- "$TEMP_FILE"
  mv -- "$TEMP_FILE" "$BACKUP_FILE"
  TEMP_FILE=""
  printf '[✓] Архивът е готов: %s\n' "$BACKUP_FILE"
fi

if [[ "$MODE" == restore ]]; then
  PHASE="проверка на архива"
  [[ -f "$BACKUP_FILE" && -r "$BACKUP_FILE" ]] || die "Архивът не може да се прочете: ${BACKUP_FILE}"
  log "Проверявам архива: ${BACKUP_FILE}"
  gzip -t -- "$BACKUP_FILE"

  PHASE="настройване на потребителя"
  log "Настройвам локалния потребител ${DB_USER}..."
  # Password goes through stdin, not process arguments; SQL literals are escaped.
  sql_password="${DB_PASSWORD//\'/\'\'}"
  {
    cat <<'SQL'
SET standard_conforming_strings = on;
SELECT format('CREATE ROLE %I', :'app_user')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'app_user')
\gexec
SQL
    printf 'ALTER ROLE :"app_user" WITH LOGIN PASSWORD '\''%s'\'';\n' "$sql_password"
  } | admin_psql --dbname=postgres --single-transaction --set=app_user="$DB_USER"
  unset sql_password

  PHASE="зареждане във временна база"
  suffix="${BASHPID}_${RANDOM}"
  STAGE_DB="${DB_NAME}_restore_${suffix}"
  OLD_DB="${DB_NAME}_previous_${suffix}"
  log "Зареждам ${STAGE_DB}; текущата ${DB_NAME} остава на място..."
  sudo -u postgres createdb --host="$LOCAL_PGHOST" --port="$LOCAL_PGPORT" \
    --username=postgres --no-password --template=template0 --owner="$DB_USER" -- "$STAGE_DB"
  STAGE_CREATED=1
  gzip -dc -- "$BACKUP_FILE" | admin_psql --dbname="$STAGE_DB" --single-transaction --quiet

  PHASE="права и проверка на възстановената база"
  # Cover all application schemas, including future objects created by postgres.
  admin_psql --dbname="$STAGE_DB" --single-transaction --set=app_user="$DB_USER" <<'SQL'
SELECT format('GRANT USAGE, CREATE ON SCHEMA %I TO %I', nspname, :'app_user') || ';' ||
       format('GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA %I TO %I', nspname, :'app_user') || ';' ||
       format('GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA %I TO %I', nspname, :'app_user') || ';' ||
       format('GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA %I TO %I', nspname, :'app_user') || ';' ||
       format('ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA %I GRANT ALL PRIVILEGES ON TABLES TO %I', nspname, :'app_user') || ';' ||
       format('ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA %I GRANT ALL PRIVILEGES ON SEQUENCES TO %I', nspname, :'app_user') || ';' ||
       format('ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA %I GRANT EXECUTE ON FUNCTIONS TO %I', nspname, :'app_user')
FROM pg_namespace WHERE nspname <> 'information_schema' AND nspname !~ '^pg_'
\gexec
-- Reject empty/irrelevant dumps before replacing the application database.
DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname <> 'information_schema' AND n.nspname !~ '^pg_'
      AND c.relkind IN ('r', 'p')
  ) THEN
    RAISE EXCEPTION 'Restored database contains no application tables';
  END IF;
END $$;
ANALYZE;
SQL

  PHASE="замяна на локалната база"
  log "Заменям ${DB_NAME}; прекъсвам активните връзки..."
  log "При прекъсване проверете имената: ${DB_NAME}, ${STAGE_DB}, ${OLD_DB}."
  CUTOVER_STARTED=1
  # Commit ALLOW_CONNECTIONS before terminating sessions to prevent reconnects.
  admin_psql --dbname=postgres --set=target="$DB_NAME" <<'SQL'
SELECT format('ALTER DATABASE %I ALLOW_CONNECTIONS false', datname)
FROM pg_database WHERE datname = :'target'
\gexec
SELECT pg_terminate_backend(pid, 10000) FROM pg_stat_activity WHERE datname = :'target';
SQL
  # The two renames commit together, so a failed switch preserves the old name.
  admin_psql --dbname=postgres --single-transaction \
    --set=target="$DB_NAME" --set=stage="$STAGE_DB" --set=previous="$OLD_DB" <<'SQL'
SET lock_timeout = '15s';
SELECT format('ALTER DATABASE %I RENAME TO %I', datname, :'previous')
FROM pg_database WHERE datname = :'target'
\gexec
ALTER DATABASE :"stage" RENAME TO :"target";
SQL
  CUTOVER_STARTED=0
  STAGE_CREATED=0
  # Only remove the old database after the replacement has committed.
  if ! sudo -u postgres dropdb --host="$LOCAL_PGHOST" --port="$LOCAL_PGPORT" \
    --username=postgres --no-password --if-exists --force -- "$OLD_DB"; then
    printf '[!] Restore е успешен, но старата база %s трябва да се изтрие ръчно.\n' "$OLD_DB" >&2
  fi
  printf '[✓] Възстановена: %s от %s; потребител: %s\n' "$DB_NAME" "$BACKUP_FILE" "$DB_USER"
fi

# Never rotate after a failed backup/restore, nor delete the archive just used.
PHASE="ротация на архивите"
if (( RETAIN_DAYS > 0 )); then
  if ! find "$LOCAL_DIR" -maxdepth 1 -type f -name "${DB_NAME}_*.sql.gz" \
    ! -samefile "$BACKUP_FILE" -mtime +"$RETAIN_DAYS" -print -delete; then
    printf '[!] Не всички стари архиви бяха изтрити.\n' >&2
  fi
fi
