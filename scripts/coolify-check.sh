#!/usr/bin/env bash
# Verifica que los compose del kit cumplen el contrato para Coolify.
# Renderiza los compose con valores ficticios no secretos y comprueba con
# jq los puntos 1 (sin escape a Traefik ni poder sobre el host) y 2
# (sin nombres fijos de proyecto, red ni volumen) del contrato.
# Uso: bash scripts/coolify-check.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

command -v docker >/dev/null 2>&1 || { echo "ERROR: docker no disponible" >&2; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "ERROR: jq no disponible" >&2; exit 1; }

# compose.yaml es el compose de producción. compose.bootstrap.yaml se usa
# solo en el primer arranque para crear el admin y nunca debe desplegarse
# en Coolify.
COMPOSE_FILES=("compose.yaml")

TMP_ENV="$(mktemp -t coolify-check.XXXXXX.env)"
trap 'rm -f "$TMP_ENV"' EXIT

# Devuelve un valor ficticio no secreto para la variable dada.
fake_value() {
  local var="$1"
  case "$var" in
    COMPOSE_PROJECT_NAME) echo "coolify-check-proj" ;;
    VOLUME_PREFIX) echo "coolify-check-vol" ;;
    ADMINMAIL) echo "admin@ejemplo.invalid" ;;
    ADMINPASS) echo "x1234567890abcdef1234567890abcdef" ;;
    TRUSTED_HOSTS) echo "^(localhost|127[.]0[.]0[.]1|ejemplo[.]invalid)$" ;;
    TRUSTED_PROXIES) echo "127.0.0.1" ;;
    MAILER_URL) echo "null://localhost" ;;
    APP_SECRET|DB_PASSWORD|DB_ROOT_PASSWORD) echo "x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef" ;;
    *) echo "x${var}1234567890abcdef" ;;
  esac
}

# Render y validación.
RENDER=""
for compose in "${COMPOSE_FILES[@]}"; do
  # Extraer todas las variables ${VAR} y ${VAR:-defecto} que aparecen en el compose.
  VARS="$(awk '
    match($0, /\$\{[A-Za-z_][A-Za-z0-9_]*(:[^}]*)?\}/) {
      s = substr($0, RSTART, RLENGTH)
      sub(/^\$\{/, "", s)
      sub(/\}.*$/, "", s)
      sub(/:.*$/, "", s)
      print s
    }
  ' "$REPO_ROOT/$compose" | sort -u)"

  {
    echo "# Generado por scripts/coolify-check.sh (valores ficticios no secretos)"
    for v in $VARS; do
      val="$(fake_value "$v")"
      # Las comillas simples se escapan duplicándolas.
      esc="${val//\'/\'\'}"
      echo "$v='$esc'"
    done
  } > "$TMP_ENV"

  PARTIAL="$(docker compose \
    --project-directory "$REPO_ROOT" \
    -f "$REPO_ROOT/$compose" \
    --env-file "$TMP_ENV" \
    config --format json)" || {
    echo "ERROR: no se pudo renderizar $compose" >&2
    echo "$PARTIAL" >&2
    exit 1
  }

  if [ -z "$RENDER" ]; then
    RENDER="$PARTIAL"
  else
    RENDER="$(jq -s '.[0].services += .[1].services | .[0]' \
      <(printf '%s' "$RENDER") <(printf '%s' "$PARTIAL"))"
  fi
done

FAILED=0

# Contrato punto 2: sin name: a nivel raíz en el YAML fuente.
for compose in "${COMPOSE_FILES[@]}"; do
  if grep -qE '^name:' "$REPO_ROOT/$compose"; then
    echo "FALLA contrato 2: nombre de proyecto fijo a nivel raíz en $compose"
    FAILED=1
  fi
done

