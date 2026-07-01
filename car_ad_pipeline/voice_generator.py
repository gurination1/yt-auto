import os
import json
import time
from car_ad_pipeline.gemini_client import GeminiClient

def generate_voiceover(client: GeminiClient, scene_cues: list, output_dir: str) -> list:
    print("Generating voiceover audio segments using Gemini TTS...")
    os.makedirs(output_dir, exist_ok=True)
    
    audio_paths = []
    total_prompt_tokens = 0
    total_output_tokens = 0
    
    token_log_path = os.path.join(output_dir, "token_usage.log")
    
    for i, scene in enumerate(scene_cues):
        ad_copy = scene.get("ad_copy_hindi", "").strip()
        if not ad_copy:
            print(f"Scene {i+1} has no Hindi ad copy. Skipping voice generation.")
            audio_paths.append(None)
            continue
            
        print(f"Generating TTS for Scene {i+1}: '{ad_copy}'...")
        
        # We can clean emotional direction tags like [excited], [pause] from TTS text, 
        # but the prompt walkthrough says: "natural-language style direction, inline tags ([excited], [confident], [pause])"
        # Wait, does the voice model understand them? Yes, sometimes the prompt says the tags are kept in text 
        # or we instruct the model to interpret them. We keep them in the text as directed by the walkthrough.
        
        audio_data = client.generate_tts(ad_copy, voice="Aoede")
        
        # Log token usage estimation (roughly 4 characters per token for prose, and output audio is about 20 tokens per second of audio)
        # We can approximate prompt tokens based on prompt length, and output tokens based on audio file size.
        prompt_est = len(ad_copy) // 2
        output_est = len(audio_data) // 800  # rough estimate for audio bytes to tokens
        
        total_prompt_tokens += prompt_est
        total_output_tokens += output_est
        
        audio_filename = f"scene_{i+1}_tts.wav"
        audio_path = os.path.join(output_dir, audio_filename)
        with open(audio_path, "wb") as f:
            f.write(audio_data)
            
        print(f"Saved: {audio_path}")
        audio_paths.append(audio_path)
        
    # Append to token usage log
    log_line = (
        f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Car Ad Pipeline - "
        f"Prompt tokens (est): {total_prompt_tokens}, Output tokens (est): {total_output_tokens}, "
        f"Estimated Audio cost: ${(total_output_tokens / 1000000) * 20:.5f}\n"
    )
    with open(token_log_path, "a") as f:
        f.write(log_line)
        
    print(f"Logged token usage to {token_log_path}: {log_line.strip()}")
    return audio_paths
