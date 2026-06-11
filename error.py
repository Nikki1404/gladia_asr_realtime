Nikita Verma suggest the changes as per the python sdk - 
 
https://github.com/deepgram/deepgram-python-sdk?tab=readme-ov-file#installation


i was asked to do this ..

similarly i have done numeric handling in this client so could you suggest  the changes as per the python sdk - (https://github.com/deepgram/deepgram-python-sdk?tab=readme-ov-file#installation)
 


this is my client 
import os
import json
import asyncio
import websockets
import wave
import time
import glob
import re
from pathlib import Path
from datetime import datetime

# =====================
# CONFIG
# =====================

DEEPGRAM_API_KEY = "5c6e335e937a1b8ded48e7ed2fba525f65b03315"

# Audio files to test
AUDIO_FILES = sorted(glob.glob("audio/car*.wav"))

# Output directory
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

# =====================
# NUMERIC NORMALIZATION
# =====================

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

# =====================
# AUDIO HELPERS
# =====================

def get_wav_info(audio_path):
    with wave.open(audio_path, 'rb') as wf:
        sample_rate = wf.getframerate()
        channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        frames = wf.getnframes()
        duration = frames / sample_rate

        return {
            'sample_rate': sample_rate,
            'channels': channels,
            'sample_width': sample_width,
            'frames': frames,
            'duration': duration
        }


def get_audio_info(audio_path):
    file_ext = Path(audio_path).suffix.lower()

    if file_ext == '.wav':
        return get_wav_info(audio_path)
    else:
        return {
            'format': file_ext[1:],
            'duration': None
        }

# =====================
# CORE WEBSOCKET LOGIC
# =====================

async def send_wav_realtime(ws, audio_path, audio_info, first_chunk_sent_ref):
    """
    Sends WAV audio in 'real-time' paced chunks.
    first_chunk_sent_ref is a one-element list used to store the timestamp of the first chunk.
    """
    try:
        with open(audio_path, 'rb') as audio_file:
            # Skip WAV header
            audio_file.seek(44)
            bytes_per_sample = audio_info['sample_width']
            channels = audio_info['channels']
            sample_rate = audio_info['sample_rate']
            bytes_per_second = sample_rate * channels * bytes_per_sample

            target_chunk_ms = 100
            chunk_size = int(bytes_per_second * (target_chunk_ms / 1000.0))
            chunk_size = max(chunk_size, 4096)

            while True:
                chunk = audio_file.read(chunk_size)
                if not chunk:
                    break

                await ws.send(chunk)

                if first_chunk_sent_ref[0] is None:
                    first_chunk_sent_ref[0] = time.time()

                chunk_duration = len(chunk) / bytes_per_second
                await asyncio.sleep(chunk_duration)

        # After sending all audio, tell Deepgram we're done
        await ws.send(json.dumps({"type": "CloseStream"}))

    except websockets.exceptions.ConnectionClosedError as e:
        print(f"  Sender: connection closed while sending: {e}")
    except Exception as e:
        print(f"  Sender error: {e}")


async def transcribe_audio_websocket(api_key, audio_path):
    audio_info = get_audio_info(audio_path)
    file_ext = Path(audio_path).suffix.lower()

    if file_ext != '.wav':
        print("  ✗ This realtime-paced version currently expects WAV input.")
        return None

    print(f"  Audio: {audio_info['sample_rate']}Hz, {audio_info['channels']}ch, {audio_info['duration']:.2f}s")

    # Start simple & robust; you can re-enable tweaks later
    params = (
        "model=nova-3&"
        "language=multi&"
        "punctuate=true&"
        "numerals=true&"
        "interim_results=true&"
        "endpointing=300&"
        "utterance_end_ms=1000&"
        "no_delay=true&"
        "encoding=linear16&"
        f"sample_rate={audio_info['sample_rate']}&"
        "channels=1"
    )

    ws_url = f"wss://api.deepgram.com/v1/listen?{params}"
    headers = {
        "Authorization": f"Token {api_key}"
    }

    transcripts = []
    latencies = []
    finalized_segments = []
    utterance_buffer = []

    start_time = time.time()
    audio_duration = audio_info.get('duration')

    first_byte_time = None
    first_response_time = None
    first_final_time = None
    connection_time = None
    send_duration = None
    first_chunk_sent_ref = [None]

    try:
        print("  Connecting to Deepgram WebSocket (Nova-3 realtime)...")
        async with websockets.connect(ws_url, additional_headers=headers) as ws:
            connection_time = time.time() - start_time
            print(f"  Connected in {connection_time:.3f}s")
            print("  Sending audio via paced realtime chunks...")

            send_start = time.time()

            async def receiver():
                nonlocal first_byte_time, first_response_time, first_final_time, audio_duration
                response_count = 0
                try:
                    async for message in ws:
                        receive_time = time.time()
                        response = json.loads(message)
                        msg_type = response.get("type")

                        if first_byte_time is None:
                            first_byte_time = receive_time - start_time

                        if msg_type == "Results":
                            response_count += 1

                            if 'channel' in response:
                                alternatives = response['channel'].get('alternatives', [])
                                if alternatives:
                                    raw_transcript = alternatives[0].get('transcript', '')
                                    transcript = normalize_numeric_phrases_context_aware(raw_transcript)
                                    confidence = alternatives[0].get('confidence', 0)
                                    is_final = response.get('is_final', False)
                                    speech_final = response.get('speech_final', False)

                                    latency_from_start = receive_time - start_time
                                    latency_from_send_start = receive_time - send_start
                                    if first_chunk_sent_ref[0]:
                                        latency_from_first_chunk = receive_time - first_chunk_sent_ref[0]
                                    else:
                                        latency_from_first_chunk = 0

                                    if first_response_time is None and transcript:
                                        first_response_time = latency_from_start
                                    if first_final_time is None and is_final and transcript:
                                        first_final_time = latency_from_start

                                    result_info = {
                                        'response_num': response_count,
                                        'timestamp': latency_from_start,
                                        'latency_from_start': latency_from_start,
                                        'latency_from_send_start': latency_from_send_start,
                                        'latency_from_first_chunk': latency_from_first_chunk,
                                        'is_final': is_final,
                                        'speech_final': speech_final,
                                        'raw_transcript': raw_transcript,
                                        'transcript': transcript,
                                        'confidence': confidence
                                    }

                                    if transcript:
                                        transcripts.append(result_info)
                                        latencies.append({
                                            'response_num': response_count,
                                            'latency_from_start_ms': latency_from_start * 1000,
                                            'latency_from_send_start_ms': latency_from_send_start * 1000,
                                            'latency_from_first_chunk_ms': latency_from_first_chunk * 1000,
                                            'is_final': is_final,
                                            'speech_final': speech_final,
                                            'words': len(transcript.split()),
                                            'char_count': len(transcript)
                                        })

                                    if is_final and transcript:
                                        utterance_buffer.append(transcript)

                                    if speech_final and utterance_buffer:
                                        finalized_segments.append(" ".join(utterance_buffer).strip())
                                        utterance_buffer.clear()

                                    status = "FINAL" if is_final else "INTERIM"
                                    sf = " [speech_final]" if speech_final else ""
                                    preview = transcript[:80] + "..." if len(transcript) > 80 else transcript
                                    if preview:
                                        print(f"    [{status}]{sf} Resp {response_count}: {preview}")

                        elif msg_type == "UtteranceEnd":
                            if utterance_buffer:
                                finalized_segments.append(" ".join(utterance_buffer).strip())
                                utterance_buffer.clear()
                            print("    [EVENT] UtteranceEnd")

                        elif msg_type == "Metadata":
                            print("  Metadata received")
                            if audio_duration is None and 'duration' in response:
                                audio_duration = response['duration']

                        elif msg_type == "SpeechStarted":
                            print("  Speech started")

                except websockets.exceptions.ConnectionClosedError as e:
                    print(f"  Receiver: connection closed by server: {e}")
                except Exception as e:
                    print(f"  Receiver error: {e}")

            receiver_task = asyncio.create_task(receiver())
            await send_wav_realtime(ws, audio_path, audio_info, first_chunk_sent_ref)
            send_end = time.time()
            send_duration = send_end - send_start

            # Wait a bit for remaining messages, then cancel receiver if still running
            try:
                await asyncio.wait_for(receiver_task, timeout=5)
            except asyncio.TimeoutError:
                receiver_task.cancel()

    except Exception as e:
        print(f"  ✗ WebSocket Error: {e}")
        import traceback
        traceback.print_exc()
        return None

    if utterance_buffer:
        finalized_segments.append(" ".join(utterance_buffer).strip())
        utterance_buffer.clear()

    total_time = time.time() - start_time
    print(f"  Total processing time: {total_time:.3f}s")

    return {
        'transcripts': transcripts,
        'latencies': latencies,
        'finalized_segments': finalized_segments,
        'total_time': total_time,
        'audio_duration': audio_duration if audio_duration else 0,
        'timing_metrics': {
            'connection_time': connection_time,
            'send_duration': send_duration,
            'first_byte_time': first_byte_time,
            'first_response_time': first_response_time,
            'first_final_time': first_final_time,
            'time_to_first_chunk': (first_chunk_sent_ref[0] - start_time) if first_chunk_sent_ref[0] else None
        }
    }

# =====================
# SAVE RESULTS
# =====================

def save_results(audio_path, result, output_dir):
    try:
        os.makedirs(output_dir, exist_ok=True)
        audio_name = Path(audio_path).stem

        transcript_file = os.path.join(output_dir, f"{audio_name}_transcript.txt")

        if result.get('finalized_segments'):
            full_transcript = " ".join(result['finalized_segments']).strip()
        else:
            final_transcripts = [t['transcript'] for t in result['transcripts'] if t['is_final']]
            full_transcript = ' '.join(final_transcripts).strip()

        with open(transcript_file, 'w', encoding='utf-8') as f:
            f.write(full_transcript)

        print(f"  💾 Transcript saved to: {transcript_file}")
        print(f"     Words: {len(full_transcript.split())}")

        latency_file = os.path.join(output_dir, f"{audio_name}_latencies.json")

        if result['latencies']:
            avg_from_send_start = sum(l['latency_from_send_start_ms'] for l in result['latencies']) / len(result['latencies'])
            min_from_send_start = min(l['latency_from_send_start_ms'] for l in result['latencies'])
            max_from_send_start = max(l['latency_from_send_start_ms'] for l in result['latencies'])

            avg_from_first_chunk = sum(l['latency_from_first_chunk_ms'] for l in result['latencies']) / len(result['latencies'])
            min_from_first_chunk = min(l['latency_from_first_chunk_ms'] for l in result['latencies'])
            max_from_first_chunk = max(l['latency_from_first_chunk_ms'] for l in result['latencies'])
        else:
            avg_from_send_start = min_from_send_start = max_from_send_start = 0
            avg_from_first_chunk = min_from_first_chunk = max_from_first_chunk = 0

        latency_data = {
            'audio_file': audio_path,
            'audio_duration_sec': result['audio_duration'],
            'total_processing_time_sec': result['total_time'],
            'timestamp': datetime.now().isoformat(),
            'model': 'nova-3',
            'language': 'multi',
            'finalized_segments': result.get('finalized_segments', []),
            'timing_metrics': {
                'connection_time_sec': result['timing_metrics']['connection_time'],
                'send_duration_sec': result['timing_metrics']['send_duration'],
                'first_byte_latency_sec': result['timing_metrics']['first_byte_time'],
                'first_response_latency_sec': result['timing_metrics']['first_response_time'],
                'first_final_latency_sec': result['timing_metrics']['first_final_time'],
                'time_to_first_chunk_sec': result['timing_metrics']['time_to_first_chunk']
            },
            'latencies': result['latencies'],
            'summary': {
                'total_responses': len(result['latencies']),
                'final_responses': sum(1 for l in result['latencies'] if l['is_final']),
                'speech_final_responses': sum(1 for l in result['latencies'] if l.get('speech_final')),
                'total_words': sum(l['words'] for l in result['latencies']),
                'total_characters': sum(l['char_count'] for l in result['latencies']),
                'avg_latency_from_send_start_ms': avg_from_send_start,
                'min_latency_from_send_start_ms': min_from_send_start,
                'max_latency_from_send_start_ms': max_from_send_start,
                'avg_latency_from_first_chunk_ms': avg_from_first_chunk,
                'min_latency_from_first_chunk_ms': min_from_first_chunk,
                'max_latency_from_first_chunk_ms': max_from_first_chunk,
            }
        }

        with open(latency_file, 'w', encoding='utf-8') as f:
            json.dump(latency_data, f, indent=2, ensure_ascii=False)

        print(f"  💾 Latencies saved to: {latency_file}")
        if result['timing_metrics']['first_byte_time'] is not None:
            print(f"     First byte: {result['timing_metrics']['first_byte_time']:.3f}s")
        if result['timing_metrics']['first_response_time']:
            print(f"     First response: {result['timing_metrics']['first_response_time']:.3f}s")
        if result['timing_metrics']['first_final_time']:
            print(f"     First final: {result['timing_metrics']['first_final_time']:.3f}s")

        return transcript_file, latency_file

    except Exception as e:
        print(f"  ✗ Error saving results: {e}")
        import traceback
        traceback.print_exc()
        return None, None

# =====================
# MAIN
# =====================

async def main():
    print("=" * 70)
    print("Deepgram Nova-3 ASR Testing (WebSocket Streaming - Realtime)")
    print("=" * 70)
    print(f"API Key: {DEEPGRAM_API_KEY[:10]}...")
    print(f"Output Directory: {OUTPUT_DIR}")
    print(f"Audio Files: {len(AUDIO_FILES)} files found")
    print(f"Processing Mode: Sequential realtime-paced streaming")
    print()

    skipped_count = 0
    newly_processed_count = 0
    failed_count = 0

    for idx, audio_file in enumerate(AUDIO_FILES, 1):
        print("-" * 70)
        print(f"Processing [{idx}/{len(AUDIO_FILES)}]: {audio_file}")
        print("-" * 70)

        if not os.path.exists(audio_file):
            print("ERROR: File not found")
            failed_count += 1
            continue

        audio_name = Path(audio_file).stem
        transcript_file = os.path.join(OUTPUT_DIR, f"{audio_name}_transcript.txt")
        latency_file = os.path.join(OUTPUT_DIR, f"{audio_name}_latencies.json")

        if os.path.exists(transcript_file) and os.path.exists(latency_file):
            print("✓ SKIPPED - Already processed")
            print(f"  Found: {transcript_file}")
            print(f"  Found: {latency_file}")
            skipped_count += 1
            print()
            continue

        file_size = os.path.getsize(audio_file)
        print(f"File size: {file_size:,} bytes ({file_size / 1024:.2f} KB)")

        result = await transcribe_audio_websocket(DEEPGRAM_API_KEY, audio_file)

        if result and result['transcripts']:
            print(f"\n✓ SUCCESS! Transcription Complete: {audio_file}")
            save_results(audio_file, result, OUTPUT_DIR)
            newly_processed_count += 1
        else:
            print(f"\n✗ Failed to get transcription: {audio_file}")
            failed_count += 1

        print()

    print("=" * 70)
    print("Testing Complete!")
    print("=" * 70)
    print(f"Total files: {len(AUDIO_FILES)}")
    print(f"Newly processed: {newly_processed_count}")
    print(f"Skipped (already done): {skipped_count}")
    print(f"Failed: {failed_count}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
