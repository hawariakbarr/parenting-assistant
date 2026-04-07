# Parenting Assistant with OpenClaw 🌸

A personal AI assistant living in your WhatsApp group — tracks every feed, diaper, and weigh-in for your newborn, sends proactive reminders, and answers parenting questions in Bahasa Indonesia or English.

Built for Hawari & Mila, parents of Kalana (Kal), born 9 March 2026.

---

## Features

### 🍼 Feed Tracking

Log every feed in natural language. The bot confirms, calculates the next feed window, and keeps a running daily count.

```
Ayah: Nenen 20 menit
Bot:  ✅ DBF 20 menit, jam 14:00 🌸
      Next feed window: 16:30–17:30
      Feed ke-6 hari ini — on track!
```

Supported feed types:
| Type | Example input |
|------|--------------|
| Direct breastfeed (DBF) | `Nenen 20 menit` |
| Pumped breastmilk (ASIP) | `ASIP 80ml jam 14` |
| Formula (Sufor) | `Sufor 60ml` |

---

### ⚖️ Weight Tracking

Log a weigh-in and get instant delta from birth weight, daily gain rate, and WHO/IDAI status assessment.

```
Ayah: Timbang 3500 gram
Bot:  ⚖️ Berat Kal: 3.500g (+300g dari lahir)
      Daily gain: 25g/day ✅ (target WHO: 20–30g)
      Keep it up, Bunda! 💪
```

---

### 🧷 Diaper Tracking

Track wet and bowel movements. The bot flags if daily wet diaper count drops below the WHO minimum (6x/day).

```
Bunda: Pup kuning
Bot:   ✅ Pup kuning tercatat — ke-2 hari ini
       Warna normal 🌸

Bunda: Pipis
Bot:   ✅ Pipis ke-5 hari ini
       ⚠️ Target ≥6x/day — 1 lagi ya!
```

---

### 🔔 Proactive Reminders

The bot sends reminders automatically — no setup needed after the first feed is logged.

| Time (WIB) | What gets sent |
|------------|---------------|
| T-30 / T-15 / T-5 min | Feed countdown before next window |
| 06:00 daily | Morning summary — overnight recap + today's targets |
| 21:00 daily | Evening summary — full day: feeds, diapers, weight |
| 09:00 Sunday | Weekly weight prompt: "Waktunya timbang Kal! 🌸" |

---

### 👶 Baby Cry Detector

Send an audio recording of your baby crying and the bot analyses the sound to tell you what Kal likely needs.

```
[Audio sent]
Bot:  🔊 Analisis selesai!
      Kemungkinan besar: Lapar (confidence: 82%)
      Ciri: Rhythmic, ~450Hz, builds gradually

      Coba: Tawarkan minum dulu ya 🌸
      Kalau tidak berhenti setelah 5 menit,
      cek juga popok dan posisi.
```

Works with WAV, MP3, M4A, OGG. Also works if you just describe the cry in text.

---

### 📊 On-Demand Summaries

Ask for a recap any time.

```
Ayah: Summary hari ini
Bot:  📊 Ringkasan 7 Apr 2026 (Hari ke-29)

      🍼 Feeds: 8x | ~560ml (✅ target 555ml)
      🧷 Pipis: 7x ✅ | Pup: 2x ✅
      ⚖️ Berat terakhir: 3.700g (+500g dari lahir)

      Kal sedang tumbuh dengan baik! 🌸
```

---

### 🧠 Bilingual & Context-Aware

- Responds in whichever language you write in (ID or EN)
- Routes queries to the best available AI model (Claude, GPT, Gemini) based on language and complexity
- Falls back gracefully if a model is unavailable

---

## Setup

```bash
# 1. Copy and fill in your credentials
cp .env.example .env
nano .env

# 2. Bootstrap openclaw config files from .env
bash scripts/setup.sh

# 3. Start the daemon
pm2 start ecosystem.config.cjs && pm2 save

# 4. Link WhatsApp (first time only)
openclaw channels login --channel whatsapp --account default
```

> Re-run `bash scripts/setup.sh` any time you rotate API keys.

### Required credentials (`.env`)

