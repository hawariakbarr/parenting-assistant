# Session Reset Protocol (v2.1)

## Context: Sessions Reset Every 5 Minutes

With frequent resets, **disk files are the only reliable source of truth**. Session memory cannot be trusted.

---

## MANDATORY STARTUP SEQUENCE

Every new session MUST execute this:

### Step 1: Load Durable Memory (NON-NEGOTIABLE)
```bash
# Read in this order:
1. MEMORY.md → All permanent facts (parents, preferences, rules)
2. memory/YYYY-MM-DD.md → TODAY's feeds/diapers/weights
3. memory/YYYY-MM-DD-1.md → YESTERDAY's data (context only)
```

### Step 2: Verify Baby Status
```
Current date: YYYY-MM-DD
Current age: [Calculate from 9 Mar 2026 birth date]
Last feed: [Read from memory/YYYY-MM-DD.md]
Today's feed count: [Read from memory/YYYY-MM-DD.md]
Last weight: [Read from MEMORY.md]
```

### Step 3: Await Input
```
Parent sends: "08.40 90ml asip"
→ Parse input
→ Cross-check against today's memory file
→ Log to memory/YYYY-MM-DD.md (in chronological order)
→ Create cron reminders (persist across resets)
→ Reply with confirmation (feed count from FILE)
```

---

## When Processing Feed/Diaper/Weight Logs

### ALWAYS READ FROM DISK
- ❌ Never trust "I logged 3 feeds earlier in this session"
- ✅ Always read memory/YYYY-MM-DD.md from disk
- ✅ Always count feeds from the file, not memory

### ALWAYS VERIFY CHRONOLOGICAL ORDER
```
Before logging new entry:
1. Load today's file
2. Check last entry time
3. Ensure new entry > last entry time (chronologically forward)
4. Insert in correct order (not always at end!)
5. Re-number feeds sequentially
```

### ALWAYS ECHO BACK FROM FILE
```
✅ CORRECT:
"✅ LOGGED: 09:10 — Sufor 30ml
Today's feed count: 4 [verified from memory/2026-03-27.md]
Next feed window: 11:40–12:40 WIB"

❌ WRONG:
"✅ LOGGED: 09:10 — Sufor 30ml
Today's feed count: 4 [I remember from earlier]"
```

---

## Cron Reminders (Survive Resets)

Cron jobs **persist across session resets**. So:
- Create reminders once per feed (not repeated)
- Do NOT worry about reminders disappearing
- Verify reminders in `cron list` if unsure
- Reminders fire automatically to WhatsApp group

---

## Common Mistakes to Avoid

| ❌ WRONG | ✅ RIGHT |
|---------|---------|
| Trust session context from 4 minutes ago | Always re-read disk files |
| Assume yesterday's logs are in memory | Load yesterday's file explicitly |
| Skip verification when parent re-logs | Cross-check file even if parent repeats |
| Guess feed count | Count from actual file on disk |
| Log entry wherever (chronologically) | Insert in correct chronological position |

---

## Example: Processing a Feed After Reset

```
SESSION 1 (0–5 min):
  - Parent logs: "08.40 90ml asip"
  - I read memory/2026-03-27.md
  - I log feed ke-1
  - Session ends (5 min timeout)

SESSION 2 (5–10 min):
  - Parent logs: "09.10 30ml sufor"
  - [SESSION 1 CONTEXT GONE]
  - ✅ I load MEMORY.md (parent info)
  - ✅ I load memory/2026-03-27.md from disk
  - ✅ I see feed ke-1 is already logged at 08:40
  - ✅ I insert feed ke-2 at 09:10 (chronologically correct)
  - ✅ I reply: "Today's feed count: 2 [from file]"
  - Session ends (5 min timeout)

SESSION 3 (10–15 min):
  - Parent logs: "09.50 dbf 20 menit"
  - [SESSION 2 CONTEXT GONE]
  - ✅ I load MEMORY.md
  - ✅ I load memory/2026-03-27.md from disk
  - ✅ I see 2 feeds already logged (08:40, 09:10)
  - ✅ I insert feed ke-3 at 09:50
  - ✅ I reply: "Today's feed count: 3 [from file]"
```

---

## Session Reset Resilience Checklist

- [ ] Every session loads MEMORY.md first
- [ ] Every session loads today's memory file from disk
- [ ] Every feed log reads file before processing
- [ ] Every feed log checks chronological order
- [ ] Every feed log re-counts from the actual file
- [ ] Every reply includes feed count from file (not memory)
- [ ] Cron reminders created once per feed (not repeated)
- [ ] Diaper logs checked against file
- [ ] Weight logs checked against file
- [ ] Emergency alerts always reference file data

---

*Last updated: 27 Mar 2026 (Session reset protocol v2.1)*
