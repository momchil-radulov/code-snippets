#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_PATH="$(readlink -f -- "${BASH_SOURCE[0]}")"
ORIGINAL_ARGS=("$@")
TARGET_SERIES="${MARIADB_SERIES:-latest-LTS}"
REPO_SETUP_URL='https://r.mariadb.com/downloads/mariadb_repo_setup'
# Verified on 2026-08-06. If MariaDB updates the helper, verify and replace this value.
REPO_SETUP_SHA256="${MARIADB_REPO_SETUP_SHA256:-7325ac7755809ca3312b446bd832542421699298f25b701f9a111bb42df0c7c1}"

DRY_RUN=false
CURRENT_STEP='initial checks'
TEMP_DIR=''

usage() {
    cat <<'EOF'
Usage: ./reinstall_local_mariadb.sh [--dry-run]

DESTRUCTIVE: completely removes the local MySQL/MariaDB server, all databases
under /var/lib/mysql, and the database configuration under /etc/mysql. It then
installs the latest MariaDB LTS from the official MariaDB repository. It does
not create application databases or users.

Options:
  --dry-run   Show the plan and installed database packages without changing anything
  -h, --help  Show this help

Environment overrides:
  MARIADB_SERIES             Repository series (default: latest-LTS)
  MARIADB_REPO_SETUP_SHA256  Expected SHA-256 if the official helper has changed

Files outside the explicitly listed system paths are NOT touched. No databases,
users, SQL backups, or applications are created or started by this script.
EOF
}

die() {
    printf 'Error: %s\n' "$*" >&2
    exit 1
}