| Variable | Where to get it |
|----------|----------------|
| `ANTHROPIC_API_KEY` | console.anthropic.com |
| `OPENROUTER_API_KEY` | openrouter.ai/keys |
| `GOOGLE_API_KEY` | console.cloud.google.com |
| `GITHUB_COPILOT_TOKEN` | github.com/settings/tokens |
| `GATEWAY_AUTH_TOKEN` | Any random string |
| `WHATSAPP_ALLOWED_FROM` | Phone numbers allowed to message the bot |

---

## PM2 Commands

```bash
pm2 start all          # Start
pm2 stop all           # Stop
pm2 restart all        # Restart
pm2 logs               # View logs
pm2 monit              # Live monitor
pm2 resurrect          # Restore after reboot
```

---

## How It Works

```
WhatsApp message
    ↓
OpenClaw gateway (:18789)
    ↓
Agent reads disk memory (MEMORY.md + today's log)
    ↓
Smart router selects best AI model
    ↓
Response sent back to WhatsApp group
```

Sessions reset every ~5 minutes. All data is persisted to disk so nothing is lost across resets:
- **Long-term memory** — `workspace/MEMORY.md` (growth history, preferences)
- **Daily logs** — `workspace/memory/YYYY-MM-DD.md` (feeds, diapers, weights per day)

---

## Architecture

```
~/.openclaw/
├── openclaw.json                # Master config: agents, channels, gateway, plugins
├── ecosystem.config.cjs         # PM2 service config (gateway on :18789)
├── .env                         # Credentials (gitignored — copy from .env.example)
├── scripts/setup.sh             # Bootstrap: reads .env → writes openclaw config files
├── identity/                    # Device keypair (ED25519, gitignored)
├── agents/main/
│   ├── agent/                   # auth-profiles.json, models.json (gitignored)
│   └── sessions/                # Conversation session JSONL logs
├── workspace/                   # Agent persona, instructions, and memory
│   ├── SOUL.md                  # Persona: tone, language, boundaries
│   ├── AGENTS.md                # Operating instructions: parsing rules, logging protocol
│   ├── TOOLS.md                 # Feed/weight/diaper format conventions
│   ├── MEMORY.md                # Long-term durable memory (gitignored)
│   ├── QUICK_START.md           # Session reset protocol
│   ├── memory/                  # Daily logs: one YYYY-MM-DD.md per day (gitignored)
│   └── skills/                  # Installed skill modules
├── flows/                       # Flow registry (SQLite)
├── cron/                        # Scheduled reminders (gitignored)
├── delivery-queue/              # Outbound message queue (gitignored)
└── logs/                        # System logs (gitignored)
```

---

## Skills

Skills are self-contained instruction modules in `workspace/skills/`. Each one activates automatically when a relevant message is received.

| Skill | What it does |
|-------|-------------|
| `smart-parenting-orchestrator` | Routes every message to the best available AI model based on language (ID/EN), query complexity, and API health |
| `baby-cry-detector` | Analyses baby cry audio (WAV/MP3/M4A/OGG) or text descriptions — classifies cry type and suggests response |
| `baby-audio-transcribe` | Transcribes baby-related audio messages |
| `whatsapp-image-send` | Sends growth charts and dashboard images to the group |
| `whatsapp-styler` | Formats outbound messages for WhatsApp readability |
| `url-shortener` | Shortens dashboard and report URLs before sending |

---

## Memory System

The agent has no persistent session state — every session starts cold. It rebuilds context entirely from disk:

```
Session start (every ~5 min)
    ↓
1. Load workspace/MEMORY.md        → family info, preferences, growth history
2. Load memory/YYYY-MM-DD.md       → today's feeds, diapers, weights
3. Load memory/YYYY-MM-DD-1.md     → yesterday (context only)
    ↓
Process message → update disk → reply
```

**Critical rule:** Feed counts and totals always come from the file, never from session context. This prevents duplicates and hallucinated counts across resets.

---

## Channel & Gateway

| Setting | Value |
|---------|-------|
| Channel | WhatsApp |
| Group | Private group "Kalana" |
| Allowed senders | Configurable via `WHATSAPP_ALLOWED_FROM` in `.env` |
| Gateway port | `18789` (LAN-bound) |
| Control UI | `http://localhost:18789` |
