---
name: baby-audio-transcribe
description: Free speech-to-text transcription using Gemini API. Use when transcribing audio files (voice memos, recordings) to text. Supports Indonesian and English. Ideal for transcribing parenting voice logs, baby monitor recordings, or consultation notes. Triggers on "transcribe audio", "voice to text", "convert audio to text", "transkripsi audio".
---

# Baby Audio Transcribe

Free speech-to-text transcription using the Gemini API (already configured).

## Quick Start

```bash
# Transcribe audio file
{baseDir}/scripts/transcribe.sh /path/to/audio.wav

# Or with any format (auto-converts)
{baseDir}/scripts/transcribe.sh /path/to/audio.ogg
{baseDir}/scripts/transcribe.sh /path/to/audio.mp3
```

## Supported Formats

- WAV (recommended)
- OGG, MP3, M4A, FLAC (auto-converted via ffmpeg)

## Use Cases for Parents

1. **Voice memo → feeding log**: Record "Kal nenen 20 menit jam 2 siang" → transcribe → auto-log
2. **Pediatrician consultation**: Record appointment → transcribe for reference
3. **Daily notes**: Quick voice notes about baby's behavior/milestones

## Output

- Transcription displayed in terminal
- Also saved to `<input>.txt` in same directory

## Notes

- Uses your existing GEMINI_API_KEY (free tier)
- Supports Indonesian and English automatically
- No additional setup needed
