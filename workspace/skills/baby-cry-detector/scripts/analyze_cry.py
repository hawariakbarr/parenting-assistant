#!/root/.openclaw/venv/bin/python3
"""
Baby Cry Analyzer — Acoustic feature extraction and cry classification.

Analyzes audio recordings of infant cries to extract acoustic features
(fundamental frequency, intensity, rhythm, energy profile) and classifies
the cry type using rule-based heuristics grounded in pediatric research.

Dependencies: numpy, scipy, soundfile (sf)
Install: pip install numpy scipy soundfile

Usage:
    python3 analyze_cry.py <audio_file_path> [--format json|text] [--verbose]

Supported formats: WAV, FLAC, OGG, MP3 (MP3 requires additional codec)
"""

import sys
import os
import json
import argparse
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Dependency check & import
# ---------------------------------------------------------------------------

MISSING_DEPS = []

try:
    import numpy as np
except ImportError:
    MISSING_DEPS.append("numpy")

try:
    import soundfile as sf
except ImportError:
    MISSING_DEPS.append("soundfile")

try:
    from scipy import signal as scipy_signal
    from scipy.ndimage import uniform_filter1d
except ImportError:
    MISSING_DEPS.append("scipy")

if MISSING_DEPS:
    print(json.dumps({
        "error": "missing_dependencies",
        "message": f"Install required packages: pip install {' '.join(MISSING_DEPS)}",
        "missing": MISSING_DEPS
    }))
    sys.exit(1)


# ---------------------------------------------------------------------------
# Audio loading
# ---------------------------------------------------------------------------

def load_audio(filepath: str, target_sr: int = 16000) -> tuple:
    """Load audio file, convert to mono, resample to target_sr."""
    try:
        data, sr = sf.read(filepath, dtype="float64")
    except Exception as e:
        return None, None, f"Cannot read audio file: {e}"

    # Convert to mono
    if data.ndim > 1:
        data = np.mean(data, axis=1)

    # Resample if needed
    if sr != target_sr:
        num_samples = int(len(data) * target_sr / sr)
        data = scipy_signal.resample(data, num_samples)
        sr = target_sr

    # Normalize
    peak = np.max(np.abs(data))
    if peak > 0:
        data = data / peak

    return data, sr, None


# ---------------------------------------------------------------------------
# Fundamental frequency (F0) extraction via autocorrelation
# ---------------------------------------------------------------------------

