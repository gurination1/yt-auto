import os
try:
    from dotenv import load_dotenv
    load_dotenv()
    for ep in [".env", "../.env", "../../.env", "/mnt/g/yt-auto-fleet/.env"]:
        if os.path.exists(ep):
            load_dotenv(ep, override=False)
except Exception:
    pass

# Auto-load local_env.sh if present to populate environment variables
def _autoload_local_env():
    for env_path in [".env", "local_env.sh", "../local_env.sh",  "/root/local_env.sh"]:
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if line.startswith("export "):
                            line = line[7:]
                        if "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip('"').strip("'")
                            if k and k not in os.environ and v:
                                os.environ[k] = v
            except Exception:
                pass

_autoload_local_env()

# ── Gemini Key Pool ──────────────────────────────────────────────────────────
def _load_keys() -> list[str]:
    keys: list[str] = []
    multi = os.environ.get("GEMINI_API_KEYS", "").strip()
    if multi:
        keys.extend(k.strip() for k in multi.split(",") if k.strip())
    single = os.environ.get("GEMINI_API_KEY", "").strip()
    if single and not keys:
        keys.append(single)
    return list(dict.fromkeys(keys))

GEMINI_API_KEYS: list[str] = _load_keys()
GEMINI_API_KEY: str = GEMINI_API_KEYS[0] if GEMINI_API_KEYS else ""

GEMINI_JUDGE_API_KEY: str = os.environ.get("GEMINI_JUDGE_API_KEY", "").strip() or GEMINI_API_KEY

# ── Other APIs ───────────────────────────────────────────────────────────────
PEXELS_API_KEY   = os.environ.get("PEXELS_API_KEY", "")
PIXABAY_API_KEY  = os.environ.get("PIXABAY_API_KEY", "")
COVERR_API_KEY   = os.environ.get("COVERR_API_KEY", "")
NASA_API_KEY     = os.environ.get("NASA_API_KEY", "DEMO_KEY")
KLIPY_API_KEY    = os.environ.get("KLIPY_API_KEY", "")
FREESOUND_API_KEY = os.environ.get("FREESOUND_API_KEY", "")

# ── YouTube OAuth ────────────────────────────────────────────────────────────
YT_CLIENT_ID     = os.environ.get("YT_CLIENT_ID", "")
YT_CLIENT_SECRET = os.environ.get("YT_CLIENT_SECRET", "")
YT_REFRESH_TOKEN = os.environ.get("YT_REFRESH_TOKEN", "")

# ── Gemini Models ────────────────────────────────────────────────────────────
GEMINI_FLASH        = "gemini-2.5-flash"
GEMINI_FLASH_BACKUP = "gemini-2.5-flash-lite"
GEMINI_PRO          = "gemini-2.5-flash"
GEMINI_TTS_MODEL    = "gemini-2.5-flash-preview-tts"
GEMINI_API_BASE     = "https://generativelanguage.googleapis.com/v1beta"

GEMINI_VOICES    = ["Fenrir", "Puck", "Charon", "Orus", "Kore", "Aoede"]
EDGE_VOICES      = ["en-US-GuyNeural", "en-US-AndrewNeural", "en-US-ChristopherNeural", "en-US-EricNeural", "en-US-BrianNeural", "en-US-AvaNeural", "en-US-EmmaNeural", "en-US-SteffanNeural"]
KOKORO_VOICES    = ["af_heart","af_bella","af_nicole","af_sarah","af_sky","af_aoede","am_adam","am_michael","am_fenrir","am_puck"]

# ── Video Specs ──────────────────────────────────────────────────────────────
SHORTS_W, SHORTS_H = 1080, 1920
LONG_W,   LONG_H   = 1920, 1080
FPS                 = 30
TOPIC_LOG_SIZE      = 90

HOOK_PATTERNS = [
    "The {topic} fact that breaks a rule you learned in school",
    "In exactly 30 seconds you'll never see {topic} the same way",
    "Scientists found something inside {topic} that shouldn't exist",
    "The {topic} detail that 99% of people never notice — even experts",
    "What {topic} does when no one is watching will disturb you",
    "The one thing about {topic} that every textbook gets wrong",
    "This single {topic} fact overturns 100 years of assumptions",
    "You've seen {topic} your whole life. You've never actually seen it.",
]

