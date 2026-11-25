#!/usr/bin/env bash
# Membuat .env dari .env.example dan mengisi secret yang masih kosong.
# Nilai secret yang sudah terisi tidak pernah ditimpa; nilai tidak pernah dicetak.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT/.env"
SECRETS=(JWT_SECRET HMAC_WEBHOOK_SECRET)

if [ ! -f "$ENV_FILE" ]; then
  cp "$ROOT/.env.example" "$ENV_FILE"
  echo "Membuat .env dari .env.example"
fi

# Mengganti (atau menambahkan) KEY=VALUE tanpa sed GNU-only.
set_var() {
  local key="$1" value="$2" tmp
  tmp="$(mktemp)"
  awk -v key="$key" -v value="$value" '
    BEGIN { done = 0 }
    index($0, key "=") == 1 { if (!done) { print key "=" value; done = 1 }; next }
    { print }
    END { if (!done) print key "=" value }
  ' "$ENV_FILE" > "$tmp"
  cat "$tmp" > "$ENV_FILE"
  rm -f "$tmp"
}

current_value() {
  awk -v key="$1" 'index($0, key "=") == 1 { v = substr($0, length(key) + 2) } END { print v }' "$ENV_FILE"
}

for name in "${SECRETS[@]}"; do
  value="$(current_value "$name" | tr -d '[:space:]"'"'")"
  if [ -z "$value" ]; then
    set_var "$name" "$(openssl rand -hex 32)"
    echo "$name: dibuat"
  else
    echo "$name: sudah terisi, dilewati"
  fi
done