def extract_f0_autocorrelation(
    audio: np.ndarray,
    sr: int,
    frame_len_ms: float = 30.0,
    hop_ms: float = 10.0,
    f0_min: float = 200.0,
    f0_max: float = 1500.0,
    voicing_threshold: float = 0.3,
) -> np.ndarray:
    """
    Extract F0 contour using autocorrelation method.
    Returns array of F0 values per frame (0.0 for unvoiced frames).
    """
    frame_len = int(sr * frame_len_ms / 1000)
    hop = int(sr * hop_ms / 1000)
    min_lag = int(sr / f0_max)
    max_lag = int(sr / f0_min)

    n_frames = max(1, (len(audio) - frame_len) // hop + 1)
    f0_contour = np.zeros(n_frames)

    window = np.hanning(frame_len)

    for i in range(n_frames):
        start = i * hop
        frame = audio[start : start + frame_len]
        if len(frame) < frame_len:
            break

        frame = frame * window

        # Autocorrelation via FFT
        n_fft = 2 ** int(np.ceil(np.log2(2 * frame_len)))
        fft_frame = np.fft.rfft(frame, n=n_fft)
        acf = np.fft.irfft(np.abs(fft_frame) ** 2)
        acf = acf[:frame_len]

        # Normalize
        if acf[0] > 0:
            acf = acf / acf[0]
        else:
            continue

        # Search for peak in valid lag range
        search_start = max(min_lag, 1)
        search_end = min(max_lag, len(acf) - 1)

        if search_start >= search_end:
            continue

        acf_segment = acf[search_start:search_end]
        if len(acf_segment) == 0:
            continue

        peak_idx = np.argmax(acf_segment)
        peak_val = acf_segment[peak_idx]

        if peak_val >= voicing_threshold:
            lag = search_start + peak_idx
            if lag > 0:
                f0_contour[i] = sr / lag

    return f0_contour


# ---------------------------------------------------------------------------
# Energy and intensity
# ---------------------------------------------------------------------------

def compute_energy_profile(
    audio: np.ndarray, sr: int, frame_ms: float = 30.0, hop_ms: float = 10.0
) -> np.ndarray:
    """Compute short-time energy (RMS) per frame."""
    frame_len = int(sr * frame_ms / 1000)
    hop = int(sr * hop_ms / 1000)
    n_frames = max(1, (len(audio) - frame_len) // hop + 1)
    energy = np.zeros(n_frames)

    for i in range(n_frames):
        start = i * hop
        frame = audio[start : start + frame_len]
        if len(frame) > 0:
            energy[i] = np.sqrt(np.mean(frame ** 2))

    return energy


def compute_intensity_db(energy: np.ndarray) -> float:
    """Convert mean RMS energy to dB (relative to 1.0 peak)."""
    mean_e = np.mean(energy[energy > 0]) if np.any(energy > 0) else 1e-10
    return float(20 * np.log10(max(mean_e, 1e-10)))


# ---------------------------------------------------------------------------
# Cry segmentation and rhythm analysis
# ---------------------------------------------------------------------------

def segment_cry_pauses(
    energy: np.ndarray, sr: int, hop_ms: float = 10.0, silence_threshold_ratio: float = 0.1
) -> dict:
    """
    Detect cry bouts and pauses based on energy envelope.
    Returns pause pattern metrics.
    """
    if len(energy) == 0:
        return {"cry_bouts": 0, "avg_cry_sec": 0, "avg_pause_sec": 0, "rhythm": "unknown"}

    threshold = np.max(energy) * silence_threshold_ratio
    is_cry = energy > threshold

    # Smooth to avoid micro-segmentation
    smoothed = uniform_filter1d(is_cry.astype(float), size=10) > 0.5

    # Find transitions
    transitions = np.diff(smoothed.astype(int))
    cry_starts = np.where(transitions == 1)[0]
    cry_ends = np.where(transitions == -1)[0]

    # Handle edge cases
    if smoothed[0]:
        cry_starts = np.concatenate([[0], cry_starts])
    if smoothed[-1]:
        cry_ends = np.concatenate([cry_ends, [len(smoothed) - 1]])

    n_bouts = min(len(cry_starts), len(cry_ends))
    if n_bouts == 0:
        return {"cry_bouts": 0, "avg_cry_sec": 0, "avg_pause_sec": 0, "rhythm": "unknown"}

    frame_sec = hop_ms / 1000.0
    cry_durations = [(cry_ends[i] - cry_starts[i]) * frame_sec for i in range(n_bouts)]
    avg_cry = np.mean(cry_durations)

    pause_durations = []
    for i in range(n_bouts - 1):
        pause = (cry_starts[i + 1] - cry_ends[i]) * frame_sec
        pause_durations.append(pause)
    avg_pause = np.mean(pause_durations) if pause_durations else 0

    # Determine rhythm
    if n_bouts <= 1:
        rhythm = "single_burst"
    elif avg_pause < 0.5:
        rhythm = "continuous"
    elif 0.5 <= avg_pause < 2.0 and np.std(cry_durations) / (avg_cry + 1e-6) < 0.4:
        rhythm = "rhythmic_repetitive"
    elif avg_pause > 3.0:
        rhythm = "intermittent_with_long_pauses"
    else:
        rhythm = "irregular"

    return {
        "cry_bouts": int(n_bouts),
        "avg_cry_sec": round(avg_cry, 2),
        "avg_pause_sec": round(avg_pause, 2),
        "rhythm": rhythm,
    }


# ---------------------------------------------------------------------------
# Onset detection
# ---------------------------------------------------------------------------

def detect_onset_type(energy: np.ndarray) -> str:
    """Classify whether cry onset is sudden or gradual."""
    if len(energy) < 10:
        return "unknown"

    # Look at first 20% of the signal
    onset_region = energy[: max(1, len(energy) // 5)]
    if len(onset_region) < 3:
        return "unknown"

    max_energy = np.max(energy)
    if max_energy == 0:
        return "unknown"

    # Time to reach 80% of peak
    threshold_80 = 0.8 * max_energy
    reached_idx = np.where(energy >= threshold_80)[0]
    if len(reached_idx) == 0:
        return "gradual"

    rise_fraction = reached_idx[0] / len(energy)
    if rise_fraction < 0.05:
        return "sudden"
    elif rise_fraction < 0.2:
        return "moderately_fast"
    else:
        return "gradual"


# ---------------------------------------------------------------------------
# Energy trajectory classification
# ---------------------------------------------------------------------------

def classify_energy_trajectory(energy: np.ndarray) -> str:
    """Classify overall energy trajectory: building, steady, fading, fluctuating."""
    if len(energy) < 4:
        return "too_short"

    thirds = np.array_split(energy, 3)
    means = [np.mean(t) for t in thirds]

    if means[2] > means[0] * 1.5:
        return "building"
    elif means[0] > means[2] * 1.5:
        return "fading"
    elif max(means) / (min(means) + 1e-10) < 1.3:
        return "steady"
    else:
        return "fluctuating"


# ---------------------------------------------------------------------------
# Cry type classification (rule-based)
# ---------------------------------------------------------------------------

CRY_TYPES = {
    "hungry": {
        "f0_range": (380, 520),
        "onset": ["gradual", "moderately_fast"],
        "rhythm": ["rhythmic_repetitive"],
        "energy_trajectory": ["building"],
        "intensity": "moderate",
    },
    "pain": {
        "f0_range": (500, 1200),
        "onset": ["sudden"],
        "rhythm": ["single_burst", "intermittent_with_long_pauses"],
        "energy_trajectory": ["steady", "fading"],
        "intensity": "high",
    },
    "tired": {
        "f0_range": (330, 460),
        "onset": ["gradual"],
        "rhythm": ["irregular", "intermittent_with_long_pauses"],
        "energy_trajectory": ["fluctuating", "building"],
        "intensity": "low",
    },
    "discomfort": {
        "f0_range": (380, 560),
        "onset": ["gradual", "moderately_fast"],
        "rhythm": ["irregular", "rhythmic_repetitive"],
        "energy_trajectory": ["fluctuating", "steady"],
        "intensity": "moderate",
    },
    "gas_colic": {
        "f0_range": (440, 800),
        "onset": ["sudden", "moderately_fast"],
        "rhythm": ["continuous", "rhythmic_repetitive"],
        "energy_trajectory": ["steady", "building"],
        "intensity": "high",
    },
    "needs_burp": {
        "f0_range": (380, 520),
        "onset": ["moderately_fast"],
        "rhythm": ["rhythmic_repetitive", "irregular"],
        "energy_trajectory": ["fluctuating"],
        "intensity": "moderate",
    },
    "boredom_attention": {
        "f0_range": (330, 460),
        "onset": ["gradual"],
        "rhythm": ["irregular", "intermittent_with_long_pauses"],
        "energy_trajectory": ["fluctuating", "fading"],
        "intensity": "low",
    },
}


def classify_cry(
    f0_mean: float,
    f0_max: float,
    onset: str,
    rhythm: str,
    trajectory: str,
    intensity_db: float,
) -> list:
    """
    Score each cry type and return sorted classifications.
    Returns list of (type, confidence) tuples, highest confidence first.
    """
    scores = {}

    # Intensity classification
    if intensity_db > -8:
        intensity_class = "high"
    elif intensity_db > -15:
        intensity_class = "moderate"
    else:
        intensity_class = "low"

    for cry_type, profile in CRY_TYPES.items():
        score = 0.0
        max_possible = 5.0

        # F0 match (0–1.5 points)
        f0_low, f0_high = profile["f0_range"]
        if f0_low <= f0_mean <= f0_high:
            score += 1.5
        elif f0_mean < f0_low:
            dist = (f0_low - f0_mean) / f0_low
            score += max(0, 1.5 - dist * 3)
        else:
            dist = (f0_mean - f0_high) / f0_high
            score += max(0, 1.5 - dist * 3)

        # Onset match (0–1 point)
        if onset in profile["onset"]:
            score += 1.0
        elif onset == "unknown":
            score += 0.3

        # Rhythm match (0–1 point)
        if rhythm in profile["rhythm"]:
            score += 1.0
        elif rhythm == "unknown":
            score += 0.3

        # Trajectory match (0–0.75 points)
        if trajectory in profile["energy_trajectory"]:
            score += 0.75
        elif trajectory == "too_short":
            score += 0.2

        # Intensity match (0–0.75 points)
        if intensity_class == profile["intensity"]:
            score += 0.75
        elif (
            (intensity_class == "moderate" and profile["intensity"] in ("low", "high"))
            or (intensity_class in ("low", "high") and profile["intensity"] == "moderate")
        ):
            score += 0.25

        scores[cry_type] = round(score / max_possible, 3)

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_scores


# ---------------------------------------------------------------------------
# Flag unusual patterns
# ---------------------------------------------------------------------------

def check_acoustic_flags(f0_contour: np.ndarray, f0_mean: float, f0_max_val: float) -> list:
    """Check for acoustic red flags."""
    flags = []

    if f0_max_val > 1000:
        flags.append({
            "flag": "hyperphonated_cry",
            "severity": "high",
            "detail": (
                f"Maximum F0 reached {f0_max_val:.0f} Hz. Cries consistently above 1000 Hz "
                "can indicate neurological or physiological concerns. "
                "Please consult your pediatrician."
            ),
        })

    if f0_mean > 0 and f0_mean < 250:
        flags.append({
            "flag": "unusually_low_pitch",
            "severity": "medium",
            "detail": (
                f"Average F0 is {f0_mean:.0f} Hz, which is below typical infant range (350–550 Hz). "
                "This could indicate a very weak cry. Monitor closely."
            ),
        })

    voiced = f0_contour[f0_contour > 0]
    if len(voiced) > 10:
        jitter = np.mean(np.abs(np.diff(voiced))) / (np.mean(voiced) + 1e-6)
        if jitter > 0.15:
            flags.append({
                "flag": "high_pitch_instability",
                "severity": "medium",
                "detail": (
                    f"Pitch jitter is {jitter:.2%}, indicating unstable vocalization. "
                    "This can be normal during intense crying but may warrant monitoring."
                ),
            })

    return flags


# ---------------------------------------------------------------------------
# Main analysis pipeline
# ---------------------------------------------------------------------------

def analyze_cry_audio(filepath: str, verbose: bool = False) -> dict:
    """Full analysis pipeline. Returns structured result dict."""

    result = {
        "file": os.path.basename(filepath),
        "status": "ok",
    }

    # Load
    audio, sr, err = load_audio(filepath)
    if err:
        return {"file": os.path.basename(filepath), "status": "error", "error": err}

    duration = len(audio) / sr
    result["audio_duration_sec"] = round(duration, 2)
    result["sample_rate_hz"] = sr

    if duration < 0.5:
        return {
            **result,
            "status": "error",
            "error": "Audio too short. Need at least 0.5 seconds. Ideally 10–30 seconds.",
        }

    if duration > 300:
        # Truncate to 5 minutes
        audio = audio[: sr * 300]
        result["note"] = "Audio truncated to 300 seconds for analysis."

    # F0 extraction
    f0_contour = extract_f0_autocorrelation(audio, sr)
    voiced = f0_contour[f0_contour > 0]

    if len(voiced) < 3:
        return {
            **result,
            "status": "warning",
            "warning": "Could not detect sufficient voiced (crying) segments. The recording may be mostly silence or background noise.",
            "suggestion": "Try recording when the baby is actively crying, holding the device 30–60 cm from the baby.",
        }

    f0_mean = float(np.mean(voiced))
    f0_median = float(np.median(voiced))
    f0_min = float(np.min(voiced))
    f0_max = float(np.max(voiced))
    f0_std = float(np.std(voiced))

    result["fundamental_frequency_hz"] = round(f0_mean, 1)
    result["f0_median_hz"] = round(f0_median, 1)
    result["f0_min_hz"] = round(f0_min, 1)
    result["f0_max_hz"] = round(f0_max, 1)
    result["f0_std_hz"] = round(f0_std, 1)

    # Energy
    energy = compute_energy_profile(audio, sr)
    intensity = compute_intensity_db(energy)
    result["intensity_db"] = round(intensity, 1)

    # Segmentation / rhythm
    pause_info = segment_cry_pauses(energy, sr)
    result["cry_bouts"] = pause_info["cry_bouts"]
    result["avg_cry_duration_sec"] = pause_info["avg_cry_sec"]
    result["avg_pause_duration_sec"] = pause_info["avg_pause_sec"]
    result["rhythm_pattern"] = pause_info["rhythm"]

    # Onset
    onset = detect_onset_type(energy)
    result["onset_type"] = onset

    # Energy trajectory
    trajectory = classify_energy_trajectory(energy)
    result["energy_trajectory"] = trajectory

    # Classification
    classifications = classify_cry(f0_mean, f0_max, onset, pause_info["rhythm"], trajectory, intensity)
    primary = classifications[0]
    result["classification"] = primary[0]
    result["confidence"] = round(primary[1], 3)
    result["secondary_classifications"] = [
        {"type": c[0], "confidence": round(c[1], 3)} for c in classifications[1:4]
    ]

    # Flags
    flags = check_acoustic_flags(f0_contour, f0_mean, f0_max)
    result["acoustic_flags"] = flags
    if flags:
        result["has_warnings"] = True

    # Confidence note
    if primary[1] < 0.4:
        result["confidence_note"] = (
            "Low confidence — the acoustic pattern does not strongly match any single cry type. "
            "Consider the baby's context (last feed time, sleep schedule, recent activities) for better interpretation."
        )
    elif primary[1] < 0.6:
        result["confidence_note"] = (
            "Moderate confidence — the pattern has some ambiguity. "
            "Check the secondary classifications as well."
        )

    if verbose:
        result["f0_contour_sample"] = [round(float(v), 1) for v in voiced[:50]]

    return result


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Analyze baby crying audio to determine what the infant needs."
    )
    parser.add_argument("audio_file", help="Path to audio file (WAV, MP3, FLAC, OGG)")
    parser.add_argument(
        "--format", choices=["json", "text"], default="json",
        help="Output format (default: json)"
    )
    parser.add_argument("--verbose", action="store_true", help="Include extra details")

    args = parser.parse_args()

    if not os.path.isfile(args.audio_file):
        print(json.dumps({"status": "error", "error": f"File not found: {args.audio_file}"}))
        sys.exit(1)

    result = analyze_cry_audio(args.audio_file, verbose=args.verbose)

    if args.format == "json":
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        # Human-readable text output
        print(f"=== Baby Cry Analysis: {result.get('file', 'unknown')} ===\n")

        if result.get("status") == "error":
            print(f"Error: {result.get('error', 'Unknown error')}")
            sys.exit(1)

        if result.get("status") == "warning":
            print(f"Warning: {result.get('warning', '')}")
            if result.get("suggestion"):
                print(f"Suggestion: {result['suggestion']}")
            sys.exit(0)

        print(f"Duration: {result.get('audio_duration_sec', 0):.1f} seconds")
        print(f"Average Pitch (F0): {result.get('fundamental_frequency_hz', 0):.1f} Hz")
        print(f"Pitch Range: {result.get('f0_min_hz', 0):.1f} – {result.get('f0_max_hz', 0):.1f} Hz")
        print(f"Intensity: {result.get('intensity_db', 0):.1f} dB")
        print(f"Cry Bouts: {result.get('cry_bouts', 0)}")
        print(f"Rhythm: {result.get('rhythm_pattern', 'unknown')}")
        print(f"Onset: {result.get('onset_type', 'unknown')}")
        print(f"Energy Trend: {result.get('energy_trajectory', 'unknown')}")
        print()

        classification = result.get("classification", "unknown")
        confidence = result.get("confidence", 0)
        label_map = {
            "hungry": "🍼 Hungry",
            "pain": "😢 Pain / Acute Distress",
            "tired": "😴 Tired / Sleepy",
            "discomfort": "😣 Discomfort (diaper, temperature, position)",
            "gas_colic": "💨 Gas / Colic",
            "needs_burp": "🫧 Needs Burping",
            "boredom_attention": "🧸 Boredom / Wants Attention",
        }
        print(f"Primary: {label_map.get(classification, classification)}")
        print(f"Confidence: {confidence:.0%}")

        secondaries = result.get("secondary_classifications", [])
        if secondaries:
            print("\nAlternative possibilities:")
            for s in secondaries[:3]:
                lbl = label_map.get(s["type"], s["type"])
                print(f"  - {lbl}: {s['confidence']:.0%}")

        flags = result.get("acoustic_flags", [])
        if flags:
            print("\n⚠️  ALERTS:")
            for f in flags:
                print(f"  [{f['severity'].upper()}] {f['flag']}: {f['detail']}")

        note = result.get("confidence_note")
        if note:
            print(f"\nNote: {note}")

        print("\n⚠️  Disclaimer: This is an informational tool, not a medical device.")
        print("   Always consult your pediatrician if you have concerns about your baby.")


if __name__ == "__main__":
    main()
