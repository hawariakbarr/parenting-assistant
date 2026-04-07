# Daily Handoff Template

## Purpose
Every session restart, load this pattern to maintain continuity. Use actual data from disk files.

---

## 📋 Current Status (Load from Files)

**Date:** [YYYY-MM-DD]  
**Today's file:** `memory/YYYY-MM-DD.md`  
**Kal's age:** [DD] days (born 9 Mar 2026)

### Feeds Today (from file)
- Feed ke-1: [HH:MM] — [Type] [Volume]ml
- Feed ke-2: [HH:MM] — [Type] [Volume]ml
- Feed ke-3: [HH:MM] — [Type] [Volume]ml
- Feed ke-N: [HH:MM] — [Type] [Volume]ml

**Total so far:** [N] feeds, [VOLUME]ml

### Diapers Today (from file)
- Pipis: [N]x
- Pup: [N]x

### Weight (from MEMORY.md)
- Last weigh-in: [DATE] — [WEIGHT]g
- Gain rate: [RATE]g/day

### Next Action
- Next feed window: [HH:MM–HH:MM] WIB
- Upcoming milestones: [e.g., "Weekly weigh-in Saturday"]

---

## 🔄 Session Restart Checklist

Before processing any new input:

- [ ] Loaded MEMORY.md
- [ ] Loaded memory/YYYY-MM-DD.md (today)
- [ ] Loaded memory/YYYY-MM-DD-1.md (yesterday)
- [ ] Verified parent names (Ayah = Hawari, Ibu = Mil)
- [ ] Confirmed language (Bahasa Indonesia)
- [ ] Timezone set (WIB = UTC+7)
- [ ] Today's feed count verified from file
- [ ] Last feed time noted from file
- [ ] Ready to process new input

---

## Example Handoff (27 Mar 2026)

**Date:** 2026-03-27  
**Kal's age:** 19 days

### Feeds Today (as of 09:10)
1. 01:40 — Sufor 60ml
2. 04:20 — Sufor 60ml + ASIP 30ml
3. 08:40 — ASIP 90ml
4. 09:10 — Sufor 30ml

**Total:** 4 feeds, 270ml

### Diapers
- Pipis: (pending)
- Pup: (pending)

### Weight
- Last: 3,375g (23 Mar, hari ke-14)

### Next
- Next feed window: 06:50–07:50 WIB (from 04:20 feed)
- Reminders scheduled: T-30, T-15, T-5

---

## 💡 Why This Matters

With 5-minute session resets:
- **Session 1:** Load handoff, process 08:40 feed, create reminders
- **Session 2:** Load handoff, see 1 feed logged, process 09:10 feed
- **Session 3:** Load handoff, see 2 feeds logged, process next input
- **Session N:** Always accurate, no lost context, no duplicates

---

*Generate new handoff at the start of each session by reading disk files.*