THUMBNAIL_LAYOUTS = [
    "dark_top_bar",
    "centered_gradient",
    "bottom_third",
    "split_left",
]

# ── Channel Boundary & Topic Isolation (Channel 1: Science & Frontier Tech) ──
CHANNEL_NICHE = os.environ.get("CHANNEL_NICHE", "science")

CHANNEL_BOUNDARY = {
    "channel_id": "ch1",
    "name": "Channel 1: Science & Frontier Tech",
    "niche_description": "Cutting-edge physical sciences, quantum mechanics, astrophysics, cosmology, nanotechnology, metamaterials, advanced materials science, and breakthrough physics.",
    "allowed_subclusters": [
        "quantum mechanics, entanglement, and subatomic physics",
        "astrophysics, neutron stars, and deep cosmic phenomena",
        "nanotechnology, molecular machines, and advanced metamaterials",
        "advanced materials science, superconductors, and crystal lattices",
        "theoretical physics, thermodynamics, and spacetime paradoxes"
    ],
    "strict_negative_constraints": [
        "NO civil construction, infrastructure, tunnels, bridges, dams, excavators, or skyscrapers.",
        "NO ancient warfare, medieval battles, military sieges, swords, or historical empires.",
        "NO UFOs, alien abductions, ghosts, haunted places, cryptids, or paranormal folklore.",
        "NO financial markets, crypto, bitcoin, stocks, venture capital, hedge funds, or trading.",
        "NO zoology, wildlife documentaries, animal predators, insects, or plant biology."
    ],
    "negative_keywords": [
        "tunnel boring",
        "tbm",
        "civil tunnel",
        "rail tunnel",
        "highway tunnel",
        "subsea tunnel",
        "suspension bridge",
        "viaduct",
        "bridge construction",
        "hydroelectric dam",
        "mega dam",
        "concrete dam",
        "water dam",
        "excavator",
        "bagger 288",
        "bagger 293",
        "skyscraper construction",
        "civil engineering",
        "concrete arch",
        "gotthard base",
        "siege weapon",
        "roman army",
        "roman legion",
        "gladiator",
        "medieval battle",
        "ancient warfare",
        "catapult",
        "trebuchet",
        "phalanx",
        "knight armor",
        "spartan warrior",
        "cannae",
        "ufo sighting",
        "alien abduction",
        "haunted house",
        "ghost ship",
        "bermuda triangle",
        "cryptid",
        "bigfoot",
        "crypto",
        "bitcoin",
        "ethereum",
        "blockchain",
        "stock market",
        "hedge fund",
        "wall street",
        "venture capital",
        "startup valuation",
        "tax-loss",
        "private equity",
        "wildlife documentary",
        "zoology",
        "apex predator",
        "venomous snake",
        "insect swarm",
        "mammal species",
        "bird migration",
        "jellyfish sting",
        "dinosaur fossil"
    ]
}

CHANNEL_SUBCLUSTERS = CHANNEL_BOUNDARY["allowed_subclusters"]
SCIENCE_SUBCLUSTERS = CHANNEL_SUBCLUSTERS
NATURE_SUBCLUSTERS = CHANNEL_SUBCLUSTERS
NATURAL_WORLD_SUBCLUSTERS = CHANNEL_SUBCLUSTERS
HISTORY_SUBCLUSTERS = CHANNEL_SUBCLUSTERS
MYSTERY_SUBCLUSTERS = CHANNEL_SUBCLUSTERS
ENGINEERING_SUBCLUSTERS = CHANNEL_SUBCLUSTERS
NICHE_SUBCLUSTERS = CHANNEL_SUBCLUSTERS

YT_CATEGORY_EDUCATION = "27"
YT_CATEGORY_SCIENCE   = "28"
YT_CATEGORY_DEFAULT   = "28"
NASA_BROLL_ENABLED    = True

