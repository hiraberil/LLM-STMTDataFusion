import os

# ── API Keys (via .env or environment variables) ──────────────────────────────
_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

# ── Data Paths ───────────────────────────────────────────────────────────────
# Fill these in with your own local paths before running.
BOOK_CLAIMS_PATH = ""  # path to book claims file 
BOOK_TRUTH_PATH  = ""  # path to book truth file 

MOVIE_CLAIMS_PATH = ""  # path to movie claims file 
MOVIE_TRUTH_PATH  = ""  # path to movie truth file 

FLIGHT_CLAIMS_PATH = ""  # path to flight claims file 
FLIGHT_TRUTH_PATH  = ""  # path to flight truth file 

# ── LLM Settings ─────────────────────────────────────────────────────────────
LLM_PROVIDER = "openai"      # "openai" | "anthropic"
LLM_MODEL    = "gpt-4o-mini" # e.g. "gpt-4o", "claude-sonnet-4-6"

# ── Prompt Style ─────────────────────────────────────────────────────────────
PROMPT_DOMAIN = "dependent"  # set by run scripts at runtime
PROMPT_SHOT   = 0            # 0 | 1

# ── Output ────────────────────────────────────────────────────────────────────
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "results")
