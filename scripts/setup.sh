#!/usr/bin/env bash
# setup.sh — Bootstrap openclaw credentials from .env
# Usage: bash scripts/setup.sh
# Run once after cloning, or again after rotating keys.

set -euo pipefail

ENV_FILE="$(dirname "$0")/../.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "ERROR: .env not found. Copy .env.example and fill in your keys:"
  echo "  cp .env.example .env"
  exit 1
fi

# Load .env
set -a
source "$ENV_FILE"
set +a

# Validate required vars
required=(ANTHROPIC_API_KEY OPENROUTER_API_KEY GOOGLE_API_KEY GITHUB_COPILOT_TOKEN GATEWAY_AUTH_TOKEN WHATSAPP_ALLOWED_FROM)
missing=()
for var in "${required[@]}"; do
  [[ -z "${!var:-}" ]] && missing+=("$var")
done
if [[ ${#missing[@]} -gt 0 ]]; then
  echo "ERROR: Missing required values in .env: ${missing[*]}"
  exit 1
fi

DATA_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# ── auth-profiles.json ──────────────────────────────────────────────────────
AUTH_FILE="$DATA_DIR/agents/main/agent/auth-profiles.json"
mkdir -p "$(dirname "$AUTH_FILE")"

python3 - <<PYEOF
import json, os

path = "$AUTH_FILE"
try:
    with open(path) as f:
        d = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    d = {"version": 1, "profiles": {}, "lastGood": {}, "usageStats": {}}

d.setdefault("profiles", {})
d["profiles"]["anthropic:default"]      = {"type": "token",   "provider": "anthropic",      "token": os.environ["ANTHROPIC_API_KEY"]}
d["profiles"]["openrouter:default"]     = {"type": "api_key", "provider": "openrouter",     "key":   os.environ["OPENROUTER_API_KEY"]}
d["profiles"]["google:default"]         = {"type": "api_key", "provider": "google",         "key":   os.environ["GOOGLE_API_KEY"]}
d["profiles"]["github-copilot:github"]  = {"type": "token",   "provider": "github-copilot", "token": os.environ["GITHUB_COPILOT_TOKEN"]}

with open(path, "w") as f:
    json.dump(d, f, indent=2)
print("  ✓ auth-profiles.json updated")
PYEOF

# ── models.json (openrouter apiKey) ─────────────────────────────────────────
MODELS_FILE="$DATA_DIR/agents/main/agent/models.json"
if [[ -f "$MODELS_FILE" ]]; then
  python3 - <<PYEOF
import json, os
path = "$MODELS_FILE"
with open(path) as f:
    d = json.load(f)
if "openrouter" in d.get("providers", {}):
    d["providers"]["openrouter"]["apiKey"] = os.environ["OPENROUTER_API_KEY"]
    with open(path, "w") as f:
        json.dump(d, f, indent=2)
    print("  ✓ models.json updated")
PYEOF
fi

# ── openclaw.json (gateway token + whatsapp allowFrom) ──────────────────────
CONFIG_FILE="$DATA_DIR/openclaw.json"
if [[ -f "$CONFIG_FILE" ]]; then
  python3 - <<PYEOF
import json, os
path = "$CONFIG_FILE"
with open(path) as f:
    d = json.load(f)

d.setdefault("gateway", {}).setdefault("auth", {})["token"] = os.environ["GATEWAY_AUTH_TOKEN"]

allowed = [n.strip() for n in os.environ["WHATSAPP_ALLOWED_FROM"].split(",") if n.strip()]
d.setdefault("channels", {}).setdefault("whatsapp", {})["allowFrom"] = allowed

with open(path, "w") as f:
    json.dump(d, f, indent=2)
print("  ✓ openclaw.json updated")
PYEOF
fi

echo ""
echo "Setup complete. Start openclaw with:"
echo "  pm2 start ecosystem.config.cjs && pm2 save"