RICH_FALLBACK_TOPICS = [
    {
        "topic": "The Quantum Zeno Effect: How observing an unstable particle can freeze it in time forever",
        "short_hook": "Can watching an atom stop time itself?",
        "hook_type": "curiosity_gap",
        "for_format": "both",
        "subcluster": "quantum mechanics, entanglement, and subatomic physics"
    },
    {
        "topic": "Time Crystals: The bizarre state of matter that repeats in time without consuming energy",
        "short_hook": "A crystal that ticks forever with zero power.",
        "hook_type": "curiosity_gap",
        "for_format": "both",
        "subcluster": "advanced materials science, superconductors, and crystal lattices"
    },
    {
        "topic": "Type-II Superconductors: How quantum flux pinning allows magnets to levitate upside down in mid-air",
        "short_hook": "Why does this frozen disc float upside down?",
        "hook_type": "curiosity_gap",
        "for_format": "both",
        "subcluster": "advanced materials science, superconductors, and crystal lattices"
    },
    {
        "topic": "Graphene Aerogel: The world's lightest solid that can rest atop a flower petal without bending it",
        "short_hook": "This solid rests on a flower without bending it.",
        "hook_type": "curiosity_gap",
        "for_format": "both",
        "subcluster": "nanotechnology, molecular machines, and advanced metamaterials"
    },
    {
        "topic": "The Casimir Effect: How two uncharged plates in a pure vacuum are forced together by virtual particles",
        "short_hook": "Why does empty space push metal plates together?",
        "hook_type": "curiosity_gap",
        "for_format": "both",
        "subcluster": "quantum mechanics, entanglement, and subatomic physics"
    },
    {
        "topic": "James Webb Space Telescope: Why infrared mirrors must be coated in microscopic vaporized gold",
        "short_hook": "Why did NASA coat this telescope in pure gold?",
        "hook_type": "curiosity_gap",
        "for_format": "both",
        "subcluster": "astrophysics, neutron stars, and deep cosmic phenomena"
    },
    {
        "topic": "Neutron Star Degeneracy: Why a single sugar-cube volume of neutron star weighs as much as Mount Everest",
        "short_hook": "A teaspoon of this star weighs billions of tons.",
        "hook_type": "curiosity_gap",
        "for_format": "both",
        "subcluster": "astrophysics, neutron stars, and deep cosmic phenomena"
    },
    {
        "topic": "Quantum Entanglement: How photons communicate instantaneously across billions of light-years",
        "short_hook": "Einstein called this spooky action at a distance.",
        "hook_type": "curiosity_gap",
        "for_format": "both",
        "subcluster": "quantum mechanics, entanglement, and subatomic physics"
    },
    {
        "topic": "Metallic Hydrogen: The superheated ultra-high pressure fuel synthesized inside diamond anvil cells",
        "short_hook": "Crushing gas between diamonds turns it into metal.",
        "hook_type": "curiosity_gap",
        "for_format": "both",
        "subcluster": "advanced materials science, superconductors, and crystal lattices"
    },
    {
        "topic": "Carbon Nanotubes: The cylindrical carbon allotropes 100 times stronger than steel at one-sixth the weight",
        "short_hook": "This microscopic tube is 100 times stronger than steel.",
        "hook_type": "curiosity_gap",
        "for_format": "both",
        "subcluster": "nanotechnology, molecular machines, and advanced metamaterials"
    },
    {
        "topic": "Fast Radio Bursts: Millisecond cosmic flashes releasing more energy than the Sun outputs in three days",
        "short_hook": "What is firing millisecond energy bursts across deep space?",
        "hook_type": "curiosity_gap",
        "for_format": "both",
        "subcluster": "astrophysics, neutron stars, and deep cosmic phenomena"
    },
    {
        "topic": "The Mpemba Paradox: Why boiling hot water can freeze significantly faster than cold water",
        "short_hook": "Why does boiling water freeze faster than cold water?",
        "hook_type": "curiosity_gap",
        "for_format": "both",
        "subcluster": "theoretical physics, thermodynamics, and spacetime paradoxes"
    },
    {
        "topic": "Silica Aerogel: The 99.8% air solid matrix that stops a 1000-degree blowtorch from melting a crayon",
        "short_hook": "This frozen smoke stops a blowtorch instantly.",
        "hook_type": "curiosity_gap",
        "for_format": "both",
        "subcluster": "nanotechnology, molecular machines, and advanced metamaterials"
    },
    {
        "topic": "Gravitational Lensing: How massive galaxy clusters bend spacetime into cosmic magnifying glasses",
        "short_hook": "Einstein predicted giant magnifying glasses in deep space.",
        "hook_type": "curiosity_gap",
        "for_format": "both",
        "subcluster": "astrophysics, neutron stars, and deep cosmic phenomena"
    },
    {
        "topic": "Gallium Liquid Metal: The non-toxic metal that melts at 86 degrees Fahrenheit and shatters aluminum",
        "short_hook": "Why is this liquid metal strictly banned on airplanes?",
        "hook_type": "curiosity_gap",
        "for_format": "both",
        "subcluster": "advanced materials science, superconductors, and crystal lattices"
    },
    {
        "topic": "Quantum Tunneling: How subatomic particles pass straight through impenetrable energy barriers",
        "short_hook": "Subatomic particles can teleport through solid walls.",
        "hook_type": "curiosity_gap",
        "for_format": "both",
        "subcluster": "quantum mechanics, entanglement, and subatomic physics"
    },
    {
        "topic": "Magnetars: The super-dense magnetic stars whose field would dissolve human atoms from 1,000 miles away",
        "short_hook": "A dead star that dissolves atoms from 1,000 miles away.",
        "hook_type": "curiosity_gap",
        "for_format": "both",
        "subcluster": "astrophysics, neutron stars, and deep cosmic phenomena"
    },
    {
        "topic": "DNA Origami Nanobots: Synthetic molecular containers programmed to deliver payloads at cellular scale",
        "short_hook": "Microscopic robots made of folded DNA strands.",
        "hook_type": "curiosity_gap",
        "for_format": "both",
        "subcluster": "nanotechnology, molecular machines, and advanced metamaterials"
    },
    {
        "topic": "Superfluid Helium-4: The quantum liquid with zero viscosity that climbs up beaker walls and escapes",
        "short_hook": "This bizarre liquid defies gravity and climbs out of beakers.",
        "hook_type": "curiosity_gap",
        "for_format": "both",
        "subcluster": "theoretical physics, thermodynamics, and spacetime paradoxes"
    },
    {
        "topic": "Strontium Optical Lattice Clocks: Timekeepers so precise they lose less than one second in 30 billion years",
        "short_hook": "This atomic clock won't lose a second in 30 billion years.",
        "hook_type": "curiosity_gap",
        "for_format": "both",
        "subcluster": "quantum mechanics, entanglement, and subatomic physics"
    },
    {
        "topic": "Metamaterial Invisibility Cloaks: Nanostructured surfaces that guide optical waveforms completely around objects",
        "short_hook": "Engineers built an invisibility cloak using metamaterials.",
        "hook_type": "curiosity_gap",
        "for_format": "both",
        "subcluster": "nanotechnology, molecular machines, and advanced metamaterials"
    },
    {
        "topic": "Cosmic Ray Muon Tomography: How high-energy subatomic particles map hidden chambers inside monuments",
        "short_hook": "Cosmic rays from space found a hidden room in the pyramids.",
        "hook_type": "curiosity_gap",
        "for_format": "both",
        "subcluster": "theoretical physics, thermodynamics, and spacetime paradoxes"
    },
    {
        "topic": "Cherenkov Radiation: Why underwater nuclear reactors glow with eerie electric blue optical light",
        "short_hook": "Why do underwater nuclear cores glow electric blue?",
        "hook_type": "curiosity_gap",
        "for_format": "both",
        "subcluster": "quantum mechanics, entanglement, and subatomic physics"
    },
    {
        "topic": "Bose-Einstein Condensate: The macroscopic quantum state where thousands of chilled atoms act as one wave",
        "short_hook": "Scientists stopped light inside a super-chilled gas.",
        "hook_type": "curiosity_gap",
        "for_format": "both",
        "subcluster": "theoretical physics, thermodynamics, and spacetime paradoxes"
    },
    {
        "topic": "Quasicrystals: The forbidden non-repeating atomic geometries that physicists thought were impossible",
        "short_hook": "The impossible crystal structure that won a Nobel Prize.",
        "hook_type": "curiosity_gap",
        "for_format": "both",
        "subcluster": "advanced materials science, superconductors, and crystal lattices"
    }
]

