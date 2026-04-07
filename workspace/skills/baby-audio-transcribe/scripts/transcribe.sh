#!/bin/bash
# Baby Audio Transcribe - Uses Gemini via summarize CLI
# Free transcription using your existing GEMINI_API_KEY

set -e

AUDIO_FILE="$1"
LANG="${2:-auto}"

if [ -z "$AUDIO_FILE" ]; then
    echo "Usage: transcribe.sh <audio-file> [language]"
    echo ""
    echo "Examples:"
    echo "  transcribe.sh voice_memo.wav"
    echo "  transcribe.sh recording.ogg id"
    echo "  transcribe.sh consultation.mp3 en"
    exit 1
fi

if [ ! -f "$AUDIO_FILE" ]; then
    echo "Error: File not found: $AUDIO_FILE"
    exit 1
fi

# Set GEMINI_API_KEY if not already set
if [ -z "$GEMINI_API_KEY" ]; then
    export GEMINI_API_KEY="AIzaSyBGq8p_rLmtrNpbM6uFrb5-Ul-6HCiVAjU"
fi

# Convert to WAV if needed (for best results)
TEMP_WAV=""
case "$AUDIO_FILE" in
    *.wav|*.WAV)
        INPUT_FILE="$AUDIO_FILE"
        ;;
    *)
        TEMP_WAV="/tmp/transcribe_$(date +%s).wav"
        ffmpeg -i "$AUDIO_FILE" -ar 16000 -ac 1 "$TEMP_WAV" -y 2>/dev/null
        INPUT_FILE="$TEMP_WAV"
        ;;
esac

# Transcribe using summarize CLI with Gemini
echo "Transcribing: $AUDIO_FILE"
RESULT=$(summarize "$INPUT_FILE" --extract 2>&1)

# Clean up temp file
if [ -n "$TEMP_WAV" ] && [ -f "$TEMP_WAV" ]; then
    rm -f "$TEMP_WAV"
fi

# Output result
echo ""
echo "=== Transcription ==="
echo "$RESULT"

# Save to file
OUTPUT_FILE="${AUDIO_FILE%.*}.txt"
echo "$RESULT" > "$OUTPUT_FILE"
echo ""
echo "Saved to: $OUTPUT_FILE"
