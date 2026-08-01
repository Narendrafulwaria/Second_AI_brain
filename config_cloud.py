import os
from pathlib import Path

# Use Streamlit's persistent storage for cloud deployment
# Streamlit Cloud provides persistent storage at ~/mounts
if os.path.exists(os.path.expanduser("~/mounts")):
    ROOT = Path(os.path.expanduser("~/mounts/SecondSelf"))
else:
    # Fallback to local directory for local testing
    ROOT = Path(__file__).resolve().parent

RAW_DIR = ROOT / "raw"
RAW_PROCESSED_DIR = RAW_DIR / "processed"
WIKI_DIR = ROOT / "wiki"
EMBEDDINGS_DIR = ROOT / "data" / "embeddings"
GRAPH_PATH = ROOT / "data" / "graph.json"
STATIC_DIR = ROOT / "static"

PARA_CATEGORIES = ["Projects", "Areas", "Resources", "Archives"]

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

SIMILARITY_THRESHOLD = 0.75
TOP_K_LINKS = 5
RAG_TOP_K = 5

GROQ_MODEL = "llama-3.3-70b-versatile"

# Load from Streamlit secrets (environment variables)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")


def ensure_directories() -> None:
    """Create required project directories if they do not exist."""
    directories = [
        RAW_DIR,
        RAW_PROCESSED_DIR,
        WIKI_DIR,
        EMBEDDINGS_DIR,
        GRAPH_PATH.parent,
        STATIC_DIR,
        *[WIKI_DIR / category for category in PARA_CATEGORIES],
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def require_groq_api_key() -> str:
    """Return the Groq API key or raise a clear configuration error."""
    if not GROQ_API_KEY:
        raise EnvironmentError(
            "GROQ_API_KEY not found in Streamlit secrets. "
            "Please add GROQ_API_KEY to your app secrets in Streamlit Cloud."
        )
    return GROQ_API_KEY


ensure_directories()
