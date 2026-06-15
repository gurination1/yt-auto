import os
import random
import wave
from pipeline.config import GEMINI_VOICES
from pipeline.gemini import GeminiClient

def generate_audio(script: dict) -> list[str]:
    gemini_client = GeminiClient()
    voice = random.choice(GEMINI_VOICES)
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

                # Kokoro voices: af_heart, af_bella, am_adam, am_michael, af_sky
                ko_voices = ["af_heart", "af_bella", "am_adam", "am_michael"]
                ko_voice  = random.choice(ko_voices)
                pipeline_ko = KPipeline(lang_code="a")  # 'a' = American English

                samples = []
                for _, _, audio in pipeline_ko(seg["narration"], voice=ko_voice, speed=1.0):
                    samples.append(audio)

                import scipy.io.wavfile
                audio_np = np.concatenate(samples)
                scipy.io.wavfile.write(out_path, 24000, audio_np)
                print(f"Kokoro fallback succeeded for segment {seg_id} (voice: {ko_voice})")

            except Exception as e2:
                raise RuntimeError(
                    f"Both Gemini TTS and Kokoro failed for segment {seg_id}: "
                    f"Gemini={e} | Kokoro={e2}"
                )
        
        audio_files.append(out_path)
        
    return audio_files
