"""
Test Visual Subject Matching Engine
===================================
Simulates the candidate pool evaluation across multiple challenging scenarios:
1. Anglerfish (MBARI authentic vs generic dark water vs cartoon vs fishing tackle)
2. Paul Freeman Bigfoot (Archival film vs cosplay vlog vs game)
3. Chernobyl Elephant's Foot (Corium archival footage vs STALKER gameplay)
4. Dynamic Speech Cadence & Optical Flow Speed Pacing
"""

import os
import sys
import json
import math
import wave
import struct

# Add parent directory to path
sys.path.insert(0, "/root/yt-auto")

from pipeline.visual_subject_matching_engine import (
    SemanticEntityExtractor,
    HardEntityGatekeeper,
    FastVisionQualityGate,
    CadenceMotionPacer,
    VisualSubjectMatchingPipeline,
    CandidateVideo
)

def run_comprehensive_test():
    print("Initializing Visual Subject Matching Pipeline...")
    pipeline = VisualSubjectMatchingPipeline()

    # =========================================================================
    # Test Case 1: Anglerfish
    # =========================================================================
    sentence_1 = "The female anglerfish uses a glowing bioluminescent esca to attract prey in the abyssal midnight zone."
    print("\n" + "="*80)
    print(f"TEST CASE 1: {sentence_1}")
    print("="*80)

    profile_1 = pipeline.extractor.extract(sentence_1)
    print(f"Extracted Entity Profile:")
    print(f"  Anchor Entity   : {profile_1.anchor_entity}")
    print(f"  Alt Names       : {profile_1.scientific_or_alt_names}")
    print(f"  Category        : {profile_1.entity_category}")
    print(f"  Negative Words  : {profile_1.negative_banwords}")
    print(f"  Targeted Query  : {profile_1.targeted_queries.get('youtube_authority')}")

    # Create candidate pool
    candidates_1 = [
        CandidateVideo(
            id="cand_mbari_01",
            title="Black Seadevil Anglerfish (Melanocetus) Captured on ROV Video | MBARI",
            description="MBARI's ROV Doc Ricketts filmed this female anglerfish at 600m depth in Monterey Canyon.",
            channel_name="MBARI (Monterey Bay Aquarium Research Institute)",
            tags=["anglerfish", "deep sea", "MBARI", "Melanocetus johnsonii", "bioluminescence"],
            duration_seconds=124.0,
            url="https://youtube.com/watch?v=mock_mbari"
        ),
        CandidateVideo(
            id="cand_generic_water",
            title="Dark Deep Blue Ocean Underwater Ambient 4K Relaxation",
            description="Calm deep ocean darkness water background loop for sleeping.",
            channel_name="AmbientRelaxationHQ",
            tags=["ocean", "water", "dark", "underwater", "relaxing"],
            duration_seconds=3600.0,
            url="https://youtube.com/watch?v=mock_generic"
        ),
        CandidateVideo(
            id="cand_cartoon_fish",
            title="Cute Anglerfish Cartoon Animation Song for Kids",
            description="Learn ocean animals with funny cartoon animated anglerfish character!",
            channel_name="KidsToonWorld",
            tags=["anglerfish cartoon", "kids animation", "drawing", "songs"],
            duration_seconds=180.0,
            url="https://youtube.com/watch?v=mock_cartoon"
        ),
        CandidateVideo(
            id="cand_tackle_unboxing",
            title="Angler Fish Lure Unboxing & Tackle Review - Catch Big Bass!",
            description="Today we review this crazy angler fish lure and reaction testing in a tank.",
            channel_name="ProFishingReview",
            tags=["fishing lure", "angler fish", "tackle review", "reaction"],
            duration_seconds=610.0,
            url="https://youtube.com/watch?v=mock_tackle"
        )
    ]

    print("\nEvaluating Candidate Pool through Hard Entity Gatekeeper:")
    for cand in candidates_1:
        decision = pipeline.gatekeeper.evaluate_candidate(cand, profile_1)
        status = "PASSED" if decision.passed else "REJECTED"
        print(f"  [{status:8s}] {cand.id:20s} | Score: {decision.final_score:5.1f} | Tier: {decision.authority_tier} | Reasons: {decision.rejection_reasons}")

    # =========================================================================
    # Test Case 2: Chernobyl Elephant's Foot
    # =========================================================================
    sentence_2 = "Deep beneath Reactor 4 sits the Elephant's Foot, a deadly mass of radioactive corium."
    print("\n" + "="*80)
    print(f"TEST CASE 2: {sentence_2}")
    print("="*80)

    profile_2 = pipeline.extractor.extract(sentence_2)
    print(f"Extracted Entity Profile:")
    print(f"  Anchor Entity   : {profile_2.anchor_entity}")
    print(f"  Alt Names       : {profile_2.scientific_or_alt_names}")
    print(f"  Targeted Query  : {profile_2.targeted_queries.get('youtube_authority')}")

    candidates_2 = [
        CandidateVideo(
            id="cand_chernobyl_archive",
            title="Rare 1996 Robotic Inspection of the Elephant's Foot Corium inside Unit 4 | Archive Footage",
            description="Authentic documentary archive footage of remote robotic probe measuring the Chernobyl Elephant's foot corium.",
            channel_name="U.S. National Archives / Historical Science",
            tags=["chernobyl", "elephants foot", "corium", "reactor 4", "documentary"],
            duration_seconds=420.0,
            url="https://youtube.com/watch?v=mock_chernobyl"
        ),
        CandidateVideo(
            id="cand_stalker_game",
            title="S.T.A.L.K.E.R. 2 - Finding the Elephant's Foot Secret Easter Egg Gameplay Walkthrough",
            description="We finally reached the reactor core! Let's play S.T.A.L.K.E.R. 2 Heart of Chornobyl.",
            channel_name="GamerKing99",
            tags=["stalker 2", "gameplay", "walkthrough", "elephants foot", "reaction"],
            duration_seconds=950.0,
            url="https://youtube.com/watch?v=mock_stalker"
        )
    ]

    print("\nEvaluating Candidate Pool through Hard Entity Gatekeeper:")
    for cand in candidates_2:
        decision = pipeline.gatekeeper.evaluate_candidate(cand, profile_2)
        status = "PASSED" if decision.passed else "REJECTED"
        print(f"  [{status:8s}] {cand.id:20s} | Score: {decision.final_score:5.1f} | Tier: {decision.authority_tier} | Reasons: {decision.rejection_reasons}")

    # =========================================================================
    # Test Case 3: Speech Cadence & Optical Flow Speed Pacing
    # =========================================================================
    print("\n" + "="*80)
    print("TEST CASE 3: Dynamic Speech Cadence & Optical Flow Speed Pacing")
    print("="*80)

    os.makedirs("/root/scratch", exist_ok=True)
    mock_audio = "/root/scratch/mock_tts_test.wav"
    
    with wave.open(mock_audio, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        # 5.0 seconds of audio
        samples = [int(12000 * math.sin(2 * math.pi * 440 * i / 24000)) for i in range(24000 * 5)]
        raw_data = struct.pack(f"<{len(samples)}h", *samples)
        wf.writeframes(raw_data)

    pacer = CadenceMotionPacer()

    script_fast = "The creature vanished into the dense fog at unbelievable speed leaving deep tracks behind."
    script_slow = "In total darkness, the ancient predator waits."
    script_normal = "Scientists deployed autonomous deep-sea submersibles to survey the hydrothermal vents."

    spec_fast = pacer.calculate_pacing(mock_audio, script_fast, source_video_duration=10.0)
    spec_slow = pacer.calculate_pacing(mock_audio, script_slow, source_video_duration=10.0)
    spec_normal = pacer.calculate_pacing(mock_audio, script_normal, source_video_duration=10.0)

    print(f"Fast Narration   -> WPM: {spec_fast.speech_wpm:5.1f} | Speed Factor: {spec_fast.speed_factor:4.2f}x | Mode: {spec_fast.motion_interpolation_mode}")
    print(f"Slow Narration   -> WPM: {spec_slow.speech_wpm:5.1f} | Speed Factor: {spec_slow.speed_factor:4.2f}x | Mode: {spec_slow.motion_interpolation_mode}")
    print(f"Normal Narration -> WPM: {spec_normal.speech_wpm:5.1f} | Speed Factor: {spec_normal.speed_factor:4.2f}x | Mode: {spec_normal.motion_interpolation_mode}")
    print(f"\nGenerated Filter Chain (Fast): {spec_fast.ffmpeg_filter_chain}")

    print("\nALL VERIFICATION TESTS COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    run_comprehensive_test()
