#!/usr/bin/env python3
"""
SecondSelf — Phase 5C: Streamlit App

Interactive web interface for the personal AI second brain.
Features: Knowledge graph visualization + Ask-your-brain Q&A.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

import requests
import streamlit as st
from bs4 import BeautifulSoup
from jinja2 import Template

# Try to use cloud config for Streamlit deployment, fall back to local config
try:
    from config_cloud import GRAPH_PATH, WIKI_DIR, PARA_CATEGORIES, RAW_DIR
except ImportError:
    from config import GRAPH_PATH, WIKI_DIR, PARA_CATEGORIES, RAW_DIR

from ask import ask


# Page configuration
st.set_page_config(
    page_title="SecondSelf — Your Personal AI Second Brain",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1a1a1a;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #333;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e0e0e0;
    }
    .source-card {
        background-color: #f8f9fa;
        border-left: 4px solid #45B7D1;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #666;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: 600;
        color: #333;
    }
</style>
""", unsafe_allow_html=True)


def load_graph() -> Dict[str, Any]:
    """
    Load the knowledge graph from data/graph.json.
    Auto-rebuild if missing.
    """
    graph_path = Path(GRAPH_PATH)
    
    if not graph_path.exists():
        st.warning("Graph not found. Building graph from wiki notes...")
        try:
            from build_graph import run_graph_pipeline
            run_graph_pipeline()
        except Exception as e:
            st.error(f"Failed to build graph: {e}")
            return {"nodes": [], "edges": [], "meta": {"node_count": 0, "edge_count": 0}}
    
    try:
        with open(graph_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Failed to load graph: {e}")
        return {"nodes": [], "edges": [], "meta": {"node_count": 0, "edge_count": 0}}


def render_graph(graph: Dict[str, Any]) -> str:
    """
    Render the interactive graph using vis-network.
    
    Args:
        graph: Graph dictionary with nodes and edges
        
    Returns:
        HTML string for the graph visualization
    """
    # Load the template
    template_path = Path(__file__).parent / "static" / "graph.html"
    
    if not template_path.exists():
        st.error("Graph template not found")
        return ""
    
    with open(template_path, 'r', encoding='utf-8') as f:
        template = Template(f.read())
    
    # Inject graph data
    graph_json = json.dumps(graph, ensure_ascii=False)
    html = template.render(graph_data=graph_json)
    
    return html


def get_wiki_stats() -> Dict[str, Any]:
    """
    Get statistics about the wiki notes.
    
    Returns:
        Dictionary with note counts by category
    """
    wiki_path = Path(WIKI_DIR)
    stats = {category: 0 for category in PARA_CATEGORIES}
    
    if not wiki_path.exists():
        return stats
    
    import frontmatter
    
    for category in PARA_CATEGORIES:
        category_path = wiki_path / category
        if category_path.exists():
            stats[category] = len(list(category_path.glob("*.md")))
    
    return stats


def generate_id() -> str:
    """Return an 8-character hex string from uuid.uuid4()."""
    return uuid.uuid4().hex[:8]


def get_timestamp() -> str:
    """Return UTC time in ISO 8601 format: 2026-07-16T10:30:00Z"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def extract_url_content(url: str) -> Dict[str, Any]:
    """Extract content from URL."""
    result = {"url": url}
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('title')
        if title:
            result["title"] = title.get_text().strip()
        # Extract first paragraph as preview
        first_p = soup.find('p')
        if first_p:
            result["preview"] = first_p.get_text().strip()[:200]
    except Exception as e:
        st.warning(f"Could not fetch link content: {e}")
    return result


def save_capture(capture: Dict[str, Any]) -> str:
    """Save capture to raw/ directory as JSON."""
    capture_id = capture["id"]
    timestamp = capture["timestamp"]
    
    # Sanitize timestamp for filesystem
    safe_timestamp = timestamp.replace(":", "-").replace("Z", "")
    filename = f"{capture_id}_{safe_timestamp}.json"
    filepath = RAW_DIR / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(capture, f, indent=2)
    
    return str(filepath)


def main():
    """Main Streamlit app."""
    
    # Header
    st.markdown('<h1 class="main-header">🧠 SecondSelf</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #666; font-size: 1.1rem;">Your Personal AI Second Brain</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📊 Knowledge Base Stats")
        
        # Load graph
        graph = load_graph()
        node_count = graph.get("meta", {}).get("node_count", 0)
        edge_count = graph.get("meta", {}).get("edge_count", 0)
        
        st.metric("Total Notes", node_count)
        st.metric("Total Links", edge_count)
        
        st.markdown("---")
        st.markdown("### 📁 Notes by Category")
        
        wiki_stats = get_wiki_stats()
        for category in PARA_CATEGORIES:
            count = wiki_stats.get(category, 0)
            st.markdown(f"**{category}**: {count}")
        
        st.markdown("---")
        st.markdown("### 🔄 Pipeline Status")
        
        if node_count > 0:
            st.success("✓ Graph built")
        else:
            st.warning("⚠ No notes yet")
        
        st.markdown("---")
        st.markdown("### 📖 Usage")
        st.markdown("""
1. **Capture**: Add notes via web interface or CLI
2. **Classify**: Run `classify.py` 
3. **Link**: Run `link.py`
4. **Graph**: Auto-updates here
5. **Ask**: Use the Q&A panel below
        """)
    
    # Main content area with tabs
    tab1, tab2, tab3 = st.tabs(["📝 Capture", "🧠 Knowledge Graph", "💬 Ask Your Brain"])
    
    # Tab 1: Capture
    with tab1:
        st.markdown('<h2 class="section-header">📝 Capture Notes</h2>', unsafe_allow_html=True)
        
        capture_type = st.radio("Capture Type", ["Text Note", "URL Link"], horizontal=True)
        
        if capture_type == "Text Note":
            note_content = st.text_area(
                "Enter your note:",
                placeholder="Write your note here...",
                height=150
            )
            
            if st.button("Capture Note", type="primary"):
                if note_content.strip():
                    capture = {
                        "id": generate_id(),
                        "timestamp": get_timestamp(),
                        "type": "note",
                        "content": note_content.strip()
                    }
                    filepath = save_capture(capture)
                    st.success(f"✓ Note captured successfully: {Path(filepath).name}")
                    st.rerun()
                else:
                    st.warning("Please enter a note.")
        
        else:  # URL Link
            url_input = st.text_input(
                "Enter URL:",
                placeholder="https://example.com/article"
            )
            
            if st.button("Capture Link", type="primary"):
                if url_input.strip():
                    with st.spinner("Fetching content..."):
                        content_data = extract_url_content(url_input.strip())
                        capture = {
                            "id": generate_id(),
                            "timestamp": get_timestamp(),
                            "type": "link",
                            **content_data
                        }
                        filepath = save_capture(capture)
                        st.success(f"✓ Link captured successfully: {Path(filepath).name}")
                        if "title" in content_data:
                            st.info(f"Title: {content_data['title']}")
                        st.rerun()
                else:
                    st.warning("Please enter a URL.")
        
        # Show recent captures
        st.markdown("---")
        st.markdown("### Recent Captures")
        
        raw_files = sorted(RAW_DIR.glob("*.json"), reverse=True)[:5]
        if raw_files:
            for filepath in raw_files:
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        capture = json.load(f)
                    
                    with st.expander(f"{capture['timestamp']} - {capture['type'].upper()}"):
                        if capture['type'] == 'note':
                            st.text(capture.get('content', ''))
                        elif capture['type'] == 'link':
                            st.markdown(f"**URL:** {capture.get('url', '')}")
                            if 'title' in capture:
                                st.markdown(f"**Title:** {capture['title']}")
                            if 'preview' in capture:
                                st.text(capture['preview'])
                except Exception as e:
                    st.error(f"Error reading {filepath.name}: {e}")
        else:
            st.info("No captures yet. Use the form above to add your first note.")
    
    # Tab 2: Knowledge Graph
    with tab2:
        st.markdown('<h2 class="section-header">🧠 Knowledge Graph</h2>', unsafe_allow_html=True)
        
        if node_count > 0:
            graph_html = render_graph(graph)
            st.components.v1.html(graph_html, height=650)
        else:
            st.info("""
            No notes in your knowledge base yet.
            
            To get started:
            1. Capture notes using the Capture tab
            2. Run `python classify.py`
            3. Run `python link.py`
            4. Refresh this page
            """)
    
    # Tab 3: Ask Your Brain
    with tab3:
        st.markdown('<h2 class="section-header">💬 Ask Your Brain</h2>', unsafe_allow_html=True)
        
        # Question input
        question = st.text_input(
            "Ask a question about your notes:",
            placeholder="e.g., What projects am I working on?",
            key="question_input"
        )
        
        # Ask button
        if st.button("Ask", key="ask_button", type="primary"):
            if question.strip():
                with st.spinner("Searching your knowledge base..."):
                    result = ask(question)
                    
                    # Display answer
                    st.markdown("### Answer")
                    st.markdown(result['answer'])
                    
                    # Display sources
                    if result['sources']:
                        st.markdown("### 📚 Sources")
                        for source in result['sources']:
                            st.markdown(f"""
                            <div class="source-card">
                                <strong>{source['title']}</strong><br/>
                                <small>Relevance: {source['score']:.2%}</small>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No relevant sources found in your notes.")
            else:
                st.warning("Please enter a question.")
        
        # Example questions
        st.markdown("---")
        st.markdown("### 💡 Example Questions")
        example_questions = [
            "What projects am I working on?",
            "What resources do I have about Python?",
            "What have I learned recently?",
            "What areas am I focusing on?",
        ]
        
        for q in example_questions:
            if st.button(q, key=f"example_{q}"):
                st.session_state.question_input = q
                st.rerun()


if __name__ == "__main__":
    main()
