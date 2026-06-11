import json
import argparse
import asyncio
import wave
import time
import glob
import re
import queue
import threading
from pathlib import Path
from datetime import datetime

from deepgram import DeepgramClient
from deepgram.core.events import EventType

# CONFIG

DEEPGRAM_API_KEY = "deepgram_api_key"

if not DEEPGRAM_API_KEY or DEEPGRAM_API_KEY in {"your_deepgram_api_key_here", "deepgram_api_key"}:
    raise ValueError("Please add your actual Deepgram API key in DEEPGRAM_API_KEY")

OUTPUT_DIR = "deepgram-nova-3"

DIGIT_WORDS = {
    "zero": "0", "oh": "0", "o": "0",
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9"
}

REPEAT_WORDS = {
    "double": 2,
    "triple": 3,
    "quadruple": 4,
    "quintuple": 5
}

NUMBER_WORDS = {
    "zero": 0, "oh": 0, "o": 0,
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90
}

MAGNITUDE_WORDS = {"hundred", "thousand", "lakh", "million"}

NUMERIC_CUE_WORDS = {
    "number", "numbers", "digit", "digits", "code", "otp", "pin", "passcode",
    "id", "account", "reference", "ticket", "invoice", "amount", "mobile",
    "phone", "contact", "serial", "zip", "postcode", "address", "plate",
    "card", "cvv", "expiry", "transaction"
}

NON_NUMERIC_FOLLOW_WORDS = {
    "time", "times", "day", "days", "week", "weeks", "month", "months",
    "year", "years", "person", "people", "thing", "things", "way"
}

# NUMERIC NORMALIZATION

def spoken_number_to_int(tokens):
    if not tokens:
        return None

    total = 0
    current = 0
    used = False

    for token in tokens:
        t = token.lower()

        if t == "and":
            continue
        elif t in NUMBER_WORDS:
            current += NUMBER_WORDS[t]
            used = True
        elif t == "hundred":
            if current == 0:
                current = 1
            current *= 100
            used = True
        elif t == "thousand":
            if current == 0:
                current = 1
            total += current * 1000
            current = 0
            used = True
        elif t == "lakh":
            if current == 0:
                current = 1
            total += current * 100000
            current = 0
            used = True
        elif t == "million":
            if current == 0:
                current = 1
            total += current * 1000000
            current = 0
            used = True
        else:
            return None

    return total + current if used else None


def tokenize_text(text):
    return re.findall(r"\d+|[A-Za-z]+|[^\w\s]", text)


def is_word_token(tok):
    return re.fullmatch(r"[A-Za-z]+", tok or "") is not None


def is_numericish_token(tok):
    if tok.isdigit():
        return True
    low = tok.lower()
    return low in DIGIT_WORDS or low in REPEAT_WORDS or low in NUMBER_WORDS or low in MAGNITUDE_WORDS


def has_numeric_context(tokens, start, end):
    left_window = tokens[max(0, start - 4):start]
    right_window = tokens[end:min(len(tokens), end + 4)]
    window = left_window + right_window

    for tok in window:
        low = tok.lower()
        if tok.isdigit():
            return True
        if low in NUMERIC_CUE_WORDS:
            return True
        if low in REPEAT_WORDS:
            return True

    if any(is_numericish_token(tok) for tok in left_window):
        return True
    if any(is_numericish_token(tok) for tok in right_window):
        return True

    return False


def should_convert_number_phrase(tokens, start, end):
    phrase = [t.lower() for t in tokens[start:end] if is_word_token(t)]
    if not phrase:
        return False

    if any(t in REPEAT_WORDS for t in phrase):
        return True

    if end < len(tokens):
        nxt = tokens[end].lower()
        if nxt in NON_NUMERIC_FOLLOW_WORDS and not has_numeric_context(tokens, start, end):
            return False

    if has_numeric_context(tokens, start, end):
        return True

    if len(phrase) >= 2:
        return True

    return False


