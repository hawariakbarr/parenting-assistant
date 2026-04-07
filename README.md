# Parenting Assistant with Openclaw🌸

A personal AI-powered parenting assistant running as a WhatsApp bot. Built for Hawari & Mila to monitor baby Kalana's daily health and growth.

## What It Does

- **Feed tracking** — Log DBF / ASIP / Sufor feeds, show next feed window, maintain daily counts
- **Weight tracking** — Record weigh-ins, compute deltas vs birth weight, assess against WHO/IDAI targets
- **Diaper tracking** — Log wet/bowel movements, track daily counts, flag hydration concerns
- **Proactive reminders** — Feed countdowns (T-30/T-15/T-5), morning/evening summaries, weekly weight prompts
- **Smart routing** — Routes queries to the optimal AI model based on language (ID/EN), complexity, and API health

## Architecture

```
openclaw/
├── openclaw.json            # Main config (agents, channels, gateway, plugins)
├── identity/                # Device identity & keypair
├── agents/main/
│   ├── agent/               # Agent config (models, auth profiles)
│   └── sessions/            # Conversation session logs
├── workspace/               # Agent memory & operational docs
│   ├── MEMORY.md            # Long-term durable memory (growth milestones, preferences)
│   ├── SOUL.md              # Persona & communication guidelines
│   ├── AGENTS.md            # Operating instructions
│   ├── TOOLS.md             # Tool conventions (feed/weight/diaper formats)
│   ├── QUICK_START.md       # Session reset protocol
│   ├── memory/              # Daily logs (YYYY-MM-DD.md per day)
│   └── skills/              # Installed skill modules
│       ├── smart-parenting-orchestrator/   # Intelligent model routing
│       ├── baby-cry-detector/              # Cry audio classification
│       ├── baby-audio-transcribe/          # Audio transcription
│       ├── url-shortener/                  # URL shortening utility
│       ├── whatsapp-chats/                 # Chat history access
│       ├── whatsapp-image-send/            # Image delivery
│       └── whatsapp-styler/               # Message formatting
├── flows/                   # Flow registry (SQLite)
├── cron/                    # Scheduled jobs (feed reminders, daily summaries)
├── delivery-queue/          # Outbound message queue
│   └── failed/              # Failed delivery attempts
├── devices/                 # Paired/pending device registry
└── logs/                    # System logs
```

## Channel

- **WhatsApp** — Private group "Kalana" (`xxxxxxxxxxxxx@g.us`)
- **Allowed senders:** Me (+6289xxxxxx) and My Wife (+62812xxxxxxxx)
- **Group policy:** Open (responds to all group messages)

## Gateway

Local HTTP gateway on port `18789`, LAN-bound. Control UI accessible at `http://localhost:18789`.

## AI Providers

| Provider | Usage |
|----------|-------|
| GitHub Copilot | Primary agent model |
| Anthropic | Claude models (Opus/Sonnet/Haiku) |
| OpenRouter | Qwen and fallback models |
| Google | Gemini models |

Model credentials are stored in `agents/main/agent/auth-profiles.json`.

## Memory System

The agent uses a two-tier file-based memory system:

- **Long-term** (`workspace/MEMORY.md`) — Growth milestones, parent preferences, family info
- **Daily logs** (`workspace/memory/YYYY-MM-DD.md`) — Per-day feeds, diapers, weight entries

Sessions reset every ~5 minutes; the agent rebuilds context from disk on each session start.

## Skills

Skills are self-contained instruction modules in `workspace/skills/`. Each skill has:
- `SKILL.md` — Metadata and documentation
- `config.yaml` — Configuration (where applicable)
- `scripts/` — Implementation scripts
- `references/` — Supporting documentation

## Reminder Schedule

| Time (WIB) | Trigger |
|------------|---------|
| 06:00 daily | Morning summary — overnight recap + day targets |
| T-30/15/5 min | Feed countdown reminders |
| 09:00 Sunday | Weekly weight prompt |
| 21:00 daily | Evening summary — feeds + diapers + weight |

## Security Notes

- Auth credentials are stored in `agents/main/agent/auth-profiles.json` — keep this file private and out of version control
- Device private key is stored in `identity/device.json` — do not share or expose
- Gateway auth token is in `openclaw.json` under `gateway.auth.token`
- Add all credential files to `.gitignore` before committing this directory to any repository