def validate_config():
    missing = []
    if not GEMINI_API_KEYS:
        missing.append("GEMINI_API_KEY or GEMINI_API_KEYS")
    
    check_vars = []
    if PEXELS_API_KEY:
        check_vars.append(("PEXELS_API_KEY", PEXELS_API_KEY))
    if os.environ.get("DISABLE_YT_UPLOAD") != "1":
        check_vars.extend([
            ("YT_CLIENT_ID", YT_CLIENT_ID),
            ("YT_CLIENT_SECRET", YT_CLIENT_SECRET),
            ("YT_REFRESH_TOKEN", YT_REFRESH_TOKEN)
        ])
    for var, val in check_vars:
        if not val:
            missing.append(var)
    if missing:
        raise ValueError(f"Missing required env vars: {', '.join(missing)}")
    n = len(GEMINI_API_KEYS)
    print(f"[Config] {n} Gemini generation key(s) loaded.")
    if GEMINI_JUDGE_API_KEY != GEMINI_API_KEY:
        print("[Config] Separate GEMINI_JUDGE_API_KEY active — Judge uses its own quota.")
    if COVERR_API_KEY:
        print("[Config] Coverr API: enabled (cinematic B-roll tier active).")
    if NASA_API_KEY:
        print(f"[Config] NASA API: enabled (key={'DEMO_KEY (rate-limited)' if NASA_API_KEY == 'DEMO_KEY' else 'custom'}).")
    if KLIPY_API_KEY:
        print("[Config] Klipy API: enabled (GIF/meme B-roll tier active).")
    if FREESOUND_API_KEY:
        print("[Config] Freesound API: enabled (CC0 ambient music tier active).")

