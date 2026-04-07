# ⚡ Quick Start — Setiap Session Baru (5 Min Reset)

## LANGKAH 1: Load Memory (30 detik)
```
1. Baca: MEMORY.md
2. Baca: memory/YYYY-MM-DD.md (hari ini)
3. Baca: memory/YYYY-MM-DD-1.md (kemarin)
```

## LANGKAH 2: Compute Kal Status (30 detik)
```
✓ Usia Kal: [dari 9 Mar 2026]
✓ Today's feed count: [dari file]
✓ Last feed time: [dari file]
✓ Last weight: [dari MEMORY.md]
```

## LANGKAH 3: Terima Input + Process (1 menit)

### Feed Log
```
Input: "HH.MM type volume/duration"
→ Parse (ask if ambiguous)
→ Read memory file (verify last feed)
→ Insert chronologically
→ Create reminders (T-30, T-15, T-5)
→ Echo back with count from FILE
```

### Diaper Log
```
Input: "pipis" atau "pup [color]"
→ Read memory file
→ Add to count
→ Flag if <6 pipis/day
```

### Weight Log
```
Input: "Timbang X gram" atau "BB X kg"
→ Read memory file
→ Calculate delta from last + birth weight
→ Update MEMORY.md + daily file
```

## LANGKAH 4: Confirm to Parents
```
✅ LOGGED: [time] — [type] [volume]
Next feed window: [time range]
Today's count: [from file]
```

---

## 🚨 CRITICAL REMINDERS

| ⚠️ DO NOT | ✅ DO THIS |
|----------|-----------|
| Trust session memory | Read files every time |
| Skip chronological order | Always insert in order |
| Guess feed count | Count from actual file |
| Log without cross-check | Always verify against file |
| Repeat reminders | Create once per feed |

---

## 📁 File Locations
- **Durable memory:** `/root/.openclaw/workspace/MEMORY.md`
- **Today's log:** `/root/.openclaw/workspace/memory/2026-03-DD.md`
- **Rules:** `/root/.openclaw/workspace/AGENTS.md`
- **Preferences:** `/root/.openclaw/workspace/SOUL.md`

---

## 🕐 Current Context
- **Baby:** Kalana (Kal), born 9 Mar 2026 (hari ke-19 as of 27 Mar)
- **Parents:** Hawari (Ayah) + Mil (Ibu)
- **Location:** Cimahi, Jawa Barat
- **Timezone:** WIB (UTC+7)
- **Language:** Bahasa Indonesia (casual)

---

*Last updated: 27 Mar 2026 (v2.1)*
