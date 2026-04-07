# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

OpenClaw is a personal AI parenting assistant running as a WhatsApp bot. It tracks baby Kalana's feedings, weight, and diapers for her parents (Hawari & Mila) via a private WhatsApp group. The application is installed globally from the `openclaw` npm package — this directory (`~/.openclaw`) is the **runtime data directory**, not the source code.

## Process Management

```bash
# Start (first time)
pm2 start ecosystem.config.cjs && pm2 save

# Everyday operations
pm2 start all / pm2 stop all / pm2 restart all
pm2 start openclaw-18789 / pm2 stop openclaw-18789
pm2 logs / pm2 monit / pm2 status
pm2 resurrect                    # Restore after reboot
```

## OpenClaw CLI

```bash
openclaw                         # Start the daemon
openclaw channels login --channel whatsapp --account default   # Link WhatsApp
openclaw gateway status          # Check gateway health
```

## Architecture

### Runtime Layout

```
~/.openclaw/
├── openclaw.json                # Master config: agents, channels, gateway, plugins
├── ecosystem.config.cjs         # PM2 service config (gateway on :18789)
├── identity/device.json         # Device keypair (ED25519) — do not overwrite
├── agents/main/
│   ├── agent/                   # Agent runtime: auth-profiles.json, models.json
│   └── sessions/                # Conversation session JSONL logs
├── workspace/                   # Agent persona, instructions, and memory
├── flows/registry.sqlite        # Flow definitions (SQLite)
├── cron/                        # Scheduled reminders (cron jobs + run history)
├── delivery-queue/failed/       # Undelivered outbound messages (TTL: 7 days)
└── logs/                        # System logs
```

### Workspace (Agent Brain)

The `workspace/` directory is what the agent reads on every session. Key files:

| File | Purpose |
|------|---------|
| `AGENTS.md` | Core operating instructions — input parsing, logging rules, response format |
| `SOUL.md` | Persona definition — tone, boundaries, language style |
| `TOOLS.md` | Feed/weight/diaper format conventions, reminder schedule |
| `MEMORY.md` | Long-term durable memory — growth milestones, family info, preferences |
| `QUICK_START.md` | 5-minute session reset protocol (executed on every session start) |
| `memory/YYYY-MM-DD.md` | Daily feed/diaper/weight logs, one file per day |

### Memory System

Sessions reset every ~5 minutes. The agent rebuilds context from disk on every session:

1. Load `MEMORY.md` — durable facts (preferences, rules, growth history)
2. Load `memory/YYYY-MM-DD.md` — today's actual logs
3. Load `memory/YYYY-MM-DD-1.md` — yesterday (context only)

**Critical rule:** Feed counts and data must come from the disk files, never from session context.

**Midnight edge case:** Feeds at 02:30–08:59 WIB belong to the calendar date of the WIB time, not the UTC date. Always verify with `session_status` when logging late-night/early-morning feeds.

### Skills

Skills live in `workspace/skills/` and are self-contained instruction modules:

| Skill | Purpose |
|-------|---------|
| `smart-parenting-orchestrator` | Routes queries to optimal AI model based on language (ID/EN), complexity, API health |
| `baby-cry-detector` | Analyzes baby cry audio (WAV/MP3) or text descriptions to classify cry type |
| `baby-audio-transcribe` | Transcribes baby-related audio |
| `whatsapp-chats` / `whatsapp-image-send` / `whatsapp-styler` | WhatsApp delivery utilities |
| `url-shortener` | URL shortening |

Each skill has `SKILL.md` (metadata + instructions) and optionally `config.yaml`, `scripts/`, `references/`.

### Model Routing

The smart-parenting-orchestrator selects models based on:
- **Language**: Indonesian → Claude Opus/Sonnet primary, Gemini/GPT fallback; English → Claude primary, GPT fallback
- **API health**: Falls back through the pool if a model is unavailable
- **Safety escalation**: Critical topics always route to Claude Opus

API credentials are stored in `agents/main/agent/auth-profiles.json`.

### Channels & Gateway

- **Channel**: WhatsApp, private group `120363424585447477@g.us`
- **Allowed senders**: `+6289602896424` (Hawari), `+6281233705379` (Mila)
- **Gateway**: Local HTTP on `:18789`, LAN-bound
- **Control UI**: `http://localhost:18789`

### Cron Jobs

Feed reminders (T-30/T-15/T-5), morning summaries (06:00 WIB), evening summaries (21:00 WIB), and weekly weight prompts (Sun 09:00 WIB) are persisted as cron jobs in `cron/` so they survive session resets.

## Input Format Reference

| Parent types | Meaning |
|-------------|---------|
| `Nenen 20 menit` | DBF, 20 min |
| `ASIP 80ml jam 14` | Pumped BM, 80ml at 14:00 |
| `Sufor 60ml` | Formula, 60ml |
| `Timbang 3500 gram` / `BB 3.5 kg` | Weight log |
| `Pipis` | Wet diaper |
| `Pup kuning` | Bowel movement + color |
| `Summary hari ini` | On-demand daily summary |

## Maintenance

```bash
# Clean up failed delivery queue (items older than 7 days)
bash delivery-queue/cleanup-failed.sh 7

# View today's memory log
cat workspace/memory/$(date +%Y-%m-%d).md

# Backup workspace memory
cp -r workspace/memory workspace/memory.backup.$(date +%Y%m%d)
```