# ── Social / Beacons Link ───────────────────────────────────────────────────
BEACONS_LINK = os.environ.get("BEACONS_LINK", "https://beacons.ai/edu_fun")

# ── Fleet Niche Profiles & Digital Fingerprints ──────────────────────────────
FLEET_NICHE_PROFILES = {
    "science": {
        "channel_id": "ch1",
        "name": "Science & Frontier Tech",
        "gemini_voice": "Fenrir",
        "kokoro_voice": "am_adam",
        "edge_voice": "en-US-GuyNeural",
        "cadence_speed": 1.02,
        "vocal_tone": "bold_authority",
        "persona_desc": "precise, analytical, 1.02x",
        "subtitle_fonts": ["Rajdhani", "Montserrat", "Bebas Neue"],
        "c_base": "&H00FFFFFF&",          # Base: Pure White (#FFFFFF)
        "c_active": "&H00FFE500&",        # Active: Electric Cyan (#00E5FF)
        "c_power": "&H00FF8800&",         # Power Accent: Neon Blue/Orange
        "outline_color": "&H00100505&",   # Outline: 9px #050510 (obsidian navy)
        "shadow_color": "&H80000000&",    # Shadow: 3px
        "outline_w": 9,
        "shadow_d": 3,
        "blur": 1,
        "margin_v": 440,
        "procedural_chords": [
            [("D", "min"), ("G", "maj"), ("C", "maj"), ("A", "min")],
            [("E", "min"), ("A", "min"), ("D", "maj"), ("B", "min")],
            [("C", "maj"), ("A", "min"), ("F", "maj"), ("G", "maj")],
        ],
        "music_bpm": 120,
        "foley_type": "digital_tech",
        "ducking": {
            "attack": 15,
            "release": 180,
            "ratio": 4.0,
            "threshold": 0.07,
            "music_vol": 0.22,
            "sfx_vol": 0.28,
        },
        "container_metadata": {
            "artist": "Axiom Lab Studios / Science & Frontier Tech",
            "genre": "Science & Technology / Quantum Astrophysics",
            "comment": "Autonomous analytical documentary series on frontier science, quantum physics, and advanced technology.",
        },
        "color_curves": "eq=contrast=1.08:saturation=1.14:gamma=0.95,colorbalance=bs=0.06:bm=0.02:rs=-0.02",
        "badge_text": "⚛ QUANTUM LAB",
        "badge_border": "#00E5FF",
        "badge_bg": "#050B14",
        "thumb_font": "Rajdhani",
        "thumb_color1": "#FFFFFF",
        "thumb_color2": "#00E5FF",
        "thumb_border": "#050510",
    },
    "nature": {
        "channel_id": "ch2",
        "name": "Nature & Extreme Biology",
        "gemini_voice": "Kore",
        "kokoro_voice": "af_heart",
        "edge_voice": "en-US-AvaNeural",
        "cadence_speed": 0.98,
        "vocal_tone": "deep_curiosity",
        "persona_desc": "wonder, rhythmic cadence, 0.98x",
        "subtitle_fonts": ["Komika Axis", "Gilroy", "Montserrat", "Bebas Neue"],
        "c_base": "&H00F0FFF0&",          # Base: Honeydew Soft Organic White (#F0FFF0)
        "c_active": "&H0066FF00&",        # Active: Bioluminescent Lime (#00FF66)
        "c_power": "&H0000E6FF&",         # Power Accent: Sun Gold
        "outline_color": "&H00102005&",   # Outline: 8px #052010 (abyssal black-green)
        "shadow_color": "&H80081002&",    # Shadow: 3px
        "outline_w": 8,
        "shadow_d": 3,
        "blur": 0,
        "margin_v": 440,
        "procedural_chords": [
            [("E", "min"), ("G", "maj"), ("D", "maj"), ("C", "maj")],
            [("A", "min"), ("C", "maj"), ("G", "maj"), ("F", "maj")],
            [("D", "min"), ("A#", "maj"), ("F", "maj"), ("C", "maj")],
        ],
        "music_bpm": 92,
        "foley_type": "organic_nature",
        "ducking": {
            "attack": 40,
            "release": 350,
            "ratio": 2.8,
            "threshold": 0.09,
            "music_vol": 0.26,
            "sfx_vol": 0.25,
        },
        "container_metadata": {
            "artist": "BioSphere Explorations / Wild Earth Media",
            "genre": "Nature & Wildlife / Extreme Biology",
            "comment": "Documentary expedition exploring abyssal fauna, evolutionary adaptations, and planetary ecosystems.",
        },
        "color_curves": "eq=contrast=1.05:saturation=1.18:gamma=0.98,colorbalance=gs=0.05:gh=0.03:rh=0.02:bh=-0.03",
        "badge_text": "🌿 EXTREME NATURE",
        "badge_border": "#00FF66",
        "badge_bg": "#041408",
        "thumb_font": "Komika Axis",
        "thumb_color1": "#F0FFF0",
        "thumb_color2": "#00FF66",
        "thumb_border": "#052010",
    },
    "history": {
        "channel_id": "ch3",
        "name": "History & Warfare Tactics",
        "gemini_voice": "Charon",
        "kokoro_voice": "am_michael",
        "edge_voice": "en-US-ChristopherNeural",
        "cadence_speed": 0.96,
        "vocal_tone": "dark_revelation",
        "persona_desc": "grave, baritone historical storyteller, 0.96x",
        "subtitle_fonts": ["Cinzel", "TheBoldFont", "Bebas Neue"],
        "c_base": "&H00C7E8F5&",          # Base: Antique Parchment (#F5E8C7)
        "c_active": "&H0000D7FF&",        # Active: Imperial Gold (#FFD700)
        "c_power": "&H003333CC&",         # Power Accent: Imperial Crimson
        "outline_color": "&H00000A1A&",   # Outline: 9px #1A0A00 (bronze mahogany)
        "shadow_color": "&H8000050D&",    # Shadow: 4px
        "outline_w": 9,
        "shadow_d": 4,
        "blur": 2,
        "margin_v": 440,
        "procedural_chords": [
            [("A", "min"), ("D", "min"), ("E", "maj"), ("A", "min")],
            [("D", "min"), ("G", "min"), ("A", "maj"), ("D", "min")],
            [("E", "min"), ("B", "min"), ("C", "maj"), ("B", "maj")],
        ],
        "music_bpm": 80,
        "foley_type": "historical_warfare",
        "ducking": {
            "attack": 20,
            "release": 300,
            "ratio": 3.8,
            "threshold": 0.08,
            "music_vol": 0.24,
            "sfx_vol": 0.29,
        },
        "container_metadata": {
            "artist": "Chronos Archive / Historical Warfare Documentaries",
            "genre": "History & Military Strategy / Tactical Chronicles",
            "comment": "Declassified tactical warfare chronicles, ancient siege mechanics, and empire collapse records.",
        },
        "color_curves": "eq=contrast=1.10:saturation=0.95:gamma=0.93,colorbalance=rs=0.05:rh=0.06:gh=0.02:bs=-0.04:bh=-0.06",
        "badge_text": "⚔ DECLASSIFIED ARCHIVE",
        "badge_border": "#FFD700",
        "badge_bg": "#1A0800",
        "thumb_font": "Cinzel",
        "thumb_color1": "#F5E8C7",
        "thumb_color2": "#FFD700",
        "thumb_border": "#1A0A00",
    },
    "mystery": {
        "channel_id": "ch4",
        "name": "Mysteries & Unexplained",
        "gemini_voice": "Puck",
        "kokoro_voice": "am_fenrir",
        "edge_voice": "en-US-EricNeural",
        "cadence_speed": 1.00,
        "vocal_tone": "suspenseful_mystery",
        "persona_desc": "inquisitive, suspenseful, 1.00x",
        "subtitle_fonts": ["Montserrat Black", "Montserrat", "Archivo Black", "Bebas Neue"],
        "c_base": "&H00E0E0E0&",          # Base: Spectral Silver (#E0E0E0)
        "c_active": "&H0000FFDF&",        # Active: Acid Yellow (#DFFF00)
        "c_power": "&H00FF00B8&",         # Power Accent: Neon Violet
        "outline_color": "&H0014000B&",   # Outline: 10px #0B0014 (obsidian violet)
        "shadow_color": "&H6054003B&",    # Shadow: 4px Violet Drop Shadow (#3B0054)
        "outline_w": 10,
        "shadow_d": 4,
        "blur": 1,
        "margin_v": 440,
        "procedural_chords": [
            [("B", "min"), ("F", "min"), ("G", "maj"), ("C#", "min")],
            [("C", "min"), ("F#", "dim"), ("G#", "maj"), ("D", "min")],
            [("E", "min"), ("A#", "dim"), ("B", "min"), ("F", "maj")],
        ],
        "music_bpm": 104,
        "foley_type": "mystery_eerie",
        "ducking": {
            "attack": 30,
            "release": 400,
            "ratio": 3.0,
            "threshold": 0.10,
            "music_vol": 0.28,
            "sfx_vol": 0.26,
        },
        "container_metadata": {
            "artist": "Enigma Files / Anomalies & Unexplained",
            "genre": "Mystery & Investigation / Archaeological Paradoxes",
            "comment": "Declassified investigations into archaeological enigmas, geological anomalies, and unexplained paradoxes.",
        },
        "color_curves": "eq=contrast=1.12:saturation=0.92:gamma=0.90,colorbalance=bs=0.07:bm=-0.03:rs=-0.04:rh=0.03:bh=0.04",
        "badge_text": "👁 UNEXPLAINED FILE",
        "badge_border": "#DFFF00",
        "badge_bg": "#0B0014",
        "thumb_font": "Montserrat Black",
        "thumb_color1": "#E0E0E0",
        "thumb_color2": "#DFFF00",
        "thumb_border": "#0B0014",
    },
    "engineering": {
        "channel_id": "ch4",
        "name": "Marvel Engeneering (Engineering Marvels & How It Works)",
        "gemini_voice": "Orus",
        "kokoro_voice": "am_puck",
        "edge_voice": "en-US-BrianNeural",
        "cadence_speed": 1.04,
        "vocal_tone": "bold_authority",
        "persona_desc": "resonant, punchy industrial, 1.04x",
        "subtitle_fonts": ["Barlow Condensed", "Bebas Neue", "Anton"],
        "c_base": "&H00FFFFFF&",          # Base: Blueprint Titanium White (#FFFFFF)
        "c_active": "&H000055FF&",        # Active: Safety Orange (#FF5500)
        "c_power": "&H0000CCFF&",         # Power Accent: Hazard Yellow
        "outline_color": "&H00241E1A&",   # Outline: 9px #1A1E24 (machined dark slate)
        "shadow_color": "&H80120F0D&",    # Shadow: 3px Machine Slate Shadow
        "outline_w": 9,
        "shadow_d": 3,
        "blur": 0,
        "margin_v": 440,
        "procedural_chords": [
            [("C", "min"), ("D#", "maj"), ("F", "maj"), ("G", "min")],
            [("D", "min"), ("F", "maj"), ("G", "maj"), ("A", "min")],
            [("G", "min"), ("A#", "maj"), ("C", "maj"), ("D", "min")],
        ],
        "music_bpm": 130,
        "foley_type": "industrial_machinery",
        "ducking": {
            "attack": 12,
            "release": 150,
            "ratio": 4.5,
            "threshold": 0.06,
            "music_vol": 0.23,
            "sfx_vol": 0.32,
        },
        "container_metadata": {
            "artist": "Marvel Engeneering / Engineering Marvels & How It Works",
            "genre": "Engineering & Technology / Colossal Machines & Extreme Feats",
            "comment": "Documenting colossal machines, extreme kinetic mechanisms, and how impossible engineering feats work.",
        },
        "color_curves": "eq=contrast=1.12:saturation=1.16:gamma=0.94,colorbalance=rs=0.02:rh=0.05:gh=0.02:bs=0.04:bh=-0.03",
        "badge_text": "⚙ ENGINEERING MARVEL",
        "badge_border": "#FF5500",
        "badge_bg": "#101418",
        "thumb_font": "Barlow Condensed",
        "thumb_color1": "#FFFFFF",
        "thumb_color2": "#FF5500",
        "thumb_border": "#1A1E24",
    },
    "business": {
        "channel_id": "ch5",
        "name": "Mind Here Business (Business, Global Trade & Market Secrets)",
        "gemini_voice": "Charon",
        "kokoro_voice": "am_michael",
        "edge_voice": "en-US-ChristopherNeural",
        "cadence_speed": 1.02,
        "vocal_tone": "bold_authority",
        "persona_desc": "authoritative financial & trade investigator, 1.02x",
        "subtitle_fonts": ["Montserrat", "Montserrat Black", "Bebas Neue"],
        "c_base": "&H00FFFFFF&",          # Base: Pure Crisp White (#FFFFFF)
        "c_active": "&H00A3E500&",        # Active: Wealth Emerald (#00E5A3)
        "c_power": "&H0000D7FF&",         # Power Accent: Gold (#FFD700)
        "outline_color": "&H000A0805&",   # Outline: 9px #05080A (obsidian navy)
        "shadow_color": "&H80000000&",    # Shadow: 3px
        "outline_w": 9,
        "shadow_d": 3,
        "blur": 1,
        "margin_v": 440,
        "procedural_chords": [
            [("C", "min"), ("Ab", "maj"), ("Eb", "maj"), ("Bb", "maj")],
            [("D", "min"), ("Bb", "maj"), ("F", "maj"), ("C", "maj")],
            [("A", "min"), ("F", "maj"), ("C", "maj"), ("G", "maj")],
        ],
        "music_bpm": 112,
        "foley_type": "digital_tech",
        "ducking": {
            "attack": 20,
            "release": 250,
            "ratio": 3.8,
            "threshold": 0.08,
            "music_vol": 0.22,
            "sfx_vol": 0.28,
        },
        "container_metadata": {
            "artist": "Mind Here Business / Global Trade & Corporate Investigations",
            "genre": "Business & Economics / Global Trade & Market Secrets",
            "comment": "Investigative documentary series on global supply chain chokepoints, corporate monopolies, and market secrets.",
        },
        "color_curves": "eq=contrast=1.12:saturation=1.10:gamma=0.95,colorbalance=rs=0.03:gs=0.04:bs=-0.02",
        "badge_text": "$ TRADE SECRETS",
        "badge_border": "#00E5A3",
        "badge_bg": "#05120C",
        "thumb_font": "Montserrat",
        "thumb_color1": "#FFFFFF",
        "thumb_color2": "#00E5A3",
        "thumb_border": "#05080A",
    },
}

def get_channel_profile(niche: str = None) -> dict:
    if not niche:
        niche = os.environ.get("CHANNEL_NICHE", CHANNEL_NICHE).lower()
    return FLEET_NICHE_PROFILES.get(niche, FLEET_NICHE_PROFILES.get("science", {}))

# Niche-adaptive active voice settings
_curr_profile = get_channel_profile()
DEFAULT_GEMINI_VOICE = _curr_profile.get("gemini_voice", "Fenrir")
DEFAULT_EDGE_VOICE = _curr_profile.get("edge_voice", "en-US-AndrewNeural")
DEFAULT_KOKORO_VOICE = _curr_profile.get("kokoro_voice", "am_adam")
VOICE_PITCH = 0.0
VOICE_RATE = _curr_profile.get("cadence_speed", 1.02)