def normalize_numeric_phrases_context_aware(text):
    if not text:
        return text

    tokens = tokenize_text(text)
    result = []
    i = 0

    while i < len(tokens):
        tok = tokens[i]
        low = tok.lower()

        if low in REPEAT_WORDS and i + 1 < len(tokens):
            if should_convert_number_phrase(tokens, i, min(i + 2, len(tokens))):
                nxt = tokens[i + 1].lower()
                repeat_count = REPEAT_WORDS[low]

                if nxt in DIGIT_WORDS:
                    result.append(DIGIT_WORDS[nxt] * repeat_count)
                    i += 2
                    continue

                if tokens[i + 1].isdigit() and len(tokens[i + 1]) == 1:
                    result.append(tokens[i + 1] * repeat_count)
                    i += 2
                    continue

        if tok.isdigit() and len(tok) == 1:
            digit_seq = [tok]
            j = i + 1

            while j < len(tokens):
                cur = tokens[j].lower()

                if tokens[j].isdigit() and len(tokens[j]) == 1:
                    digit_seq.append(tokens[j])
                    j += 1
                    continue

                if cur in DIGIT_WORDS:
                    digit_seq.append(DIGIT_WORDS[cur])
                    j += 1
                    continue

                if cur in REPEAT_WORDS and j + 1 < len(tokens):
                    nxt = tokens[j + 1].lower()
                    repeat_count = REPEAT_WORDS[cur]

                    if nxt in DIGIT_WORDS:
                        digit_seq.append(DIGIT_WORDS[nxt] * repeat_count)
                        j += 2
                        continue

                    if tokens[j + 1].isdigit() and len(tokens[j + 1]) == 1:
                        digit_seq.append(tokens[j + 1] * repeat_count)
                        j += 2
                        continue

                break

            if len(digit_seq) > 1:
                result.append("".join(digit_seq))
                i = j
                continue

        if low in NUMBER_WORDS or low in MAGNITUDE_WORDS or low == "and":
            j = i
            phrase_tokens = []

            while j < len(tokens):
                t = tokens[j].lower()
                if t in NUMBER_WORDS or t in MAGNITUDE_WORDS or t == "and":
                    phrase_tokens.append(t)
                    j += 1
                else:
                    break

            if should_convert_number_phrase(tokens, i, j):
                value = spoken_number_to_int(phrase_tokens)
                if value is not None:
                    result.append(str(value))
                    i = j
                    continue

        result.append(tok)
        i += 1

    text = " ".join(result)
    text = re.sub(r"\s+([,.;:?!])", r"\1", text)
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)
    text = re.sub(r"\s*-\s*", " - ", text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text

# AUDIO HELPERS
def get_wav_info(audio_path):
    # wave.open on Windows can treat pathlib.WindowsPath as a file-like object
    # and fail with: 'WindowsPath' object has no attribute 'read'.
    # Convert Path objects to string before opening.
    with wave.open(str(audio_path), "rb") as wf:
        sample_rate = wf.getframerate()
        channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        frames = wf.getnframes()
        duration = frames / sample_rate

        return {
            "sample_rate": sample_rate,
            "channels": channels,
            "sample_width": sample_width,
            "frames": frames,
            "duration": duration,
        }


def safe_get_transcript(message):
    try:
        if getattr(message, "type", None) != "Results":
            return None

        alternatives = message.channel.alternatives
        if not alternatives:
            return None

        raw_transcript = alternatives[0].transcript or ""
        if not raw_transcript.strip():
            return None

        confidence = getattr(alternatives[0], "confidence", 0)
        is_final = getattr(message, "is_final", False)
        speech_final = getattr(message, "speech_final", False)

        return raw_transcript, confidence, is_final, speech_final

    except Exception:
        return None


def create_result_state(source_name, audio_duration=0):
    return {
        "source_name": source_name,
        "transcripts": [],
        "latencies": [],
        "finalized_segments": [],
        "utterance_buffer": [],
        "start_time": time.time(),
        "first_byte_time": None,
        "first_response_time": None,
        "first_final_time": None,
        "first_chunk_sent_time": None,
        "response_count": 0,
        "audio_duration": audio_duration,
        "send_duration": None,
        "connection_time": None,
    }


def add_transcript_result(state, raw_transcript, confidence, is_final, speech_final):
    receive_time = time.time()

    if state["first_byte_time"] is None:
        state["first_byte_time"] = receive_time - state["start_time"]

    state["response_count"] += 1
    response_count = state["response_count"]

    transcript = normalize_numeric_phrases_context_aware(raw_transcript)

    latency_from_start = receive_time - state["start_time"]

    if state["first_chunk_sent_time"]:
        latency_from_first_chunk = receive_time - state["first_chunk_sent_time"]
    else:
        latency_from_first_chunk = 0

    if state["first_response_time"] is None and transcript:
        state["first_response_time"] = latency_from_start

    if state["first_final_time"] is None and is_final and transcript:
        state["first_final_time"] = latency_from_start

    result_info = {
        "response_num": response_count,
        "timestamp": latency_from_start,
        "latency_from_start": latency_from_start,
        "latency_from_first_chunk": latency_from_first_chunk,
        "is_final": is_final,
        "speech_final": speech_final,
        "raw_transcript": raw_transcript,
        "transcript": transcript,
        "confidence": confidence,
    }

    state["transcripts"].append(result_info)

    state["latencies"].append({
        "response_num": response_count,
        "latency_from_start_ms": latency_from_start * 1000,
        "latency_from_first_chunk_ms": latency_from_first_chunk * 1000,
        "is_final": is_final,
        "speech_final": speech_final,
        "words": len(transcript.split()),
        "char_count": len(transcript),
    })

    if is_final and transcript:
        state["utterance_buffer"].append(transcript)

    if speech_final and state["utterance_buffer"]:
        state["finalized_segments"].append(" ".join(state["utterance_buffer"]).strip())
        state["utterance_buffer"].clear()

    status = "FINAL" if is_final else "INTERIM"
    sf = " [speech_final]" if speech_final else ""
    preview = transcript[:100] + "..." if len(transcript) > 100 else transcript

    print(f"    [{status}]{sf} Resp {response_count}: {preview}")


def finalize_state(state):
    if state["utterance_buffer"]:
        state["finalized_segments"].append(" ".join(state["utterance_buffer"]).strip())
        state["utterance_buffer"].clear()

    total_time = time.time() - state["start_time"]

    return {
        "source_name": state["source_name"],
        "transcripts": state["transcripts"],
        "latencies": state["latencies"],
        "finalized_segments": state["finalized_segments"],
        "total_time": total_time,
        "audio_duration": state["audio_duration"] or 0,
        "timing_metrics": {
            "connection_time": state["connection_time"],
            "send_duration": state["send_duration"],
            "first_byte_time": state["first_byte_time"],
            "first_response_time": state["first_response_time"],
            "first_final_time": state["first_final_time"],
            "time_to_first_chunk": (
                state["first_chunk_sent_time"] - state["start_time"]
                if state["first_chunk_sent_time"]
                else None
            ),
        },
    }

# DEEPGRAM CONNECTION

def start_deepgram_connection(state, sample_rate, channels):
    client = DeepgramClient(api_key=DEEPGRAM_API_KEY)

    connection_start = time.time()

    # Deepgram SDK v6 listen.v1.connect returns a context manager.
    # Older SDK variants may return the connection directly.
    # This compatibility block supports both, and avoids passing unsupported args like no_delay.
    connection_obj = client.listen.v1.connect(
        model="nova-3",
        language="multi",
        punctuate=True,
        numerals=True,
        interim_results=True,
        endpointing=300,
        utterance_end_ms=1000,
        encoding="linear16",
        sample_rate=sample_rate,
        channels=channels,
    )

    if hasattr(connection_obj, "__enter__"):
        connection = connection_obj.__enter__()
        state["_connection_context"] = connection_obj
    else:
        connection = connection_obj
        state["_connection_context"] = None

    def on_open(_):
        print("  Deepgram connection opened")

    def on_message(message):
        parsed = safe_get_transcript(message)

        msg_type = getattr(message, "type", None)

        if msg_type == "UtteranceEnd":
            if state["utterance_buffer"]:
                state["finalized_segments"].append(" ".join(state["utterance_buffer"]).strip())
                state["utterance_buffer"].clear()
            print("    [EVENT] UtteranceEnd")
            return

        if msg_type == "SpeechStarted":
            print("  Speech started")
            return

        if parsed is None:
            return

        raw_transcript, confidence, is_final, speech_final = parsed
        add_transcript_result(
            state=state,
            raw_transcript=raw_transcript,
            confidence=confidence,
            is_final=is_final,
            speech_final=speech_final,
        )

    def on_close(_):
        print("  Deepgram connection closed")

    def on_error(error):
        print(f"  Deepgram error: {error}")

    connection.on(EventType.OPEN, on_open)
    connection.on(EventType.MESSAGE, on_message)
    connection.on(EventType.CLOSE, on_close)
    connection.on(EventType.ERROR, on_error)

    # IMPORTANT:
    # In this Deepgram SDK version, start_listening() can block while waiting
    # for messages. If we call it directly here, audio is never sent and
    # Deepgram closes the socket with NET-0001 timeout.
    # Run the listener in a background thread, then immediately return so
    # file/mic streaming can start sending audio.
    listener_thread = threading.Thread(
        target=connection.start_listening,
        name="deepgram-listener",
        daemon=True,
    )
    listener_thread.start()
    state["_listener_thread"] = listener_thread

    # Give the SDK a very short moment to start the socket listener.
    # Do not wait too long, otherwise Deepgram may timeout before audio is sent.
    time.sleep(0.2)

    state["connection_time"] = time.time() - connection_start

    return connection


def close_deepgram_context(state):
    """Close SDK context manager if this SDK version uses one."""
    ctx = state.get("_connection_context")
    if ctx is not None and hasattr(ctx, "__exit__"):
        try:
            ctx.__exit__(None, None, None)
        except Exception as e:
            print(f"  Warning: error closing Deepgram SDK context: {e}")

# FILE STREAMING

async def stream_wav_file(audio_path):
    audio_path = Path(audio_path)

    if not audio_path.exists():
        print(f"ERROR: File not found: {audio_path}")
        return None

    if audio_path.suffix.lower() != ".wav":
        print("ERROR: This streaming file mode expects WAV input")
        return None

    audio_info = get_wav_info(audio_path)

    print(
        f"  Audio: {audio_info['sample_rate']}Hz, "
        f"{audio_info['channels']}ch, "
        f"{audio_info['duration']:.2f}s"
    )

    state = create_result_state(
        source_name=audio_path.stem,
        audio_duration=audio_info["duration"],
    )

    connection = start_deepgram_connection(
        state=state,
        sample_rate=audio_info["sample_rate"],
        channels=audio_info["channels"],
    )

    print(f"  Connected in {state['connection_time']:.3f}s")
    print("  Sending WAV as realtime-paced stream...")

    send_start = time.time()

    try:
        with open(str(audio_path), "rb") as audio_file:
            audio_file.seek(44)

            bytes_per_sample = audio_info["sample_width"]
            channels = audio_info["channels"]
            sample_rate = audio_info["sample_rate"]
            bytes_per_second = sample_rate * channels * bytes_per_sample

            target_chunk_ms = 100
            chunk_size = int(bytes_per_second * (target_chunk_ms / 1000.0))
            chunk_size = max(chunk_size, 4096)

            while True:
                chunk = audio_file.read(chunk_size)
                if not chunk:
                    break

                connection.send_media(chunk)

                if state["first_chunk_sent_time"] is None:
                    state["first_chunk_sent_time"] = time.time()

                chunk_duration = len(chunk) / bytes_per_second
                await asyncio.sleep(chunk_duration)

        state["send_duration"] = time.time() - send_start

        connection.send_finalize()
        await asyncio.sleep(3)
        connection.send_close_stream()
        await asyncio.sleep(1)
        close_deepgram_context(state)

    except Exception as e:
        print(f"  File streaming error: {e}")
        import traceback
        traceback.print_exc()

    result = finalize_state(state)
    print(f"  Total processing time: {result['total_time']:.3f}s")

    return result

# MIC STREAMING

async def stream_microphone(duration=None):
    try:
        import sounddevice as sd
    except ImportError:
        print("ERROR: sounddevice is not installed")
        print("Install it using: pip install sounddevice")
        return None

    sample_rate = 16000
    channels = 1
    block_ms = 100
    block_size = int(sample_rate * block_ms / 1000)

    source_name = f"mic_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    state = create_result_state(source_name=source_name, audio_duration=duration or 0)

    connection = start_deepgram_connection(
        state=state,
        sample_rate=sample_rate,
        channels=channels,
    )

    print(f"  Connected in {state['connection_time']:.3f}s")
    print("  Streaming microphone audio...")
    print("  Press Ctrl+C to stop")

    audio_queue = queue.Queue()
    stop_time = time.time() + duration if duration else None
    send_start = time.time()

    def audio_callback(indata, frames, time_info, status):
        if status:
            print(f"  Mic status: {status}")
        audio_queue.put(bytes(indata))

    try:
        with sd.RawInputStream(
            samplerate=sample_rate,
            blocksize=block_size,
            channels=channels,
            dtype="int16",
            callback=audio_callback,
        ):
            while True:
                if stop_time and time.time() >= stop_time:
                    break

                try:
                    chunk = audio_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                connection.send_media(chunk)

                if state["first_chunk_sent_time"] is None:
                    state["first_chunk_sent_time"] = time.time()

                await asyncio.sleep(0)

    except KeyboardInterrupt:
        print("\n  Mic stopped by user")

    except Exception as e:
        print(f"  Mic streaming error: {e}")

    finally:
        state["send_duration"] = time.time() - send_start

        try:
            connection.send_finalize()
            await asyncio.sleep(2)
            connection.send_close_stream()
            await asyncio.sleep(1)
            close_deepgram_context(state)
        except Exception as e:
            print(f"  Error while closing Deepgram stream: {e}")

    result = finalize_state(state)
    print(f"  Total mic processing time: {result['total_time']:.3f}s")

    return result

# SAVE RESULTS

def save_results(result, output_dir):
    try:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        source_name = result["source_name"]

        transcript_file = output_path / f"{source_name}_transcript.txt"
        latency_file = output_path / f"{source_name}_latencies.json"

        if result.get("finalized_segments"):
            full_transcript = " ".join(result["finalized_segments"]).strip()
        else:
            final_transcripts = [
                t["transcript"]
                for t in result["transcripts"]
                if t["is_final"]
            ]
            full_transcript = " ".join(final_transcripts).strip()

        with open(transcript_file, "w", encoding="utf-8") as f:
            f.write(full_transcript)

        if result["latencies"]:
            avg_from_first_chunk = (
                sum(l["latency_from_first_chunk_ms"] for l in result["latencies"])
                / len(result["latencies"])
            )
            min_from_first_chunk = min(
                l["latency_from_first_chunk_ms"] for l in result["latencies"]
            )
            max_from_first_chunk = max(
                l["latency_from_first_chunk_ms"] for l in result["latencies"]
            )

            avg_from_start = (
                sum(l["latency_from_start_ms"] for l in result["latencies"])
                / len(result["latencies"])
            )
            min_from_start = min(l["latency_from_start_ms"] for l in result["latencies"])
            max_from_start = max(l["latency_from_start_ms"] for l in result["latencies"])
        else:
            avg_from_first_chunk = min_from_first_chunk = max_from_first_chunk = 0
            avg_from_start = min_from_start = max_from_start = 0

        latency_data = {
            "source_name": result["source_name"],
            "audio_duration_sec": result["audio_duration"],
            "total_processing_time_sec": result["total_time"],
            "timestamp": datetime.now().isoformat(),
            "model": "nova-3",
            "language": "multi",
            "finalized_segments": result.get("finalized_segments", []),
            "timing_metrics": {
                "connection_time_sec": result["timing_metrics"]["connection_time"],
                "send_duration_sec": result["timing_metrics"]["send_duration"],
                "first_byte_latency_sec": result["timing_metrics"]["first_byte_time"],
                "first_response_latency_sec": result["timing_metrics"]["first_response_time"],
                "first_final_latency_sec": result["timing_metrics"]["first_final_time"],
                "time_to_first_chunk_sec": result["timing_metrics"]["time_to_first_chunk"],
            },
            "latencies": result["latencies"],
            "summary": {
                "total_responses": len(result["latencies"]),
                "final_responses": sum(1 for l in result["latencies"] if l["is_final"]),
                "speech_final_responses": sum(
                    1 for l in result["latencies"] if l.get("speech_final")
                ),
                "total_words": sum(l["words"] for l in result["latencies"]),
                "total_characters": sum(l["char_count"] for l in result["latencies"]),
                "avg_latency_from_start_ms": avg_from_start,
                "min_latency_from_start_ms": min_from_start,
                "max_latency_from_start_ms": max_from_start,
                "avg_latency_from_first_chunk_ms": avg_from_first_chunk,
                "min_latency_from_first_chunk_ms": min_from_first_chunk,
                "max_latency_from_first_chunk_ms": max_from_first_chunk,
            },
        }

        with open(latency_file, "w", encoding="utf-8") as f:
            json.dump(latency_data, f, indent=2, ensure_ascii=False)

        print(f"  Transcript saved to: {transcript_file}")
        print(f"  Latencies saved to: {latency_file}")
        print(f"  Words: {len(full_transcript.split())}")

        return transcript_file, latency_file

    except Exception as e:
        print(f"  Error saving results: {e}")
        import traceback
        traceback.print_exc()
        return None, None

# MAIN

async def run_file_mode(file_pattern, force=False):
    files = sorted(glob.glob(file_pattern))

    if not files:
        print(f"No files found for pattern: {file_pattern}")
        return

    print("=" * 70)
    print("Deepgram Nova-3 SDK Streaming - FILE MODE")
    print("=" * 70)
    print(f"Files found: {len(files)}")
    print(f"Output Directory: {OUTPUT_DIR}")
    print()

    skipped_count = 0
    processed_count = 0
    failed_count = 0

    for idx, audio_file in enumerate(files, 1):
        print("-" * 70)
        print(f"Processing [{idx}/{len(files)}]: {audio_file}")
        print("-" * 70)

        audio_name = Path(audio_file).stem
        transcript_file = Path(OUTPUT_DIR) / f"{audio_name}_transcript.txt"
        latency_file = Path(OUTPUT_DIR) / f"{audio_name}_latencies.json"

        if transcript_file.exists() and latency_file.exists() and not force:
            print("✓ SKIPPED - Already processed")
            print("  Use --force to reprocess this file")
            skipped_count += 1
            continue

        result = await stream_wav_file(audio_file)

        if result and result["transcripts"]:
            print(f"\n✓ SUCCESS: {audio_file}")
            save_results(result, OUTPUT_DIR)
            processed_count += 1
        else:
            print(f"\n✗ FAILED: {audio_file}")
            failed_count += 1

        print()

    print("=" * 70)
    print("File Mode Complete")
    print("=" * 70)
    print(f"Total files: {len(files)}")
    print(f"Processed: {processed_count}")
    print(f"Skipped: {skipped_count}")
    print(f"Failed: {failed_count}")
    print("=" * 70)


async def run_mic_mode(duration):
    print("=" * 70)
    print("Deepgram Nova-3 SDK Streaming - MIC MODE")
    print("=" * 70)
    print(f"Output Directory: {OUTPUT_DIR}")
    if duration:
        print(f"Duration: {duration} seconds")
    else:
        print("Duration: until Ctrl+C")
    print()

    result = await stream_microphone(duration=duration)

    if result and result["transcripts"]:
        print("\n✓ MIC TRANSCRIPTION SUCCESS")
        save_results(result, OUTPUT_DIR)
    else:
        print("\n✗ No mic transcription received")


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode",
        choices=["file", "mic"],
        required=True,
        help="Use file mode for WAV files or mic mode for microphone streaming",
    )

    parser.add_argument(
        "--file",
        default="audio/car*.wav",
        help="WAV file path or glob pattern for file mode",
    )

    parser.add_argument(
        "--duration",
        type=int,
        default=None,
        help="Mic recording duration in seconds. If not passed, runs until Ctrl+C",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Reprocess file even if transcript and latency outputs already exist",
    )

    return parser.parse_args()


async def main():
    args = parse_args()

    if args.mode == "file":
        await run_file_mode(args.file, force=args.force)

    elif args.mode == "mic":
        await run_mic_mode(args.duration)


if __name__ == "__main__":
    asyncio.run(main())





nohup python3 -u benchmark_maria_nemotron.py --only-file maria18 --no-download --realtime --segment-seconds 60 --receive-timeout 1800 --force --force-split > nemotron_maria18_60s.log 2>&1 &