# Contrato punto 2: volúmenes sin name: fijo (acepta ${VAR} como prefijo).
# Se valida sobre el YAML fuente para distinguir nombres con variable de
# nombres literales; el render ya tiene el valor sustituido.
for compose in "${COMPOSE_FILES[@]}"; do
  INVALID_VOL_SRC="$(awk '
    BEGIN { in_vol = 0; depth = 0 }
    /^[[:space:]]*$/ { next }
    /^volumes:[[:space:]]*$/ { in_vol = 1; next }
    in_vol && /^[A-Za-z]/ { in_vol = 0 }
    in_vol && /^[[:space:]]+[A-Za-z0-9_-]+:[[:space:]]*$/ {
      # Inicio de un subvolumen (sin valor inline); resetea name.
      current = $0
      sub(/^[[:space:]]+/, "", current)
      sub(/:.*$/, "", current)
      subname = ""
    }
    in_vol && /^[[:space:]]+name:[[:space:]]*/ {
      line = $0
      sub(/^[[:space:]]+name:[[:space:]]*/, "", line)
      subname = line
      # name: debe empezar con ${ para considerarse variable.
      if (subname !~ /^\$\{/) {
        printf("%s: name=%s\n", current, subname)
      }
    }
  ' "$REPO_ROOT/$compose")"
  if [ -n "$INVALID_VOL_SRC" ]; then
    echo "FALLA contrato 2: volúmenes con nombre fijo en $compose:"
    printf '%s\n' "$INVALID_VOL_SRC" | sed 's/^/  - /'
    FAILED=1
  fi
done

# Contrato punto 2: redes sin name: fijo (Coolify las crea).
# Si no se declaran redes, .networks en el render es {} y no hay nada que
# validar; las redes por defecto de Docker Compose no se imprimen como
# declaradas.
for compose in "${COMPOSE_FILES[@]}"; do
  INVALID_NET_SRC="$(awk '
    BEGIN { in_net = 0 }
    /^[[:space:]]*$/ { next }
    /^networks:[[:space:]]*$/ { in_net = 1; next }
    in_net && /^[A-Za-z]/ { in_net = 0 }
    in_net && /^[[:space:]]+name:[[:space:]]*/ {
      line = $0
      sub(/^[[:space:]]+name:[[:space:]]*/, "", line)
      if (line !~ /^\$\{/) {
        printf("name=%s\n", line)
      }
    }
  ' "$REPO_ROOT/$compose")"
  if [ -n "$INVALID_NET_SRC" ]; then
    echo "FALLA contrato 2: redes con nombre fijo en $compose:"
    printf '%s\n' "$INVALID_NET_SRC" | sed 's/^/  - /'
    FAILED=1
  fi
done

# Contrato punto 1: en cada servicio sin profiles no puede haber nada que
# salte Traefik ni dé poder sobre el host.
INVALID_SVC="$(printf '%s' "$RENDER" | jq -r '
  .services
  | to_entries
  | map({
      svc: .key,
      profiles: (.value.profiles // []),
      ports: (.value.ports // []),
      container_name: (.value.container_name // null),
      privileged: (.value.privileged // false),
      cap_add: (.value.cap_add // []),
      devices: (.value.devices // []),
      network_mode: (.value.network_mode // null),
      pid: (.value.pid // null),
      ipc: (.value.ipc // null),
      security_opt: (.value.security_opt // []),
      binds: ([.value.volumes // [] | .[] | select(has("source") | not) | select(.type == "bind") | .source])
    })
  | map(select(.profiles | length == 0))
  | map(
      . as $s
      | [
          (if ($s.ports | length > 0) then "ports=\($s.ports | tostring)" else empty end),
          (if $s.container_name != null then "container_name=\($s.container_name)" else empty end),
          (if $s.privileged then "privileged=true" else empty end),
          (if ($s.cap_add | length > 0) then "cap_add=\($s.cap_add | tostring)" else empty end),
          (if ($s.devices | length > 0) then "devices=\($s.devices | tostring)" else empty end),
          (if $s.network_mode == "host" then "network_mode=host" else empty end),
          (if $s.pid == "host" then "pid=host" else empty end),
          (if $s.ipc == "host" then "ipc=host" else empty end),
          (if ($s.security_opt | map(select(. == "unconfined")) | length > 0) then "security_opt=unconfined" else empty end),
          (if ($s.binds | length > 0) then "binds=\($s.binds | tostring)" else empty end)
        ]
      | map("\($s.svc):\(.)")
    )
  | flatten[]
')"

if [ -n "$INVALID_SVC" ]; then
  echo "FALLA contrato 1: servicios rompen el contrato de Coolify:"
  printf '%s\n' "$INVALID_SVC" | sed 's/^/  - /'
  FAILED=1
fi

if [ "$FAILED" -ne 0 ]; then
  exit 1
fi

echo "OK: ${COMPOSE_FILES[*]} cumple el contrato de Coolify"