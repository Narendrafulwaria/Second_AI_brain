# SecondSelf - Personal AI Second Brain

An intelligent knowledge management system that captures, classifies, links, and visualizes your personal notes using AI. Built with Streamlit, Groq API, and sentence-transformers.

## Features

- **Smart Note Capture**: Capture notes via text or URL with automatic content extraction
- **AI-Powered Classification**: Automatically categorize notes using PARA method (Projects, Areas, Resources, Archives)
- **Semantic Linking**: Automatically find and create links between related notes using embeddings
- **Knowledge Graph Visualization**: Interactive graph showing connections between your notes
- **Q&A System**: Ask questions about your knowledge base with RAG (Retrieval-Augmented Generation)
- **Web Interface**: Beautiful Streamlit-based UI for all operations

## Architecture

The system follows a pipeline approach:
1. **Capture** → `capture.py` - Ingest notes from various sources
2. **Classify** → `classify.py` - Categorize using PARA method
3. **Link** → `link.py` - Create semantic connections
4. **Graph** → `build_graph.py` - Build visualization
5. **Ask** → `ask.py` - Query your knowledge base
6. **App** → `app.py` - Web interface

## Local Installation

### Prerequisites

- Python 3.11 or higher
- Groq API key (get one tại [console.groq.com](https://console.groq.com/))

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/Narendrafulwaria/Second_AI_brain.git
cd Second_AI_brain
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

5. **Run the application**
```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`

## Usage

### Capturing Notes

**Text Note:**
```bash
python capture.py --note "Your note content here"
```

**URL Note:**
```bash
python capture.py --url "https://example.com/article"
```

### Processing Pipeline

After capturing notes, run the processing pipeline:

1. **Classify notes**
```bash
python classify.py
```

2. **Link related notes**
```bash
python link.py
```

3. **Build knowledge graph**
```bash
python build_graph.py
```

The Streamlit app will automatically rebuild the graph when needed.

### Using the Web Interface

1. **Knowledge Graph**: Visualize connections between your notes
2. **Ask Your Brain**: Query your knowledge base with natural language
3. **Statistics**: View note counts by category in the sidebar

## Deployment on Streamlit Cloud

### Quick Deploy

1. **Push to GitHub**
```bash
git add .
git commit -m "Prepare for deployment"
git push origin master
```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io/)
   - Click "New app"
   - Select your repository
   - Main file: `app.py`

3. **Configure Secrets**
   - In Streamlit Cloud dashboard, add to Secrets:
```toml
GROQ_API_KEY = "your_actual_api_key"
```

### Cloud-Specific Configuration

The project includes `config_cloud.py` which automatically:
- Uses Streamlit's persistent storage (`~/mounts`)
- Loads API keys from environment variables
- Creates necessary directories on startup

All Python files automatically detect the cloud environment and use the appropriate configuration.

### Data Persistence

Streamlit Cloud provides 1GB of persistent storage. The app automatically:
- Stores wiki notes in persistent storage
- Saves embeddings and graph data
- Maintains data between deployments

For larger datasets, consider external storage solutions (see `deployment-plan.md`).

## Project Structure

```
PERSONAL_AI_SECOND_BRAIN/
├── app.py                  # Main Streamlit application
├── config.py              # Local configuration
├── config_cloud.py        # Cloud configuration
├── capture.py             # Note capture
├── classify.py            # PARA classification
├── link.py                # Semantic linking
├── build_graph.py         # Graph builder
├── ask.py                 # RAG Q&A system
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── wiki/                 # Knowledge base notes
│   ├── Projects/
│   ├── Areas/
│   ├── Resources/
│   └── Archives/
├── data/                 # Generated data
│   ├── embeddings/
│   └── graph.json
├── raw/                  # Captured notes
│   └── processed/
└── static/               # Static assets
```

## Configuration

### Environment Variables

- `GROQ_API_KEY`: Required for AI classification and Q&A
- Get your key at [console.groq.com](https://console.groq.com/)

### Settings (in config.py)

- `EMBEDDING_MODEL`: Sentence transformer model (default: all-MiniLM-L6-v2)
- `SIMILARITY_THRESHOLD`: Minimum similarity for linking (default: 0.75)
- `TOP_K_LINKS`: Number of links to create per note (default: 5)
- `RAG_TOP_K`: Number of results for Q&A (default: 5)
- `GROQ_MODEL`: Groq model for AI tasks (default: llama-3.3-70b-versatile)

## Troubleshooting

### API Key Issues
```bash
python test_api_key.py
```

### Graph Not Displaying
- Ensure you've run the full pipeline (capture → classify → link → build_graph)
- Check that `data/graph.json` exists

### Import Errors
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version (3.11+ required)

### Cloud Deployment Issues
- Verify GROQ_API_KEY is set in Streamlit Cloud secrets
- Check Streamlit Cloud logs for errors
- Ensure all files are committed to GitHub

## Development

### Running Tests
```bash
python test_api_key.py
python verify_phase1.py
```

### Adding New Features
- Follow the existing pipeline structure
- Update both `config.py` and `config_cloud.py` for new settings
- Add cloud config imports to new Python files

## Documentation

- `deployment-plan.md` - Detailed deployment guide
- `architecture.md` - System architecture
- `implementation.md` - Implementation phases
- `problemstatement.md` - Project problem statement

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions:
- GitHub Issues: [Second_AI_brain/issues](https://github.com/Narendrafulwaria/Second_AI_brain/issues)
- Streamlit Documentation: [docs.streamlit.io](https://docs.streamlit.io/)
- Groq API Documentation: [console.groq.com/docs](https://console.groq.com/docs)

## Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- AI powered by [Groq](https://groq.com/)
- Embeddings by [sentence-transformers](https://www.sbert.net/)
- PARA method by [Tiago Forte](https://buildingasecondbrain.com/)
