#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Backup на MySQL база от отдалечен сървър през SSH.
#
# По подразбиране:
#   - прави само backup
#
# Ако е подаден --restore:
#   - пита за потвърждение
#   - DROP DATABASE
#   - CREATE DATABASE
#   - restore от новосъздадения backup
#
# Примери:
#
#   ./ssh_mysql_backup.sh
#
#   ./ssh_mysql_backup.sh --restore
#
#   ./ssh_mysql_backup.sh --restore --local-db=iotdb_dev
#
#   ./ssh_mysql_backup.sh --restore --local-db=iotdb_dev --no-ask
#
# ============================================================

set -euo pipefail

# ---------- Remote ----------
HOST_ALIAS="server_db"
REMOTE_DB_NAME="iotdb"
SUDO_CMD="sudo -n"

# ---------- Local backup ----------
LOCAL_DIR="$HOME/backups/mysql"
RETAIN_DAYS=30

# ---------- Local mysql ----------
MYSQL_HOST="localhost"
MYSQL_PORT="3306"
MYSQL_USER="root"
MYSQL_PASS=""

# ---------- Options ----------
DO_RESTORE=false
ASK_CONFIRM=true
LOCAL_DB_NAME="$REMOTE_DB_NAME"

show_help() {
cat <<EOF
Usage:
  $0 [options]

Options:

  --restore
      След backup възстановява локалната база

  --local-db=NAME
      Име на локалната база за restore

  --no-ask
      Не пита преди DROP DATABASE

  --help
      Показва помощ

Examples:

  Само backup

      $0

  Backup + restore

      $0 --restore

  Restore в друга база

      $0 --restore --local-db=iotdb_dev

  Restore без потвърждение

      $0 --restore --local-db=iotdb_dev --no-ask

EOF
}

# ============================================================
# Parse arguments
# ============================================================

for arg in "$@"; do
    case "$arg" in
        --restore)
            DO_RESTORE=true
            ;;
        --no-ask)
            ASK_CONFIRM=false
            ;;
        --local-db=*)
            LOCAL_DB_NAME="${arg#*=}"
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo "[!] Непознат параметър: $arg"
            echo
            show_help
            exit 1
            ;;
    esac
done

# ============================================================
# Проверки
# ============================================================

command -v ssh >/dev/null
command -v gzip >/dev/null
command -v gunzip >/dev/null

if $DO_RESTORE; then
    command -v mysql >/dev/null
fi

mkdir -p "$LOCAL_DIR"

STAMP="$(date +%F_%H-%M-%S)"
OUTFILE="${LOCAL_DIR}/${REMOTE_DB_NAME}_${STAMP}.sql.gz"

# ============================================================
# Backup
# ============================================================

echo "[*] Backup на '${REMOTE_DB_NAME}' от '${HOST_ALIAS}'..."
echo "[*] Файл: ${OUTFILE}"

ssh -o RequestTTY=no "${HOST_ALIAS}" \
    "${SUDO_CMD} mysqldump --databases ${REMOTE_DB_NAME} | gzip -c" \
    > "${OUTFILE}"

gzip -t "${OUTFILE}"

echo "[✓] Backup успешен"

# ============================================================
# Restore
# ============================================================

if $DO_RESTORE; then

    echo
    echo "[*] Restore"
    echo "    Remote DB : ${REMOTE_DB_NAME}"
    echo "    Local DB  : ${LOCAL_DB_NAME}"
    echo

    if $ASK_CONFIRM; then

        read -r -p "Ще бъде изтрита локалната база '${LOCAL_DB_NAME}'. Продължавам? [y/N] " ans

        case "$ans" in
            y|Y|yes|YES)
                ;;
            *)
                echo "[x] Restore отменен."
                exit 0
                ;;
        esac
    fi

    MYSQL_AUTH=(-h "$MYSQL_HOST" -P "$MYSQL_PORT" -u "$MYSQL_USER")

    if [[ -n "$MYSQL_PASS" ]]; then
        MYSQL_AUTH+=(-p"$MYSQL_PASS")
    fi

    echo
    echo "[*] DROP DATABASE '${LOCAL_DB_NAME}'"

    mysql "${MYSQL_AUTH[@]}" <<EOF
DROP DATABASE IF EXISTS \`${LOCAL_DB_NAME}\`;

CREATE DATABASE \`${LOCAL_DB_NAME}\`
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
EOF

    echo "[*] Restore от ${OUTFILE}"

    gunzip -c "${OUTFILE}" |
    sed \
        -e "s/^CREATE DATABASE.*\`${REMOTE_DB_NAME}\`/CREATE DATABASE IF NOT EXISTS \`${LOCAL_DB_NAME}\`/" \
        -e "s/^USE \`${REMOTE_DB_NAME}\`;/USE \`${LOCAL_DB_NAME}\`;/" |
    mysql "${MYSQL_AUTH[@]}"

    echo "[✓] Restore завърши успешно"
fi

# ============================================================
# Изтриване на стари backup-и
# ============================================================

if [[ "$RETAIN_DAYS" -gt 0 ]]; then

    echo
    echo "[*] Изтриване на backup-и по-стари от ${RETAIN_DAYS} дни..."

    find "${LOCAL_DIR}" \
        -type f \
        -name "${REMOTE_DB_NAME}_*.sql.gz" \
        -mtime +"${RETAIN_DAYS}" \
        -print \
        -delete || true
fi

echo
echo "[✓] Готово"
