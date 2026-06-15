import os
import random
import wave
import json
from pipeline.config import GEMINI_VOICES, KOKORO_VOICES
from pipeline.gemini import GeminiClient

STATE_PATH = "voice_state.json"

def pick_voice(pool: list[str], state_key: str) -> str:
    state = {}
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, "r") as f:
                state = json.load(f)
        except Exception:
            pass
    last = state.get(state_key)
    choice = random.choice([v for v in pool if v != last] or pool)
    state[state_key] = choice
    try:
        with open(STATE_PATH, "w") as f:
            json.dump(state, f)
    except Exception as e:
        print(f"Warning: Failed to write voice state: {e}")
    return choice

def generate_audio(script: dict) -> list[str]:
    gemini_client = GeminiClient()
    voice = pick_voice(GEMINI_VOICES, "gemini")
    ko_voice = pick_voice(KOKORO_VOICES, "kokoro")
    audio_files = []
    
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    
    for seg in script["segments"]:
        seg_id = seg["id"]
        out_path = f"output/tts_segment_{seg_id}.wav"
        
        # Check if file already exists and is valid (greater than 1KB)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
            print(f"TTS segment {seg_id} already exists, skipping generation.")
            audio_files.append(out_path)
            continue
            
        print(f"Generating TTS for Segment {seg_id}...")
        
        # Primary: Gemini TTS
        try:
            audio_bytes, mime_type = gemini_client.generate_tts(seg["narration"], voice=voice)
            
            # Check if it starts with the RIFF/WAVE header or mimeType suggests wav
            if audio_bytes.startswith(b"RIFF") or "wav" in mime_type.lower():
                with open(out_path, "wb") as wf:
                    wf.write(audio_bytes)
            else:
                # Wrapped PCM L16 in WAV header
                # Typically rate is 24000, mono, 16-bit PCM (2 bytes)
                with wave.open(out_path, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)  # 16-bit
                    wf.setframerate(24000)
                    wf.writeframes(audio_bytes)
            print(f"Gemini TTS succeeded for segment {seg_id} (Voice: {voice})")
            
        except Exception as e:
            print(f"Gemini TTS failed for segment {seg_id}: {e}. Trying Kokoro fallback…")
            try:
                import numpy as np
                import soundfile as sf
                from kokoro import KPipeline

                pipeline_ko = KPipeline(lang_code="a")  # 'a' = American English

                samples = []
                for _, _, audio in pipeline_ko(seg["narration"], voice=ko_voice, speed=1.0):
                    samples.append(audio)

                audio_np = np.concatenate(samples)
                audio_int16 = np.clip(audio_np * 32767, -32768, 32767).astype(np.int16)
                with wave.open(out_path, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(24000)
                    wf.writeframes(audio_int16.tobytes())
                print(f"Kokoro fallback succeeded for segment {seg_id} (voice: {ko_voice})")

            except Exception as e2:
                raise RuntimeError(
                    f"Both Gemini TTS and Kokoro failed for segment {seg_id}: "
                    f"Gemini={e} | Kokoro={e2}"
                )
        
        audio_files.append(out_path)
        
    return audio_files
