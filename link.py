import argparse
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Tuple
import frontmatter

from config import WIKI_DIR, EMBEDDINGS_DIR, EMBEDDING_MODEL, SIMILARITY_THRESHOLD, TOP_K_LINKS


# Global model instance (singleton pattern)
_embedding_model = None


def load_embedding_model():
    """
    Load sentence-transformers model: all-MiniLM-L6-v2
    Use singleton pattern — load once, reuse across calls.
    First run downloads ~80MB model weights.
    """
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        print(f"Loading embedding model: {EMBEDDING_MODEL}")
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        print("Embedding model loaded.")
    return _embedding_model


def compute_embedding(text: str, note_id: str, force: bool = False) -> np.ndarray:
    """
    Encode note body text → 384-dim numpy array
    Save to data/embeddings/{note_id}.npy
    Skip if embedding file already exists (unless --force flag)
    """
    embedding_path = EMBEDDINGS_DIR / f"{note_id}.npy"
    
    # Skip if already exists and not forcing recompute
    if embedding_path.exists() and not force:
        return np.load(embedding_path)
    
    # Compute embedding
    model = load_embedding_model()
    embedding = model.encode(text, show_progress_bar=False)
    
    # Save to disk
    embedding_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(embedding_path, embedding)
    
    return embedding


def load_all_embeddings() -> Dict[str, np.ndarray]:
    """
    Scan data/embeddings/*.npy
    Return dict: { note_id: numpy_array }
    """
    embeddings = {}
    
    if not EMBEDDINGS_DIR.exists():
        return embeddings
    
    for embedding_file in EMBEDDINGS_DIR.glob("*.npy"):
        note_id = embedding_file.stem
        try:
            embeddings[note_id] = np.load(embedding_file)
        except Exception as e:
            print(f"Warning: Could not load embedding for {note_id}: {e}")
    
    return embeddings


def find_similar(note_id: str, vector: np.ndarray, all_embeddings: Dict[str, np.ndarray], 
                 threshold: float = SIMILARITY_THRESHOLD) -> List[Tuple[str, float]]:
    """
    Compute cosine similarity against all other embeddings
    Exclude self-comparison
    Filter scores >= SIMILARITY_THRESHOLD (0.75)
    Return top TOP_K_LINKS (5) matches sorted by score
    """
    similarities = []
    
    for other_id, other_vector in all_embeddings.items():
        # Skip self-comparison
        if other_id == note_id:
            continue
        
        # Compute cosine similarity
        similarity = np.dot(vector, other_vector) / (np.linalg.norm(vector) * np.linalg.norm(other_vector))
        
        # Filter by threshold
        if similarity >= threshold:
            similarities.append((other_id, float(similarity)))
    
    # Sort by similarity score (descending)
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    # Return top K
    return similarities[:TOP_K_LINKS]


def insert_links(note_path: Path, linked_notes: List[Tuple[str, float]]) -> None:
    """
    Update frontmatter links: [id1, id2, ...]
    Append or update ## Related section with [[id]] wikilinks
    Include similarity score in link label (optional)
    """
    # Load the note
    post = frontmatter.load(note_path)
    
    # Update frontmatter links
    linked_ids = [note_id for note_id, _ in linked_notes]
    post['links'] = linked_ids
    
    # Build related section
    if linked_notes:
        # Check if there's already a ## Related section with our wikilink format
        has_existing_related = False
        lines = post.content.split('\n')
        
        # Look for ## Related followed by our specific format
        for i, line in enumerate(lines):
            if line.strip() == "## Related":
                # Check if next lines contain our wikilink format with similarity
                if i + 1 < len(lines) and "[[" in lines[i + 1] and "(similarity:" in lines[i + 1]:
                    has_existing_related = True
                    break
        
        # Only add if no existing related section with our format
        if not has_existing_related:
            related_section = "\n## Related\n"
            for note_id, score in linked_notes:
                related_section += f"- [[{note_id}]] (similarity: {score:.2f})\n"
            
            post.content += related_section
    
    # Write back
    with open(note_path, 'w', encoding='utf-8') as f:
        f.write(frontmatter.dumps(post))


def ensure_bidirectional_links(wiki_dir: Path, all_links: Dict[str, List[str]]) -> None:
    """
    When note A links to note B, also update note B to link back to note A
    Deduplicate — don't create duplicate links
    """
    for note_id, linked_ids in all_links.items():
        for linked_id in linked_ids:
            # Find the linked note file
            linked_note_file = find_note_file_by_id(wiki_dir, linked_id)
            if linked_note_file:
                # Load and update
                post = frontmatter.load(linked_note_file)
                current_links = post.get('links', [])
                
                # Add reverse link if not already present
                if note_id not in current_links:
                    current_links.append(note_id)
                    post['links'] = current_links
                    
                    # Write back
                    with open(linked_note_file, 'w', encoding='utf-8') as f:
                        f.write(frontmatter.dumps(post))


def find_note_file_by_id(wiki_dir: Path, note_id: str) -> Path:
    """Find a note file by its ID in the wiki directory."""
    for note_file in wiki_dir.rglob("*.md"):
        try:
            post = frontmatter.load(note_file)
            if post.get('id') == note_id:
                return note_file
        except Exception:
            continue
    return None


def run_linking_pipeline(force: bool = False) -> None:
    """
    Orchestrate: load wiki notes → compute embeddings → find similar → insert links
    Print summary of linking results
    """
    # Load all wiki notes
    wiki_notes = list(WIKI_DIR.rglob("*.md"))
    print(f"Found {len(wiki_notes)} wiki notes")
    
    if not wiki_notes:
        print("No wiki notes found to link.")
        return
    
    # Compute embeddings for all notes
    all_embeddings = {}
    for note_file in wiki_notes:
        try:
            post = frontmatter.load(note_file)
            note_id = post.get('id')
            if note_id:
                # Use both title and content for embedding
                text = post.get('title', '') + "\n" + post.content
                embedding = compute_embedding(text, note_id, force=force)
                all_embeddings[note_id] = embedding
        except Exception as e:
            print(f"Warning: Could not process {note_file}: {e}")
    
    print(f"Computed embeddings for {len(all_embeddings)} notes")
    
    # Find similar notes for each note
    all_links = {}
    for note_id, embedding in all_embeddings.items():
        similar_notes = find_similar(note_id, embedding, all_embeddings)
        if similar_notes:
            all_links[note_id] = [note_id for note_id, _ in similar_notes]
    
    # Insert links into notes
    linked_count = 0
    for note_file in wiki_notes:
        try:
            post = frontmatter.load(note_file)
            note_id = post.get('id')
            if note_id and note_id in all_links:
                similar_notes = find_similar(note_id, all_embeddings[note_id], all_embeddings)
                if similar_notes:
                    insert_links(note_file, similar_notes)
                    linked_count += 1
        except Exception as e:
            print(f"Warning: Could not update links for {note_file}: {e}")
    
    # Ensure bidirectional linking
    ensure_bidirectional_links(WIKI_DIR, all_links)
    
    print(f"Linking complete: {linked_count} notes updated with links")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto-link wiki notes using semantic similarity")
    parser.add_argument("--force", action="store_true", help="Recompute all embeddings")
    
    args = parser.parse_args()
    
    run_linking_pipeline(force=args.force)
