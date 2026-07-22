#!/usr/bin/env python3
"""
SecondSelf — Phase 4: Graph Builder (The Cartographer)

Converts linked wiki notes into a nodes-and-edges JSON graph model
for visualization with vis-network.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

import frontmatter

from config import WIKI_DIR, GRAPH_PATH, PARA_CATEGORIES


# PARA color scheme for node visualization
PARA_COLORS = {
    "Projects": "#FF6B6B",
    "Areas": "#4ECDC4",
    "Resources": "#45B7D1",
    "Archives": "#96CEB4",
}


def parse_wiki_notes() -> List[Dict[str, Any]]:
    """
    Walk wiki/**/*.md, parse YAML frontmatter + body, and extract metadata.
    
    Returns:
        List of note dictionaries with: id, title, category, tags, links, body, content_preview
    """
    notes_dict = {}  # Use dict to deduplicate by ID
    wiki_path = Path(WIKI_DIR)
    
    if not wiki_path.exists():
        print(f"Warning: Wiki directory {wiki_path} does not exist")
        return []
    
    for md_file in wiki_path.rglob("*.md"):
        try:
            post = frontmatter.load(md_file)
            
            # Extract metadata
            note_id = post.get("id")
            title = post.get("title", md_file.stem)
            category = post.get("category", "Resources")
            tags = post.get("tags", [])
            links = post.get("links", [])
            body = post.content
            
            # Generate content preview (first 200 chars)
            content_preview = body[:200] if body else ""
            
            # Validate required fields
            if not note_id:
                print(f"Warning: {md_file} missing id, skipping")
                continue
            
            # Handle duplicate IDs - keep first occurrence
            if note_id in notes_dict:
                print(f"Warning: Duplicate ID {note_id} in {md_file}, skipping")
                continue
            
            notes_dict[note_id] = {
                "id": note_id,
                "title": title,
                "category": category,
                "tags": tags,
                "links": links,
                "body": body,
                "content_preview": content_preview,
                "path": str(md_file.relative_to(wiki_path)),
            }
        except Exception as e:
            print(f"Error parsing {md_file}: {e}")
    
    notes = list(notes_dict.values())
    print(f"Parsed {len(notes)} unique wiki notes")
    return notes


def extract_links(note: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract links from note frontmatter and [[wikilink]] patterns in body.
    
    Args:
        note: Note dictionary with 'links' and 'body' fields
        
    Returns:
        List of edge dictionaries: [{ source, target, similarity }]
    """
    edges = []
    note_id = note["id"]
    
    # Extract links from frontmatter
    frontmatter_links = note.get("links", [])
    for target_id in frontmatter_links:
        edges.append({
            "source": note_id,
            "target": target_id,
            "similarity": 1.0,  # Frontmatter links are explicit
        })
    
    # Parse [[wikilink]] patterns from body (e.g., from ## Related section)
    body = note.get("body", "")
    wikilink_pattern = r"\[\[([a-f0-9]+)\](?:\s*\(similarity:\s*([\d.]+)\))?"
    matches = re.findall(wikilink_pattern, body)
    
    for target_id, similarity_str in matches:
        similarity = float(similarity_str) if similarity_str else 0.8
        edges.append({
            "source": note_id,
            "target": target_id,
            "similarity": similarity,
        })
    
    return edges


def build_graph(notes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build graph structure from notes and edges.
    
    Args:
        notes: List of note dictionaries
        edges: List of edge dictionaries
        
    Returns:
        Graph dictionary with nodes, edges, and meta blocks
    """
    # Create node lookup
    node_ids = {note["id"] for note in notes}
    
    # Build nodes
    nodes = []
    for note in notes:
        category = note.get("category", "Resources")
        color = PARA_COLORS.get(category, "#45B7D1")
        
        nodes.append({
            "id": note["id"],
            "label": note["title"][:50],  # Truncate long titles
            "title": note["content_preview"],  # Hover tooltip
            "group": category,
            "color": color,
            "tags": note.get("tags", []),
            "category": category,
        })
    
    # Build edges (filter out edges to non-existent nodes)
    valid_edges = []
    for edge in edges:
        if edge["source"] in node_ids and edge["target"] in node_ids:
            valid_edges.append(edge)
    
    # Create meta block
    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "node_count": len(nodes),
        "edge_count": len(valid_edges),
    }
    
    graph = {
        "nodes": nodes,
        "edges": valid_edges,
        "meta": meta,
    }
    
    return graph


def validate_graph(graph: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and clean the graph:
    - Remove edges referencing non-existent node IDs
    - Deduplicate edges
    - Handle empty wiki gracefully
    
    Args:
        graph: Graph dictionary
        
    Returns:
        Validated and cleaned graph dictionary
    """
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    
    # Create node ID set
    node_ids = {node["id"] for node in nodes}
    
    # Remove orphan edges (edges referencing non-existent nodes)
    valid_edges = [
        edge for edge in edges
        if edge["source"] in node_ids and edge["target"] in node_ids
    ]
    
    # Deduplicate edges (keep undirected representation)
    edge_set = set()
    deduplicated_edges = []
    for edge in valid_edges:
        # Create a normalized key (undirected)
        key = tuple(sorted([edge["source"], edge["target"]]))
        if key not in edge_set:
            edge_set.add(key)
            deduplicated_edges.append(edge)
    
    # Update meta counts
    graph["edges"] = deduplicated_edges
    graph["meta"]["node_count"] = len(nodes)
    graph["meta"]["edge_count"] = len(deduplicated_edges)
    
    print(f"Validated graph: {len(nodes)} nodes, {len(deduplicated_edges)} edges")
    
    return graph


def export_graph(graph: Dict[str, Any], path: Path) -> None:
    """
    Write graph to JSON file with pretty printing.
    
    Args:
        graph: Graph dictionary
        path: Output file path
    """
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write JSON with pretty printing
    with open(path, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2, ensure_ascii=False)
    
    print(f"Graph exported to {path}")
    print(f"  Nodes: {graph['meta']['node_count']}")
    print(f"  Edges: {graph['meta']['edge_count']}")


def run_graph_pipeline() -> None:
    """
    Main pipeline: parse notes → extract links → build graph → validate → export.
    """
    print("=== Phase 4: Graph Builder ===")
    
    # Step 1: Parse wiki notes
    notes = parse_wiki_notes()
    
    if not notes:
        print("No notes found. Creating empty graph.")
        empty_graph = {
            "nodes": [],
            "edges": [],
            "meta": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "node_count": 0,
                "edge_count": 0,
            },
        }
        export_graph(empty_graph, GRAPH_PATH)
        return
    
    # Step 2: Extract links from all notes
    all_edges = []
    for note in notes:
        edges = extract_links(note)
        all_edges.extend(edges)
    
    print(f"Extracted {len(all_edges)} raw edges")
    
    # Step 3: Build graph
    graph = build_graph(notes, all_edges)
    
    # Step 4: Validate graph
    graph = validate_graph(graph)
    
    # Step 5: Export graph
    export_graph(graph, GRAPH_PATH)
    
    print("=== Graph Builder Complete ===")


if __name__ == "__main__":
    run_graph_pipeline()
