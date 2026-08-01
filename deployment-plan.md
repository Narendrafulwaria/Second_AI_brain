# Deployment Plan: SecondSelf on Streamlit Cloud

## Overview
This document outlines the steps to deploy the SecondSelf Personal AI Second Brain application to Streamlit Cloud.

## Prerequisites
- Active GitHub account with the project repository
- Groq API key (get one at https://console.groq.com/)
- Streamlit Cloud account (sign up at https://streamlit.io/cloud)

## Project Structure Analysis
```
PERSONAL_AI_SECOND_BRAIN/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── config.py              # Configuration and paths
├── ask.py                 # Q&A functionality
├── build_graph.py         # Knowledge graph builder
├── classify.py            # Note classification
├── link.py                # Note linking
├── capture.py             # Note capture
├── .env                   # Local environment variables (DO NOT commit)
├── .env.example           # Example environment variables
├── wiki/                  # Knowledge base notes (Projects, Areas, Resources, Archives)
├── data/                  # Embeddings and graph data
├── raw/                   # Raw captured notes
└── static/                # Static assets (HTML templates)
```

## Deployment Challenges & Solutions

### Challenge 1: Data Persistence
**Issue**: Streamlit Cloud doesn't persist local file system changes between deployments.

**Solution**: Use Streamlit's built-in file system persistence or external storage.

**Options**:
1. **Streamlit File System** (Recommended for small datasets)
   - Streamlit Cloud provides persistent storage at `~/mounts`
   - Modify `config.py` to use Streamlit's persistent directory
   - Max storage: 1GB per app

2. **External Storage** (For larger datasets)
   - Use GitHub for wiki notes (sync via git)
   - Use cloud storage (S3, GCS) for embeddings and graph data
   - Requires additional code modifications

### Challenge 2: Environment Variables
**Issue**: API keys and sensitive configuration need secure handling.

**Solution**: Use Streamlit Cloud's Secrets Management.

### Challenge 3: Heavy Dependencies
**Issue**: `sentence-transformers` and ML models are large and slow to download.

**Solution**: 
- Streamlit Cloud caches dependencies after first deployment
- Initial deployment may take 5-10 minutes
- Subsequent deployments are faster

## Deployment Steps

### Step 1: Prepare Repository

1. **Ensure `.gitignore` is properly configured**
```gitignore
.env
__pycache__/
*.pyc
venv/
data/embeddings/
data/graph.json
raw/processed/
wiki/.obsidian/
```

2. **Push to GitHub**
```bash
git add .
git commit -m "Prepare for Streamlit deployment"
git push origin master
```

3. **Verify `.env.example` exists**
```bash
# .env.example should contain:
GROQ_API_KEY=your_api_key_here
```

### Step 2: Configure Streamlit Cloud

1. **Deploy New App**
   - Go to https://share.streamlit.io/
   - Click "New app"
   - Select your GitHub repository
   - Select branch: `master`
   - Main file path: `app.py`

2. **Configure Secrets**
   - In Streamlit Cloud dashboard, go to "Secrets"
   - Add the following:
```toml
GROQ_API_KEY = "your_actual_groq_api_key"
```

3. **Advanced Settings** (if needed)
   - Python version: 3.11 or 3.12
   - Max workers: 1 (default is fine for this app)

### Step 3: Modify Code for Cloud Deployment

**Create `config_cloud.py`** (cloud-specific configuration):
```python
import os
from pathlib import Path
from dotenv import load_dotenv

# Use Streamlit's persistent storage
if os.path.exists("~/mounts"):
    ROOT = Path("~/mounts/SecondSelf").expanduser()
else:
    ROOT = Path(__file__).resolve().parent

RAW_DIR = ROOT / "raw"
RAW_PROCESSED_DIR = RAW_DIR / "processed"
WIKI_DIR = ROOT / "wiki"
EMBEDDINGS_DIR = ROOT / "data" / "embeddings"
GRAPH_PATH = ROOT / "data" / "graph.json"
STATIC_DIR = ROOT / "static"

# Ensure directories exist on first run
def ensure_directories() -> None:
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

PARA_CATEGORIES = ["Projects", "Areas", "Resources", "Archives"]
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
SIMILARITY_THRESHOLD = 0.75
TOP_K_LINKS = 5
RAG_TOP_K = 5
GROQ_MODEL = "llama-3.3-70b-versatile"

# Load from Streamlit secrets
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

def require_groq_api_key() -> str:
    if not GROQ_API_KEY:
        raise EnvironmentError("GROQ_API_KEY not found in Streamlit secrets")
    return GROQ_API_KEY

ensure_directories()
```

**Update `app.py`** to handle cloud environment:
```python
# At the top of app.py, modify imports:
try:
    from config_cloud import *  # Use cloud config on Streamlit
except ImportError:
    from config import *  # Fall back to local config
```

### Step 4: Initial Data Setup

Since Streamlit Cloud starts with empty data, you need to populate it:

**Option A: Manual Setup via Web Interface**
1. Deploy the app
2. Use the capture functionality to add initial notes
3. Run classification and linking manually

**Option B: Pre-populate Data**
1. Create a data initialization script:
```python
# init_data.py
import shutil
from pathlib import Path

# Copy local wiki to cloud
local_wiki = Path("wiki")
cloud_wiki = Path("~/mounts/SecondSelf/wiki").expanduser()
if local_wiki.exists():
    shutil.copytree(local_wiki, cloud_wiki, dirs_exist_ok=True)

# Copy local embeddings if they exist
local_embeddings = Path("data/embeddings")
cloud_embeddings = Path("~/mounts/SecondSelf/data/embeddings").expanduser()
if local_embeddings.exists():
    shutil.copytree(local_embeddings, cloud_embeddings, dirs_exist_ok=True)

print("Data initialized successfully")
```

2. Run this script after first deployment (via Streamlit's temporary terminal or locally)

### Step 5: Update `requirements.txt` for Cloud

Ensure your `requirements.txt` is optimized:
```
streamlit>=1.30.0
groq>=0.4.0
sentence-transformers>=2.3.0
numpy>=1.24.0
scikit-learn>=1.3.0
pyyaml>=6.0
requests>=2.31.0
beautifulsoup4>=4.12.0
python-frontmatter>=1.0.0
python-dotenv>=1.0.0
jinja2>=3.1.0
```

## Post-Deployment Checklist

- [ ] App loads successfully at the provided URL
- [ ] GROQ_API_KEY is properly configured in secrets
- [ ] Knowledge graph displays correctly
- [ ] Q&A functionality works
- [ ] Note capture works
- [ ] Data persists between app restarts
- [ ] Wiki notes are accessible

## Monitoring and Maintenance

### Regular Tasks
1. **Monitor Usage**: Check Streamlit Cloud dashboard for resource usage
2. **Update Dependencies**: Keep `requirements.txt` updated
3. **Backup Data**: Regularly export wiki notes to GitHub
4. **API Key Rotation**: Update GROQ_API_KEY in secrets if needed

### Troubleshooting

**Issue: App fails to start**
- Check Streamlit Cloud logs
- Verify all dependencies are in `requirements.txt`
- Ensure Python version compatibility

**Issue: Data not persisting**
- Verify persistent storage path is correct
- Check file permissions
- Ensure directories are created on startup

**Issue: API errors**
- Verify GROQ_API_KEY is set in secrets
- Check Groq API status
- Review rate limits

**Issue: Slow performance**
- Consider reducing embedding model size
- Implement caching for frequently accessed data
- Optimize graph rendering

## Alternative Deployment Options

### Option 1: Streamlit Community Cloud (Free)
- Pros: Free, easy setup
- Cons: Limited resources, no custom domains
- Best for: Personal use, testing

### Option 2: Streamlit Cloud (Paid)
- Pros: More resources, priority support
- Cons: Monthly cost
- Best for: Production use

### Option 3: Self-hosted (Docker)
- Pros: Full control, no resource limits
- Cons: Requires server management
- Best for: Advanced users, enterprise

## Cost Estimation

**Streamlit Community Cloud (Free)**
- $0/month
- 1GB persistent storage
- Community support

**Streamlit Cloud (Paid)**
- Starts at $20/month
- More storage and compute
- Priority support

## Security Considerations

1. **Never commit `.env` file** to GitHub
2. **Use Streamlit Secrets** for all sensitive data
3. **Regularly rotate API keys**
4. **Implement rate limiting** for API calls
5. **Use HTTPS** (Streamlit provides this by default)

## Scaling Considerations

For future scaling:
1. **Database Integration**: Replace file-based storage with a database
2. **CDN for Static Assets**: Serve large files via CDN
3. **Load Balancing**: Use multiple instances if needed
4. **Caching**: Implement Redis for caching embeddings

## Rollback Plan

If deployment fails:
1. Revert to previous commit on GitHub
2. Streamlit Cloud will auto-redeploy
3. Restore data from backup if needed

## Contact and Support

- Streamlit Cloud Documentation: https://docs.streamlit.io/streamlit-cloud
- Groq API Documentation: https://console.groq.com/docs
- Project Repository: https://github.com/Narendrafulwaria/Second_AI_brain

## Timeline Estimate

- **Preparation**: 30 minutes
- **Initial Deployment**: 15 minutes
- **Configuration**: 30 minutes
- **Testing**: 1 hour
- **Total**: ~2.5 hours

## Success Criteria

Deployment is successful when:
- App is accessible via public URL
- All core features work (graph, Q&A, capture)
- Data persists between sessions
- Performance is acceptable (<5s load time)
- No critical errors in logs
