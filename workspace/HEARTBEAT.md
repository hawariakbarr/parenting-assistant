# Heartbeat Checklist

On each heartbeat run, check the following. Only send a message if action is needed — otherwise reply HEARTBEAT_OK.

## 1. Feed Gap Check
- Read today's memory log (`memory/YYYY-MM-DD.md`).
- If the last logged feed was **3+ hours ago** and no new feed has been logged, send a gentle reminder:
  > "⏰ Pengingat: Kal mau minta minum — sudah lebih dari 3 jam dari feed terakhir ya!"

## 2. Diaper Count Check (after 17:00 WIB only)
- Count today's wet diaper (pipis) logs.
- If **< 4 pipis by 17:00** (Day 5+), send a soft hydration note:
  > "Pipis Kal baru [X] hari ini. Kalau bisa, coba tingkatkan frekuensi menyusui ya 🌸"

## 3. Daily Summary Triggers
- At **06:00 WIB**: Send morning summary (overnight feeds recap + today's first targets).
- At **21:00 WIB**: Send evening summary (full day recap — feeds, diapers, weight if logged).

## 4. Weekly Weight Prompt (Sunday 09:00 WIB)
- If no weight has been logged this week, send:
  > "Waktunya timbang Kal! Bisa share beratnya hari ini? 🌸"

## Rules
- Keep heartbeat messages **short** (1–2 lines max).
- Never repeat a reminder that was already sent in the same heartbeat cycle.
- If nothing needs attention → reply `HEARTBEAT_OK`.
