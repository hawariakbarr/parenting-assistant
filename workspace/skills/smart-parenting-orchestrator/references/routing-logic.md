# Routing Logic Explanation

## High-Level Flow

```
User Message
    ↓
1. Detect Language (Indonesian vs English)
    ↓
2. Check API Health (which models available)
    ↓
3. Detect Context (parenting? complexity?)
    ↓
4. Safety Check (critical keywords?)
    ↓
5. Apply Routing Rules
    ↓
6. Return Decision + Fallbacks
```

## Detailed Steps

### 1. Language Detection
- Scan message for keywords
- Match Indonesian vs English
- Cache result for 1 hour
- Default: English if no match

### 2. API Health Check
- Test each model API endpoint
- Cache health status for 60 seconds
- Mark unavailable if error
- Filter to healthy models only

### 3. Context Analysis
- Count parenting keywords
- Calculate complexity score (1-10)
- Detect emotional tone
- Identify safety concerns

### 4. Safety Assessment
- Scan for critical keywords
- Check for medical/mental health concerns
- Look for abuse/violence indicators
- Always escalate if found

### 5. Routing Decision
Apply rules based on:
- Language (Indonesian → Claude preferred)
- Parenting mode (Yes/No)
- Complexity score (1-10)
- Safety flag (Yes/No)

### 6. Output
Return structured decision:
```json
{
  "selected_model": "claude-opus-4-5",
  "fallback": "claude-sonnet-4-5",
  "language": "indonesian",
  "parenting": true,
  "complexity": 7,
  "safety": false,
  "cache_ttl": 5
}
```

## Complexity Scoring (UPDATED v2.2)

| Factor | Points |
|--------|--------|
| Base score for parenting | **2** |
| Base score (non-parenting) | 1 |
| Simple greeting (hai/hello/halo) | **-1** (reduce to 1) |
| Length (per 20 words) | +1 |
| Question count | +1 each |
| Multiple topics (conjunctions) | +1 per 2 |
| Safety concern | +3 |
| Multiple sentences | +1 |
| Data tracking (feed/weight/diaper logs) | **+2** |

**Result:** Min 1, Max 10

**NEW (27 Mar 2026):**
- Lowered **parenting base from 3 → 2** (allow Haiku for simple messages)
- Added **greeting penalty -1** (force Haiku for "hai", "hello", "halo")
- Data tracking still gets +2 bonus (Sonnet for accuracy)

**CHANGE LOG (26 Mar 2026):**
- Raised **parenting base score from 1 → 3** (force Sonnet for most parenting queries)
- Added **data tracking bonus +2** (feed/weight/diaper logs are parenting-critical)
- Raised **safety score from +2 → +3** (more aggressive escalation)

## Caching Strategy

**Session Cache (5 minutes):**
- Cache routing decision per session
- Reuse same model for same user
- Invalidate on: config change, model list change, TTL expired

**Language Cache (1 hour):**
- Avoid re-detecting same user's language
- Improves performance
- User can override if needed

## Examples

### Example 1: Kal Feed Log (NEW)

Input: "04.20 sufor 60 asi 30"

Analysis:
- Language: Indonesian (format shorthand)
- Parenting: Yes ✓
- Complexity: **5** (base 3 + data tracking +2)
- Safety: No

Decision:
- Model: **Claude Sonnet** ✓ (upgraded from Haiku!)
- Fallback: Claude Opus
- Cache: 5 minutes

### Example 2: Complex English with Safety

Input: "My 2-year-old has been saying she wants to hurt herself. 
I'm terrified and don't know what to do."

Analysis:
- Language: English
- Parenting: Yes
- Complexity: 9 (emotional + critical)
- Safety: YES (self-harm indication)

Decision:
- Model: Claude Opus (escalated for safety)
- Add: Crisis resources
- Message: Urge professional help
- Cache: No (reevaluate each time)

## Notes

- Safety escalation **overrides everything**
- Indonesian always prefers Claude models
- Cache reduces API calls but respects config changes
- Fallback chain ensures no complete failures