cleanup() {
    if [[ -n "$TEMP_DIR" && -d "$TEMP_DIR" && "$TEMP_DIR" == /tmp/* ]]; then
        rm -rf -- "$TEMP_DIR"
    fi
}

on_error() {
    local status=$?
    printf '\nFailed during: %s\n' "$CURRENT_STEP" >&2
    printf 'The old installation may already be removed; inspect the messages above.\n' >&2
    exit "$status"
}

trap cleanup EXIT
trap on_error ERR

while (($# > 0)); do
    case "$1" in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            die "unknown option: $1 (use --help)"
            ;;
    esac
done

[[ -r /etc/os-release ]] || die '/etc/os-release is missing'
# shellcheck disable=SC1091
source /etc/os-release
[[ "${ID:-}" == ubuntu && "${VERSION_CODENAME:-}" == noble ]] || \
    die "this script only supports Ubuntu 24.04 (noble); detected ${PRETTY_NAME:-unknown}"
[[ "$TARGET_SERIES" =~ ^(latest-LTS|mariadb-[0-9]+\.[0-9]+)$ ]] || \
    die "invalid MARIADB_SERIES: $TARGET_SERIES"
[[ "$REPO_SETUP_SHA256" =~ ^[a-fA-F0-9]{64}$ ]] || \
    die 'MARIADB_REPO_SETUP_SHA256 must contain exactly 64 hexadecimal characters'

mapfile -t DATABASE_PACKAGES < <(
    dpkg-query -W -f='${binary:Package}\t${db:Status-Abbrev}\n' 2>/dev/null |
        awk -F '\t' '
            $2 ~ /^ii/ && $1 ~ /^(mysql-(server|client|community|apt-config)(-[^:]*)?|mariadb-(server|client|backup|plugin)(-[^:]*)?|galera-[^:]+|default-mysql-(server|client)(-[^:]*)?)(:[^:]+)?$/ {
                print $1
            }
        ' | sort
)

printf 'Host: %s\n' "$(hostname)"
printf 'Operating system: %s\n' "${PRETTY_NAME}"
printf 'Target repository series: %s (currently MariaDB 12.3 LTS)\n' "$TARGET_SERIES"
printf '\nInstalled server/client packages that will be purged:\n'
if ((${#DATABASE_PACKAGES[@]} == 0)); then
    printf '  (none detected)\n'
else
    printf '  %s\n' "${DATABASE_PACKAGES[@]}"
fi

cat <<'EOF'

Local paths that will be permanently deleted:
  /var/lib/mysql
  /var/lib/mysql-files
  /var/lib/mysql-keyring
  /etc/mysql
  /var/log/mysql
  /var/log/mysql.err
  /var/log/mysql.log

Repository files that will be replaced if present:
  /etc/apt/sources.list.d/mysql.list
  /etc/apt/sources.list.d/mysql.sources
  /etc/apt/sources.list.d/mariadb.list
  /etc/apt/preferences.d/mariadb-enterprise.pref

Preserved:
  Every file outside the explicitly listed system paths
EOF

if [[ "$DRY_RUN" == true ]]; then
    printf '\nDry run complete; nothing was changed.\n'
    exit 0
fi

if ((EUID != 0)); then
    command -v sudo >/dev/null || die 'sudo is required'
    exec sudo -- "$SCRIPT_PATH" "${ORIGINAL_ARGS[@]}"
fi

printf '\nThis operation cannot be undone from the local database files.\n' >&2
printf 'Type DELETE LOCAL DATABASES to continue: ' >&2
IFS= read -r confirmation
[[ "$confirmation" == 'DELETE LOCAL DATABASES' ]] || \
    die 'confirmation did not match; nothing was changed'

CURRENT_STEP='stopping database services'
systemctl stop mysql.service 2>/dev/null || true
systemctl stop mariadb.service 2>/dev/null || true

mapfile -t DATABASE_PIDS < <(
    {
        pgrep -x mysqld 2>/dev/null || true
        pgrep -x mariadbd 2>/dev/null || true
    } | sort -nu
)
HOST_DATABASE_PIDS=()
for database_pid in "${DATABASE_PIDS[@]}"; do
    cgroup_path="$(sed -n 's/^0:://p' "/proc/${database_pid}/cgroup" 2>/dev/null || true)"
    if [[ "$cgroup_path" =~ /(docker[-/]|kubepods|libpod[-/]|lxc[-/]) ]]; then
        printf 'Leaving containerized database process %s running (%s).\n' \
            "$database_pid" "$cgroup_path"
    else
        HOST_DATABASE_PIDS+=("$database_pid")
    fi
done

if ((${#HOST_DATABASE_PIDS[@]} > 0)); then
    die "host database process(es) still running: ${HOST_DATABASE_PIDS[*]}; stop them manually and retry"
fi

if ((${#DATABASE_PACKAGES[@]} > 0)); then
    CURRENT_STEP='purging old database packages'
    DEBIAN_FRONTEND=noninteractive apt-get purge -y "${DATABASE_PACKAGES[@]}"
fi

CURRENT_STEP='deleting old database data and configuration'
for old_directory in \
    /var/lib/mysql \
    /var/lib/mysql-files \
    /var/lib/mysql-keyring \
    /etc/mysql \
    /var/log/mysql
do
    rm -rf -- "$old_directory"
done
rm -f -- /var/log/mysql.err /var/log/mysql.log

CURRENT_STEP='removing old database repository configuration'
rm -f -- \
    /etc/apt/sources.list.d/mysql.list \
    /etc/apt/sources.list.d/mysql.sources \
    /etc/apt/sources.list.d/mariadb.list \
    /etc/apt/preferences.d/mariadb-enterprise.pref

CURRENT_STEP='installing repository prerequisites'
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y ca-certificates curl apt-transport-https

CURRENT_STEP='downloading and verifying the official MariaDB repository helper'
TEMP_DIR="$(mktemp -d /tmp/mariadb-reinstall.XXXXXX)"
REPO_SETUP_FILE="${TEMP_DIR}/mariadb_repo_setup"
curl --fail --location --silent --show-error "$REPO_SETUP_URL" --output "$REPO_SETUP_FILE"
printf '%s  %s\n' "$REPO_SETUP_SHA256" "$REPO_SETUP_FILE" | sha256sum --check --status || {
    actual_checksum="$(sha256sum "$REPO_SETUP_FILE" | awk '{print $1}')"
    die "repository helper checksum mismatch (downloaded: $actual_checksum); verify it against the official MariaDB documentation before overriding MARIADB_REPO_SETUP_SHA256"
}

CURRENT_STEP='configuring the official MariaDB repository'
bash "$REPO_SETUP_FILE" \
    --mariadb-server-version="$TARGET_SERIES" \
    --os-type=ubuntu \
    --os-version=noble \
    --skip-maxscale \
    --skip-tools

CURRENT_STEP='installing MariaDB server and client'
DEBIAN_FRONTEND=noninteractive apt-get install -y \
    mariadb-server \
    mariadb-client \
    mariadb-backup

CURRENT_STEP='starting MariaDB'
systemctl enable --now mariadb.service
systemctl is-active --quiet mariadb.service

CURRENT_STEP='verifying the new installation'
installed_version="$(mariadb --protocol=socket --user=root --batch --skip-column-names \
    --execute='SELECT VERSION();')"
[[ "$installed_version" == *MariaDB* ]] || \
    die "the installed server does not identify itself as MariaDB: $installed_version"

printf '\nMariaDB installation completed successfully.\n'
printf 'Installed server: %s\n' "$installed_version"
printf 'Service: active\n'
printf 'No application databases or users were created.\n'
