# 🎬 yt-auto — Master System Architecture & Fleet Specification

> **Single Source of Truth for YouTube Automation Fleet**  
> Read this document before inspecting, modifying, or executing operations across the `yt-auto` codebase or channel fleet.

---

## 1. Executive Summary & System Philosophy

`yt-auto` is an autonomous, headless media generation and multi-platform publishing engine. It operates 5 specialized YouTube channels producing 3 Shorts per day per channel (15 Shorts/day fleet-wide) plus 1 rotating long-form video weekly, with zero human intervention.

### Core Tenets:
1. **Fully Headless & Resilient**: Handles API rate limits, provider outages, and temporary network faults via automatic fallbacks and key rotation.
2. **Quality-Gated Publishing**: Video output must pass two strict automated gates before upload:
   - **FFmpeg Black-Screen Detector** (`blackdetect=d=0.8:pix_th=0.10`): Automatically aborts upload if dead frames > 0.8s exist.
   - **Gemini Multimodal Judge AI** (`pipeline/judge.py`): Scores narrative coherence, visual match, pacing, and subtitle synchronization (threshold: ≥ 85/100).
3. **Synthetic Media Compliance**: Mandates YouTube's `containsSyntheticMedia: True` disclosure on all automated uploads to ensure channel longevity and policy compliance.

---

## 2. Multi-Channel Fleet Matrix

The automation fleet is distributed across 5 repositories and corresponding channel identities:

