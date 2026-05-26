#!/usr/bin/env bash

# how to use
# chmod +x dump_pg_metadata.sh
# ./dump_pg_metadata.sh
# glow -w 0 -s dark -p db-name_schema_ai.md
# less db-name_schema.sql

set -euo pipefail

export PGPASSWORD="your_password"

DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="your_db"
DB_USER="postgres"
DB_SCHEMA="public"

OUT_SQL="${DB_NAME}_schema.sql"
OUT_AI="${DB_NAME}_schema_ai.md"

PSQL_BASE=(
  psql
  -h "$DB_HOST"
  -p "$DB_PORT"
  -U "$DB_USER"
  -d "$DB_NAME"
)

echo "Exporting PostgreSQL metadata for database: $DB_NAME"

#
# Exact PostgreSQL schema dump
#
pg_dump \
  -h "$DB_HOST" \
  -p "$DB_PORT" \
  -U "$DB_USER" \
  -d "$DB_NAME" \
  --schema="$DB_SCHEMA" \
  --schema-only \
  --no-owner \
  --no-privileges \
  > "$OUT_SQL"

#
# Get tables
#
TABLES=$("${PSQL_BASE[@]}" -Atc "
SELECT schemaname || '.' || tablename
FROM pg_tables
WHERE schemaname = '${DB_SCHEMA}'
ORDER BY schemaname, tablename;
")

#
# AI-friendly markdown
#
cat > "$OUT_AI" <<EOF
# PostgreSQL schema - AI friendly

Database: $DB_NAME  
Schema: $DB_SCHEMA  
Generated: $(date)

## Files

- \`${OUT_SQL}\` - exact PostgreSQL DDL
- \`${OUT_AI}\` - readable metadata summary

EOF

for TABLE_NAME in $TABLES; do

  TABLE_ONLY="${TABLE_NAME#*.}"

  echo "Processing $TABLE_NAME..."

  ROW_ESTIMATE=$("${PSQL_BASE[@]}" -Atc "
SELECT COALESCE(n_live_tup, 0)
FROM pg_stat_user_tables
WHERE schemaname = '${DB_SCHEMA}'
  AND relname = '${TABLE_ONLY}';
")

  cat >> "$OUT_AI" <<EOF
## $TABLE_NAME

Estimated rows: **$ROW_ESTIMATE**

### Columns

| Column | Type | Nullable | Default |
|---|---|---|---|
EOF

  "${PSQL_BASE[@]}" -AtF $'\t' -c "
SELECT
  column_name,
  format_type(a.atttypid, a.atttypmod) AS full_type,
  is_nullable,
  COALESCE(column_default, '')
FROM information_schema.columns c
JOIN pg_attribute a
  ON a.attname = c.column_name
JOIN pg_class cl
  ON cl.oid = a.attrelid
JOIN pg_namespace n
  ON n.oid = cl.relnamespace
WHERE c.table_schema = '${DB_SCHEMA}'
  AND c.table_name = '${TABLE_ONLY}'
  AND n.nspname = c.table_schema
  AND cl.relname = c.table_name
  AND a.attnum > 0
  AND NOT a.attisdropped
ORDER BY c.ordinal_position;
" | while IFS=$'\t' read -r COL TYPE NULLABLE DEFAULT_VALUE; do

    DEFAULT_VALUE="${DEFAULT_VALUE//|/\\|}"

    echo "| \`$COL\` | \`$TYPE\` | $NULLABLE | \`$DEFAULT_VALUE\` |" >> "$OUT_AI"

  done

  cat >> "$OUT_AI" <<EOF

### Primary keys

EOF

  PKS=$("${PSQL_BASE[@]}" -Atc "
SELECT
  '- \`' || kcu.column_name || '\`'
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
  ON tc.constraint_name = kcu.constraint_name
 AND tc.table_schema = kcu.table_schema
WHERE tc.constraint_type = 'PRIMARY KEY'
  AND tc.table_schema = '${DB_SCHEMA}'
  AND tc.table_name = '${TABLE_ONLY}'
ORDER BY kcu.ordinal_position;
")

  if [[ -n "$PKS" ]]; then
    echo "$PKS" >> "$OUT_AI"
  else
    echo "- none" >> "$OUT_AI"
  fi

  cat >> "$OUT_AI" <<EOF

### Foreign keys

| Column | References | Constraint |
|---|---|---|
EOF

  FK_ROWS=$("${PSQL_BASE[@]}" -AtF $'\t' -c "
SELECT
  kcu.column_name,
  ccu.table_schema || '.' || ccu.table_name || '(' || ccu.column_name || ')',
  tc.constraint_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
  ON tc.constraint_name = kcu.constraint_name
 AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage ccu
  ON ccu.constraint_name = tc.constraint_name
 AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema = '${DB_SCHEMA}'
  AND tc.table_name = '${TABLE_ONLY}'
ORDER BY kcu.column_name;
")

  if [[ -n "$FK_ROWS" ]]; then

    echo "$FK_ROWS" | while IFS=$'\t' read -r COL REF CONSTRAINT_NAME; do

      echo "| \`$COL\` | \`$REF\` | \`$CONSTRAINT_NAME\` |" >> "$OUT_AI"

    done

  else

    echo "| - | - | - |" >> "$OUT_AI"

  fi

  cat >> "$OUT_AI" <<EOF

### Indexes

\`\`\`text
EOF

  "${PSQL_BASE[@]}" -Atc "
SELECT indexname || ': ' || indexdef
FROM pg_indexes
WHERE schemaname = '${DB_SCHEMA}'
  AND tablename = '${TABLE_ONLY}'
ORDER BY indexname;
" >> "$OUT_AI"

  cat >> "$OUT_AI" <<EOF
\`\`\`

EOF

done

echo ""
echo "DONE:"
echo "  $OUT_SQL"
echo "  $OUT_AI"

