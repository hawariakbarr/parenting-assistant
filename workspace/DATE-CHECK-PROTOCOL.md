# DATE CHECK PROTOCOL — Prevent Midnight Logging Errors

**MANDATORY before logging ANY feed/weight/diaper entry**

## Quick Checklist (Do This First!)

```
BEFORE LOGGING:
☐ Step 1: Run session_status to get current UTC time
☐ Step 2: Calculate WIB (UTC + 7 hours)
☐ Step 3: Ask: Is feed time < 10:00 WIB? 
   ☐ If YES → Ask Ibu/Ayah: "Ini feed jam berapa WIB? Tanggal berapa?"
   ☐ If NO → Proceed with logging
☐ Step 4: Verify correct file (YYYY-MM-DD.md) matches FEED DATE (not system date)
☐ Step 5: If file doesn't exist → CREATE IT before logging
☐ Step 6: Then log to correct file
```

## Why This Matters

**Problem (Happened 3+ times):**
- Feed at 02:30 WIB on 29 Mar = technically NEXT day
- But system date might be 28 Mar (UTC-based)
- Result: Logged to wrong daily file (2026-03-28.md instead of 2026-03-29.md)
- Data inconsistency across log files

**Solution:**
- **Use FEED TIME to determine file date**, not system clock
- **Early morning feeds (00:00–10:00 WIB) = next calendar day**
- **Always confirm with parent for edge cases**

## Examples

### Example 1: Feed at 02:30 WIB
```
Current: Sunday 29 Mar 2026, 02:16 AM UTC = 09:16 AM WIB (29 Mar)
Feed time logged: 02:30 WIB
Question: "Is this 02:30 AM on 29 Mar morning?"
Answer: "Yes, it's early morning 29 Mar"
File to use: 2026-03-29.md ✅
```

### Example 2: Feed at 06:30 WIB
```
Current: Sunday 29 Mar 2026
Feed time logged: 06:30 WIB
Question: "Is this 06:30 AM on 29 Mar morning?"
Answer: "Yes, just now"
File to use: 2026-03-29.md ✅
```

### Example 3: Feed at 23:50 WIB (previous night)
```
Current: Sunday 29 Mar 2026, 23:50 WIB
Feed time logged: 23:50 WIB
Question: "Is this today's feed?"
Answer: "Yes, just now on 29 Mar"
File to use: 2026-03-29.md ✅
```

## Golden Rule

🔑 **USE THE FEED TIME TO DETERMINE THE DATE, NOT THE SYSTEM CLOCK**

- If Ibu says "02:30 feed hari ini" → ask which date
- If uncertain → always ask parent to confirm
- Better to ask 3 times than log to wrong file once

## Implementation

**In AGENTS.md Step 7 (Response Format for Feed Logs):**
- Pre-check checklist added
- Midnight edge case handler documented
- Session_status verification mandatory

**In MEMORY.md Section 9:**
- Bug documented with symptoms
- Solution explained
- Prevention checklist created

---

**Last Updated:** 29 Mar 2026 | **Status:** ACTIVE | **Priority:** CRITICAL