| Channel | Repository | Primary Niche & Persona | Target Topics & Aesthetics | Daily Slots (IST) |
| :--- | :--- | :--- | :--- | :--- |
| **Ch 1** | [`/root/yt-auto`](file:///root/yt-auto) | **Science & Frontier Tech** | Quantum mechanics, astrophysics, biotech, computing, advanced materials. | 10:00 AM, 05:30 PM, 02:30 AM |
| **Ch 2** | [`/root/yt-auto-ch2`](file:///root/yt-auto-ch2) | **Nature & Extreme Biology** | Ocean abyssal fauna, animal adaptations, survival mechanisms, ecosystems. | 11:30 AM, 07:00 PM, 04:00 AM |
| **Ch 3** | [`/root/yt-auto-ch3`](file:///root/yt-auto-ch3) | **History & Warfare Tactics** | Ancient engineering, battle strategy, rise/fall of empires, tactical secrets. | 07:00 AM, 08:30 PM, 01:00 AM |
| **Ch 4** | [`/root/yt-auto-ch4`](file:///root/yt-auto-ch4) | **Mysteries & Unexplained** | Archaeological enigmas, geological anomalies, historical paradoxes, cold cases. | 05:30 AM, 01:00 PM, 10:00 PM |
| **Ch 5** | [`/root/yt-auto-ch5`](file:///root/yt-auto-ch5) | **Megaprojects & Engineering** | Subsea tunnels, megastructures, colossal machinery, civil breakthroughs. | 08:30 AM, 04:00 PM, 11:30 PM |

---

## 3. End-to-End Pipeline Phases

The video generation workflow is divided into discrete, decoupled phases:

```
[ Trigger (Railway Cron / GHA Schedule / Manual) ]
                      │
                      ▼
 ┌─────────────────────────────────────────────────────┐
 │ Phase 1: Topic Discovery (Gemini + Google Search)   │
 └──────────────────────┬──────────────────────────────┘
                        ▼
 ┌─────────────────────────────────────────────────────┐
 │ Phase 2: Script Writing (Zero-jargon, Hook-first)   │
 └──────────────────────┬──────────────────────────────┘
                        ▼
 ┌─────────────────────────────────────────────────────┐
 │ Phase 3: Voice Generation (Gemini TTS / Kokoro CPU) │
 └──────────────────────┬──────────────────────────────┘
                        ▼
 ┌─────────────────────────────────────────────────────┐
 │ Phase 4: B-Roll Retrieval (Pexels / Pixabay / yt-dlp│
 └──────────────────────┬──────────────────────────────┘
                        ▼
 ┌─────────────────────────────────────────────────────┐
 │ Phase 5: Timed Subtitles (Word-level .ass dynamic)  │
 └──────────────────────┬──────────────────────────────┘
                        ▼
 ┌─────────────────────────────────────────────────────┐
 │ Phase 6: Music & Procedural SFX (Numpy/Freesound)   │
 └──────────────────────┬──────────────────────────────┘
                        ▼
 ┌─────────────────────────────────────────────────────┐
 │ Phase 7: FFmpeg Video Assembly (Superfast preset)   │
 └──────────────────────┬──────────────────────────────┘
                        ▼
 ┌─────────────────────────────────────────────────────┐
 │ Phase 8: Thumbnail Generation (1280x720 + Overlay)  │
 └──────────────────────┬──────────────────────────────┘
                        ▼
 ┌─────────────────────────────────────────────────────┐
 │ Quality Gates: Strict Black-screen & Judge AI Check │
 └──────────────────────┬──────────────────────────────┘
                        ▼
 ┌─────────────────────────────────────────────────────┐
 │ Phase 9-13: Multi-Platform Upload                   │
 │ (YouTube, Dailymotion, Rumble, Meta Reels, Threads) │
 └─────────────────────────────────────────────────────┘
```

### Phase Details & Implementation Files:
* **Topic Generation** ([`pipeline/phase1_topics.py`](file:///root/yt-auto/pipeline/phase1_topics.py)): Uses Gemini 2.5 Flash with Google Search Grounding to find viral, verified news and cluster topics. Deduplicates against `published_topics.json`.
* **Script Generation** ([`pipeline/phase2_script.py`](file:///root/yt-auto/pipeline/phase2_script.py)): Generates a 4-5 segment hook-driven script with visceral everyday analogies and zero academic filler.
* **Text-to-Speech** ([`pipeline/phase3_tts.py`](file:///root/yt-auto/pipeline/phase3_tts.py)): Uses Gemini TTS voice models (`Aoede`, `Fenrir`, `Charon`, `Kore`, `Puck`) with Kokoro local CPU fallback.
* **B-roll Engine** ([`pipeline/phase4_broll.py`](file:///root/yt-auto/pipeline/phase4_broll.py)): Multi-tier visual scraper utilizing Pexels 4K API, Pixabay, Internet Archive, and sliced YouTube B-roll with fallback to Pollinations AI image animation.
* **Captions** ([`pipeline/phase5_captions.py`](file:///root/yt-auto/pipeline/phase5_captions.py)): Generates rapid-fire single/double-word animated subtitles using Bebas Neue font via ASS subtitle filters.
* **Audio Layer** ([`pipeline/phase6_music.py`](file:///root/yt-auto/pipeline/phase6_music.py), [`pipeline/sfx.py`](file:///root/yt-auto/pipeline/sfx.py)): Dynamic procedural pad chord generator in Numpy layered with transition whooshes at segment boundaries.
* **Assembly** ([`pipeline/phase7_assemble.py`](file:///root/yt-auto/pipeline/phase7_assemble.py)): Combines audio, normalized video slices, Ken Burns panning, subtitle filters, and color curves into 1080x1920 (9:16) MP4.
* **Quality Assurance** ([`pipeline/judge.py`](file:///root/yt-auto/pipeline/judge.py), [`run_publish.py`](file:///root/yt-auto/run_publish.py)): Evaluates video quality and aborts bad runs before publication.
* **Publishing Suite** ([`pipeline/phase9_upload.py`](file:///root/yt-auto/pipeline/phase9_upload.py) to `phase13_threads.py`): Uploads to YouTube Data API v3 and syndicates to Dailymotion, Rumble, Facebook/Instagram Reels, and Threads.

---

## 4. Scheduling & Cron Architecture

The fleet runs via a central Railway Cron Dispatcher ([`/root/yt-auto-cron`](file:///root/yt-auto-cron)) triggering GitHub Actions workflows.

### Global Concurrency & Lock Mechanism:
To avoid hitting API rate limits or runner contention, `start.sh` evaluates `global_pipeline_busy()` before triggering any workflow. If any repository in the fleet is actively executing a pipeline, new runs wait or stagger safely.

### 24-Hour Master Slot Schedule:

| Slot | UTC Time | IST Time | Target Repo | Workflow | Content Type |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **01** | `00:00` | `05:30` | `yt-auto-ch4` | `generate_short_ch4.yml` | Ch4 Short #1 |
| **02** | `01:30` | `07:00` | `yt-auto-ch3` | `generate_short.yml` | Ch3 Short #1 |
| **03** | `03:00` | `08:30` | `yt-auto-ch5` | `generate_short.yml` | Ch5 Short #1 |
| **04** | `04:30` | `10:00` | `yt-auto` | `generate_short.yml` | Ch1 Short #1 |
| **05** | `06:00` | `11:30` | `yt-auto-ch2` | `generate_short.yml` | Ch2 Short #1 |
| **06** | `07:30` | `13:00` | `yt-auto-ch4` | `generate_short_ch4.yml` | Ch4 Short #2 |
| **07** | `09:00` | `14:30` | *Rotation* | `generate_long.yml` | Weekly Long Video (M:Ch1, T:Ch2, W:Ch5, Th:Ch3, F:Ch4) |
| **08** | `10:30` | `16:00` | `yt-auto-ch5` | `generate_short.yml` | Ch5 Short #2 |
| **09** | `12:00` | `17:30` | `yt-auto` | `generate_short.yml` | Ch1 Short #2 |
| **10** | `13:30` | `19:00` | `yt-auto-ch2` | `generate_short.yml` | Ch2 Short #2 |
| **11** | `15:00` | `20:30` | `yt-auto-ch3` | `generate_short.yml` | Ch3 Short #2 |
| **12** | `16:30` | `22:00` | `yt-auto-ch4` | `generate_short_ch4.yml` | Ch4 Short #3 |
| **13** | `18:00` | `23:30` | `yt-auto-ch5` | `generate_short.yml` | Ch5 Short #3 |
| **14** | `19:30` | `01:00` | `yt-auto-ch3` | `generate_short.yml` | Ch3 Short #3 |
| **15** | `21:00` | `02:30` | `yt-auto` | `generate_short.yml` | Ch1 Short #3 |
| **16** | `22:30` | `04:00` | `yt-auto-ch2` | `generate_short.yml` | Ch2 Short #3 |

---

## 5. Quality Safeguards & Verification Gates

1. **FFmpeg Black Frame Detection**:
   ```bash
   ffmpeg -i output/final_short.mp4 -vf "blackdetect=d=0.8:pix_th=0.10" -f null -
   ```
   If any continuous black duration exceeds 0.8 seconds, upload is immediately terminated.
2. **Gemini Multimodal Judge AI**:
   - Analyzes video frames + audio track.
   - Evaluates:
     1. Hook strength & retention potential (0-25)
     2. Narrative clarity & zero PhD jargon (0-25)
     3. Visual-auditory alignment (0-25)
     4. Subtitle accuracy & timing (0-25)
   - Passing threshold: ≥ 85. If rejected, triggers targeted segment regeneration.
3. **Footage Credits Compliance**:
   - Automatically parses `footage_credits.json` and appends standard Fair Use attribution lines into YouTube video descriptions.

---

## 6. Secrets & Environment Configuration

| Secret / Env Var | Scope | Purpose |
| :--- | :--- | :--- |
| `GEMINI_API_KEYS` | Fleet-wide | Comma-separated Gemini keys for auto-rotation on 429/503. |
| `GEMINI_API_KEY` | Fleet-wide | Primary fallback Gemini API key. |
| `GEMINI_JUDGE_API_KEY`| Fleet-wide | Dedicated Gemini key for Judge AI review to prevent rate-limit starvation. |
| `PEXELS_API_KEY` | Fleet-wide | Primary 4K stock video provider. |
| `PIXABAY_API_KEY` | Fleet-wide | Secondary stock video provider. |
| `YT_CLIENT_ID` | Per Channel | YouTube OAuth Client ID. |
| `YT_CLIENT_SECRET` | Per Channel | YouTube OAuth Client Secret. |
| `YT_REFRESH_TOKEN` | Per Channel | YouTube OAuth Refresh Token (permanent). |
| `GH_TOKEN` / `GH_ALT_TOKEN` | Dispatcher | GitHub PAT for triggering repository workflows via API. |

---

## 7. Diagnostics & Common Failure Modes

### A. Black Screen Section Detected during Publish
* **Symptom**: `❌ CRITICAL UPLOAD BLOCKED! Black screen section detected (1.03s > 0.8s)`.
* **Root Cause**: B-roll normalization produced empty frames or ffmpeg concat filter experienced PTS drift.
* **Resolution**: Re-run generation with `--resume` to fetch fresh B-roll or rebuild assembly with verified clips.

### B. Generate Attempt Timed Out (Exit Code 124)
* **Symptom**: `Generate attempt 2 timed out`.
* **Root Cause**: YouTube B-roll slicing via `yt-dlp` stalled due to anti-bot challenges or slow archive.org download.
* **Resolution**: The pipeline automatically falls back to Pexels 4K clips and Pollinations AI visual generation.

### C. YouTube OAuth `RefreshError`
* **Symptom**: `google.auth.exceptions.RefreshError: invalid_grant: Token has been expired or revoked`.
* **Root Cause**: Google Cloud project is in "Testing" status (tokens expire in 7 days) or credentials revoked.
* **Resolution**: Ensure OAuth Consent Screen is marked **In Production**, and re-generate `YT_REFRESH_TOKEN` via OAuth Playground.

---

## 8. CLI Commands & Quick Reference

```bash
# Generate short video locally (dry run / test)
python run_generate.py --format short

# Resume interrupted generation from cached artifacts
python run_generate.py --format short --resume

# Run publish step with black-screen and judge verification
python run_publish.py

# Bypass Judge AI for manual verification
python run_publish.py --bypass-judge

# Inspect recent runs across all channels
gh run list -R gurination1/yt-auto --limit 5
gh run list -R gurination1/yt-auto-ch2 --limit 5
gh run list -R gurination1/yt-auto-ch3 --limit 5
gh run list -R gurination1/yt-auto-ch4 --limit 5
gh run list -R gurination1/yt-auto-ch5 --limit 5
```
