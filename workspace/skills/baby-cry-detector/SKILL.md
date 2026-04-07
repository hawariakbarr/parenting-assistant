---
name: baby-cry-detector
description: Analyze and interpret baby crying sounds to determine what the baby needs. Use this skill whenever a parent sends an audio recording of their baby crying, asks what their baby's cry means, wants help understanding infant vocalizations, or mentions their baby is crying and wants to know why. Also triggers for questions about baby cry patterns, Dunstan Baby Language, infant sound analysis, colic detection, or any parenting context involving baby crying sounds. Works with audio files (WAV, MP3, M4A, OGG, FLAC) and can also provide guidance based on text descriptions of cry characteristics.
version: 1.0.0
metadata:
  openclaw:
    emoji: "👶"
    requires:
      bins:
        - python3
    homepage: https://github.com/openclaw/baby-cry-detector
---

# Baby Cry Detector & Interpreter

Analyze baby crying audio to determine what the infant needs, using acoustic analysis combined with established infant vocalization research (Dunstan Baby Language, pediatric cry classification, and acoustic feature analysis).

## Important Disclaimer

**Always include this at the start of any analysis response:**

> ⚠️ This analysis is for informational purposes only and does not replace professional medical advice. If your baby's cry sounds unusual, is high-pitched and inconsolable, or if you have any concerns about your baby's health, please consult your pediatrician immediately.

## When This Skill Activates

- User sends an audio file of a baby crying
- User asks "why is my baby crying?" or similar
- User describes their baby's cry characteristics and wants interpretation
- User asks about baby cry patterns, Dunstan Baby Language, or infant communication
- User wants to understand different types of baby cries
- User mentions colic, fussiness, or inconsolable crying

## Workflow

### Path A: Audio File Analysis

If the user provides an audio file (WAV, MP3, M4A, OGG, FLAC):

1. Copy the audio file to a working directory
2. Run the analysis script:
   ```bash
   {baseDir}/scripts/analyze_cry.py "<path-to-audio-file>"
   ```
3. The script outputs a JSON report with:
   - `fundamental_frequency_hz`: Average pitch (F0)
   - `f0_min_hz` / `f0_max_hz`: Pitch range
   - `intensity_db`: Average loudness
   - `cry_duration_sec`: Total cry duration
   - `pause_pattern`: Rhythm of cry-pause cycles
   - `energy_profile`: How energy changes over time
   - `onset_type`: Sudden vs gradual start
   - `classification`: Primary predicted cry type
   - `confidence`: Confidence score (0.0–1.0)
   - `secondary_classifications`: Other possible meanings ranked
   - `acoustic_flags`: Any unusual patterns detected

4. Interpret the JSON results using the classification guide below
5. Present findings to the user in a warm, reassuring, parent-friendly way

### Path B: Text Description Analysis

If the user describes the cry without audio:

1. Ask clarifying questions about:
   - What sound does it most resemble? (neh, eh, owh, heh, eairh)
   - Is it sudden and sharp, or gradual and whiny?
   - Is the baby's body tense or relaxed?
   - When did the crying start (after feeding? when put down? upon waking?)
   - How old is the baby?
   - Any physical cues (arched back, clenched fists, pulled-up legs, head turning)?
2. Use the classification reference in `{baseDir}/references/cry-guide.md` to interpret
3. Provide the analysis with the same warm, reassuring tone

## Cry Classification Guide (Quick Reference)

### The 5 Dunstan Baby Language Sounds (0–3 months, pre-cry stage)

| Sound | Meaning | Acoustic Signature | Physical Cues |
|-------|---------|-------------------|---------------|
| **Neh** | Hungry | Tongue pushes to palate, "N" onset, ~400–500 Hz F0, rhythmic repetition | Sucking reflex, clenched fists, rooting, lip smacking |
| **Owh** | Tired/Sleepy | Oval mouth, yawn-like, ~350–450 Hz F0, slower cadence, falling pitch | Yawning, eye rubbing, head turning without distress |
| **Heh** | Discomfort | Breathy "H" onset, ~400–550 Hz F0, intermittent whiny pattern | Squirming, skin flushing, fussing without arching |
| **Eairh** | Lower gas/colic | Strained "air" sound, ~450–600 Hz F0, intense with pauses, rising pitch | Legs pulled to stomach, arched back, face cramp |
| **Eh** | Needs burping | Short sharp "E" onset, ~400–500 Hz F0, repetitive bursts | Chest tension, squirming after feed |

