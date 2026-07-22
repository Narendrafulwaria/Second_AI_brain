#!/usr/bin/env python3
"""
SecondSelf — Phase 5B: RAG Q&A (The Oracle)

Implements retrieval-augmented generation to answer questions
using your personal knowledge base.
"""

import json
from pathlib import Path
from typing import Dict, List, Any

import numpy as np
from sentence_transformers import SentenceTransformer
from groq import Groq

from config import (
    EMBEDDINGS_DIR,
    WIKI_DIR,
    EMBEDDING_MODEL,
    RAG_TOP_K,
    GROQ_MODEL,
    require_groq_api_key,
)


# Global model cache
_embedding_model = None
_groq_client = None


def get_embedding_model() -> SentenceTransformer:
    """Load and cache the sentence transformer model."""
    global _embedding_model
    if _embedding_model is None:
        print(f"Loading embedding model: {EMBEDDING_MODEL}")
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    return _embedding_model


def get_groq_client() -> Groq:
    """Load and cache the Groq client."""
    global _groq_client
    if _groq_client is None:
        api_key = require_groq_api_key()
        _groq_client = Groq(api_key=api_key)
    return _groq_client


def load_all_embeddings() -> Dict[str, np.ndarray]:
    """
    Load all cached embedding vectors from data/embeddings/.
    
    Returns:
        Dictionary mapping note_id to embedding vector
    """
    embeddings = {}
    embeddings_path = Path(EMBEDDINGS_DIR)
    
    if not embeddings_path.exists():
        print(f"Warning: Embeddings directory {embeddings_path} does not exist")
        return embeddings
    
    for npy_file in embeddings_path.glob("*.npy"):
        note_id = npy_file.stem
        try:
            embeddings[note_id] = np.load(npy_file)
        except Exception as e:
            print(f"Error loading embedding {npy_file}: {e}")
    
    print(f"Loaded {len(embeddings)} embeddings")
    return embeddings


def load_wiki_notes() -> Dict[str, Dict[str, Any]]:
    """
    Load all wiki notes for content retrieval.
    
    Returns:
        Dictionary mapping note_id to note metadata
    """
    notes = {}
    wiki_path = Path(WIKI_DIR)
    
    if not wiki_path.exists():
        print(f"Warning: Wiki directory {wiki_path} does not exist")
        return notes
    
    import frontmatter
    
    for md_file in wiki_path.rglob("*.md"):
        try:
            post = frontmatter.load(md_file)
            note_id = post.get("id")
            if note_id:
                notes[note_id] = {
                    "id": note_id,
                    "title": post.get("title", md_file.stem),
                    "category": post.get("category", "Resources"),
                    "tags": post.get("tags", []),
                    "content": post.content,
                    "path": str(md_file.relative_to(wiki_path)),
                }
        except Exception as e:
            print(f"Error loading note {md_file}: {e}")
    
    print(f"Loaded {len(notes)} wiki notes")
    return notes


def retrieve_relevant_notes(
    question: str,
    embeddings: Dict[str, np.ndarray],
    top_k: int = RAG_TOP_K
) -> List[Dict[str, Any]]:
    """
    Retrieve the most relevant notes for a question using semantic similarity.
    
    Args:
        question: User's question
        embeddings: Dictionary of note_id to embedding vectors
        top_k: Number of top results to return
        
    Returns:
        List of relevant notes with similarity scores
    """
    if not embeddings:
        print("No embeddings available for retrieval")
        return []
    
    # Embed the question
    model = get_embedding_model()
    question_embedding = model.encode(question, convert_to_numpy=True)
    
    # Compute cosine similarity
    results = []
    for note_id, embedding in embeddings.items():
        # Normalize vectors for cosine similarity
        question_norm = question_embedding / np.linalg.norm(question_embedding)
        embedding_norm = embedding / np.linalg.norm(embedding)
        
        similarity = np.dot(question_norm, embedding_norm)
        results.append({
            "id": note_id,
            "score": float(similarity)
        })
    
    # Sort by similarity and return top-k
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def build_rag_prompt(question: str, notes: List[Dict[str, Any]]) -> str:
    """
    Build a RAG prompt with retrieved notes.
    
    Args:
        question: User's question
        notes: List of note dictionaries with content
        
    Returns:
        Formatted prompt for the LLM
    """
    context_parts = []
    for i, note in enumerate(notes, 1):
        context_parts.append(
            f"Note {i} (ID: {note['id']}):\n"
            f"Title: {note['title']}\n"
            f"Category: {note['category']}\n"
            f"Tags: {', '.join(note['tags'])}\n"
            f"Content: {note['content'][:1000]}\n"
        )
    
    context = "\n\n".join(context_parts)
    
    prompt = f"""You are a helpful assistant that answers questions based on the user's personal knowledge base. Use the provided notes to answer the question accurately. If the notes don't contain enough information to answer the question, say so clearly.

CONTEXT (from user's notes):
{context}

QUESTION: {question}

Answer the question based on the context above. Cite the specific notes you used by their ID. Be concise and direct."""
    
    return prompt


def synthesize_answer(prompt: str) -> str:
    """
    Send the prompt to Groq API and return the synthesized answer.
    
    Args:
        prompt: Formatted RAG prompt
        
    Returns:
        LLM-generated answer
    """
    client = get_groq_client()
    
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on provided context."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1024,
        )
        
        answer = response.choices[0].message.content
        return answer.strip()
    
    except Exception as e:
        print(f"Error calling Groq API: {e}")
        return "Sorry, I encountered an error generating the answer. Please try again."


def ask(question: str) -> Dict[str, Any]:
    """
    Main entry point: Ask a question and get an answer with source citations.
    
    Args:
        question: User's question
        
    Returns:
        Dictionary with answer, sources, and scores
    """
    print(f"Processing question: {question}")
    
    # Load embeddings and notes
    embeddings = load_all_embeddings()
    notes = load_wiki_notes()
    
    # Handle empty knowledge base
    if not embeddings:
        return {
            "answer": "I don't have any notes in your knowledge base yet. Please capture some notes first using capture.py.",
            "sources": [],
            "scores": []
        }
    
    # Retrieve relevant notes
    retrieved = retrieve_relevant_notes(question, embeddings)
    
    # Filter out low-relevance results
    retrieved = [r for r in retrieved if r["score"] > 0.3]
    
    if not retrieved:
        return {
            "answer": "I couldn't find any relevant information in your notes to answer this question.",
            "sources": [],
            "scores": []
        }
    
    # Get full note content for retrieved notes
    relevant_notes = []
    for r in retrieved:
        note_id = r["id"]
        if note_id in notes:
            relevant_notes.append({
                **notes[note_id],
                "score": r["score"]
            })
    
    # Build RAG prompt
    prompt = build_rag_prompt(question, relevant_notes)
    
    # Synthesize answer
    answer = synthesize_answer(prompt)
    
    # Format sources
    sources = [
        {
            "id": note["id"],
            "title": note["title"],
            "score": note["score"]
        }
        for note in relevant_notes
    ]
    
    scores = [r["score"] for r in retrieved]
    
    return {
        "answer": answer,
        "sources": sources,
        "scores": scores
    }


if __name__ == "__main__":
    # Test with a sample question
    import sys
    
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
    else:
        question = "What projects am I working on?"
    
    result = ask(question)
    print(f"\nQuestion: {question}")
    print(f"\nAnswer:\n{result['answer']}")
    print(f"\nSources:")
    for source in result['sources']:
        print(f"  - {source['title']} (score: {source['score']:.3f})")
