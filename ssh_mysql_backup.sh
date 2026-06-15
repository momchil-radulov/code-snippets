#!/usr/bin/env bash


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


# ============================================================
# Прекратява при:
#   - грешка в команда (-e)
#   - използване на недефинирана променлива (-u)
#   - грешка в някоя команда от pipe (-o pipefail)
# ============================================================

set -euo pipefail


# ============================================================
# Remote host
# ============================================================

# SSH потребител и хост
HOST_ALIAS="ubuntu@remote_host"

# Име на remote базата
REMOTE_DB_NAME="remote_db"

# Команда за sudo на remote машината
# sudo -n = без интерактивно въвеждане на парола
SUDO_CMD="sudo -n"


# ============================================================
# Локални backup-и
# ============================================================

# Директория за backup файловете
LOCAL_DIR="$HOME/backups/mysql"

# След колко дни да се изтриват старите backup-и
# 0 = не трий нищо
RETAIN_DAYS=365


# ============================================================
# Локален MySQL
# ============================================================

# ВНИМАНИЕ:
# localhost може да използва Unix socket и да се свърже към локален MySQL.
# За Docker контейнер използвай 127.0.0.1 + публикувания порт.
MYSQL_HOST="127.0.0.1"
MYSQL_PORT="3306"
# Ако root@localhost не приема връзки с парола
# (например е настроен с auth_socket),
# може да се създаде/промени така:
#
# CREATE USER IF NOT EXISTS 'root'@'localhost'
# IDENTIFIED BY 'root';
#
# GRANT ALL PRIVILEGES ON *.* TO 'root'@'localhost'
# WITH GRANT OPTION;
#
# FLUSH PRIVILEGES;
#
# Проверка:
# mysql -h 127.0.0.1 -P 3306 -u root -proot
MYSQL_USER="root"
MYSQL_PASS="root"

# Ако root работи чрез auth_socket:
#
# sudo mysql
#
# остави:
LOCAL_MYSQL_SUDO="sudo"
#
# Ако се логва нормално:
#
# LOCAL_MYSQL_SUDO=""
#
# тогава няма да се изпълнява чрез sudo.


# ============================================================
# Опции
# ============================================================

# Да се направи ли restore след backup
DO_RESTORE=false

# Да се пита ли преди DROP DATABASE
ASK_CONFIRM=true

# По подразбиране локалната база е със същото име
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

  $0

  $0 --restore

  $0 --restore --local-db=iot_dev

  $0 --restore --local-db=iot_dev --no-ask

EOF
}


# ============================================================
# Обработка на параметрите
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
            show_help
            exit 1
            ;;

    esac
done


# ============================================================
# Проверка за необходими програми
# ============================================================

command -v ssh >/dev/null
command -v gzip >/dev/null
command -v gunzip >/dev/null

# mysql е нужен само ако ще има restore
if $DO_RESTORE; then
    command -v mysql >/dev/null
fi


# Създаване на backup директорията
mkdir -p "$LOCAL_DIR"


# ============================================================
# Генериране име на backup файла
# ============================================================

STAMP="$(date +%F_%H-%M-%S)"
OUTFILE="${LOCAL_DIR}/${REMOTE_DB_NAME}_${STAMP}.sql.gz"


echo "[*] Backup на '${REMOTE_DB_NAME}' от '${HOST_ALIAS}'..."
echo "[*] Файл: ${OUTFILE}"


# ============================================================
# Backup
# ============================================================
#
# Remote:
#
# mysqldump -> gzip
#
# Local:
#
# записва .sql.gz файла
#
ssh -o RequestTTY=no "${HOST_ALIAS}" \
    "${SUDO_CMD} mysqldump --databases ${REMOTE_DB_NAME} | gzip -c" \
    > "${OUTFILE}"


# Проверка дали gzip архивът е валиден
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

    # Допълнително потвърждение
    if $ASK_CONFIRM; then

        read -r -p \
            "Ще бъде изтрита локалната база '${LOCAL_DB_NAME}'. Продължавам? [y/N] " ans

        case "$ans" in
            y|Y|yes|YES)
                ;;
            *)
                echo "[x] Restore отменен."
                exit 0
                ;;
        esac
    fi


    # --------------------------------------------------------
    # mysql команда
    # --------------------------------------------------------

    MYSQL_CMD=(
        mysql
        -h "$MYSQL_HOST"
        -P "$MYSQL_PORT"
        -u "$MYSQL_USER"
    )

    # Добавяне на парола ако има такава
    if [[ -n "$MYSQL_PASS" ]]; then
        MYSQL_CMD+=(-p"$MYSQL_PASS")
    fi

    # При auth_socket:
    #
    # sudo mysql ...
    #
    if [[ -n "$LOCAL_MYSQL_SUDO" ]]; then
        MYSQL_CMD=(
            $LOCAL_MYSQL_SUDO
            "${MYSQL_CMD[@]}"
        )
    fi


    echo
    echo "[*] DROP DATABASE '${LOCAL_DB_NAME}'"


    # --------------------------------------------------------
    # Изтриване и създаване на локалната база
    # --------------------------------------------------------

    "${MYSQL_CMD[@]}" <<EOF
DROP DATABASE IF EXISTS \`${LOCAL_DB_NAME}\`;

CREATE DATABASE \`${LOCAL_DB_NAME}\`
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
EOF


    echo "[*] Restore от ${OUTFILE}"


    # --------------------------------------------------------
    # Преименуване на database името
    #
    # CREATE DATABASE remote_db
    # -> CREATE DATABASE local_db
    #
    # USE remote_db
    # -> USE local_db
    #
    # след което се подава към mysql
    # --------------------------------------------------------

    gunzip -c "${OUTFILE}" |
    sed \
        -e "s/^CREATE DATABASE.*\`${REMOTE_DB_NAME}\`/CREATE DATABASE IF NOT EXISTS \`${LOCAL_DB_NAME}\`/" \
        -e "s/^USE \`${REMOTE_DB_NAME}\`;/USE \`${LOCAL_DB_NAME}\`;/" |
    "${MYSQL_CMD[@]}"

    echo "[✓] Restore завърши успешно"
fi


# ============================================================
# Почистване на стари backup-и
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