### Acoustic-Based Classification (All Ages)

| Cry Type | F0 Range | Intensity | Pattern | Duration |
|----------|----------|-----------|---------|----------|
| **Hunger** | 400–500 Hz | Moderate, builds gradually | Rhythmic, repetitive, short pauses | Builds over 2–5 min |
| **Pain/Acute** | 500–900+ Hz | High, sudden peak | Sudden onset, long cry → long pause → long cry | Single loud burst then silence |
| **Tired/Overstimulated** | 350–450 Hz | Low-moderate, wavering | Irregular, whiny, rising-falling melody | Gradual increase, intermittent |
| **Discomfort** | 400–550 Hz | Moderate | Fussy, on-off, shifts with position | Variable, stops with relief |
| **Colic** | 500–800+ Hz | Very high, sustained | Intense, inconsolable, few pauses | Extended (>3 hours) |
| **Boredom/Attention** | 350–450 Hz | Low | Starts-stops, cooing mixed in | Stops when engaged |

### Red Flag Patterns (Always Recommend Doctor Visit)

- F0 consistently above 1000 Hz (hyperphonated cry) — may indicate neurological concern
- Extremely weak or nearly silent cry — may indicate respiratory or neurological issue
- Sudden change in cry character from baby's baseline
- Cry accompanied by fever, vomiting, or lethargy
- Inconsolable crying lasting >3 hours daily for >3 days/week for >3 weeks (Rule of 3s for colic)

## Response Format

Structure every response like this:

### 1. Reassurance First
Start with empathy. "I can hear your baby is telling you something! Let's figure out what they need."

### 2. Primary Interpretation
State the most likely meaning with confidence level. Explain the acoustic/behavioral reasoning.

### 3. What To Try
Give 2–3 specific, actionable suggestions for the identified cry type:
- **Hungry**: Offer breast/bottle, watch for rooting reflex
- **Tired**: Dim lights, gentle rocking, white noise, swaddle
- **Gas/Colic**: Bicycle legs, tummy time, gentle belly massage clockwise, burping positions
- **Discomfort**: Check diaper, check temperature (clothing layers), adjust position
- **Needs Burp**: Upright position, gentle back pats, over-shoulder burping
- **Pain**: Check for hair tourniquets, diaper rash, ear pulling, temperature
- **Boredom**: Face-to-face interaction, change of scenery, gentle talking/singing

### 4. Secondary Possibilities
Mention 1–2 alternative interpretations to consider if the first approach doesn't help.

### 5. When To Seek Help
Always end with gentle guidance on when to contact a pediatrician.

## Tone Guidelines

- Warm, calm, and supportive — never clinical or cold
- Acknowledge the parent's stress: "I know it's tough when your little one is upset"
- Use confident but not absolute language: "This most likely means..." not "This definitely means..."
- Normalize the experience: "All babies cry — it's their primary way of communicating with you"
- Culturally sensitive — avoid assumptions about feeding method, family structure, or caregiving arrangements
- If the user seems very distressed, acknowledge their feelings first before the analysis
- Support in both English and Bahasa Indonesia if the user writes in Indonesian

## Edge Cases

- **Multiple cry types detected**: Report the dominant type but note the mix. Babies sometimes express overlapping needs.
- **Very short audio clip (<2 seconds)**: Ask for a longer recording (10–30 seconds ideal). Note that pre-cry sounds can be very brief.
- **Background noise**: The script attempts noise filtering but may be less accurate. Note reduced confidence.
- **Older baby (>6 months)**: Dunstan pre-cry sounds become less distinct. Rely more on acoustic patterns and context.
- **Audio quality too poor**: Be honest about limitations. Fall back to text-based questioning.

## For Deeper Reference

Read `{baseDir}/references/cry-guide.md` for:
- Detailed acoustic analysis methodology
- Age-specific cry development milestones
- Extended soothing techniques by cry type
- Research citations and evidence basis
- Physical cue interpretation guide
