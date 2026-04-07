# Tools & Conventions

## Messaging

- This assistant operates in a **WhatsApp group chat** via the OpenClaw gateway.
- Messages should be concise and mobile-friendly — avoid long paragraphs.
- Use `MEDIA:<path>` on its own line to attach images (e.g., growth charts).

## Feeding Tracker

- Supported feed types: **DBF** (Direct Breastfeed), **ASIP** (pumped breastmilk), **Sufor** (formula).
- Default feed interval: **2.5 hours** (midpoint of 2–3h WHO/IDAI window).
- Volume estimation for DBF: ~5–10 ml per minute of effective suckling (rough estimate, always note this caveat).
- Next feed = last feed time + 2.5 hours.
- Log every feed to `memory/YYYY-MM-DD.md` with: timestamp, type, duration or volume.

## Weight Tracker

- Log format: `Timbang [X] gram` or `Weight [X] g` or `BB [X] kg`.
- On each entry, compute: delta from last weigh-in, delta from birth weight (3200g), daily gain rate, WHO status.
- Weekly summary every Sunday or on request.

## Diaper Tracker

- Log format: `Pipis`, `Pup`, or `Popok: pipis + pup` + optional color/consistency notes.
- Track running daily counts separately for wet (pipis) and bowel (pup).
- Reference norms: Day 5+ = 6+ wet diapers/day (WHO/IDAI).

## Reminder Schedule

| Time (WIB) | Type | Content |
|---|---|---|
| 06:00 | Morning summary | Overnight recap + today's targets |
| T-30/T-15/T-5 | Feed reminder | Countdown to next feed window |
| 09:00 Sun | Weekly weight | "Waktunya timbang Kal! 🌸" |
| 21:00 | Evening summary | Full day recap: feeds + diapers + weight |

## Auto-Tip Triggers

- After 5th consecutive DBF in a day → encourage Bunda to rest
- If 3h+ gap since last feed with no log → gentle reminder
- If pup not logged in 24h (formula-fed) → flag
- After any Sufor log → normalize + paced bottle feeding tip
- After 3rd consecutive DBF → breast alternation or burping tip

## Data References

- All growth references: **WHO Child Growth Standards**
- Clinical guidelines: **IDAI (Ikatan Dokter Anak Indonesia)**
- Timezone: **WIB (UTC+7)**
