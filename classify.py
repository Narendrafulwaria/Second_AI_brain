import json
import time
from pathlib import Path
from typing import List, Dict, Any

# Try to use cloud config for Streamlit deployment, fall back to local config
try:
    from config_cloud import RAW_DIR, RAW_PROCESSED_DIR, PARA_CATEGORIES, require_groq_api_key, GROQ_MODEL
except ImportError:
    from config import RAW_DIR, RAW_PROCESSED_DIR, PARA_CATEGORIES, require_groq_api_key, GROQ_MODEL


def load_raw_captures() -> List[Dict[str, Any]]:
    """
    Scan raw/*.json for unprocessed captures.
    Skip files in raw/processed/ (if using move-on-process strategy).
    Return list of parsed capture dicts.
    """
    captures = []
    
    # Get all JSON files in raw directory
    raw_files = list(RAW_DIR.glob("*.json"))
    
    # Get already processed files (if they exist in processed directory)
    processed_files = set()
    if RAW_PROCESSED_DIR.exists():
        processed_files = {f.name for f in RAW_PROCESSED_DIR.glob("*.json")}
    
    # Load unprocessed captures
    for filepath in raw_files:
        # Skip if already processed
        if filepath.name in processed_files:
            continue
        
        # Skip .gitkeep file
        if filepath.name == ".gitkeep":
            continue
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                capture = json.load(f)
                captures.append(capture)
        except Exception as e:
            print(f"Warning: Could not load {filepath}: {e}")
    
    return captures


def classify_capture(content: str) -> Dict[str, Any]:
    """
    Build PARA classification prompt, call Groq API with llama3-8b-8192,
    parse JSON response: { "category", "tags", "summary" }.
    Retry up to 3 times on timeout; fallback to Resources on parse failure.
    """
    from groq import Groq
    
    api_key = require_groq_api_key()
    client = Groq(api_key=api_key)
    
    prompt = f"""You are a knowledge organizer. Classify this capture using the PARA method.

PARA categories:
- Projects: active work with a deadline
- Areas: ongoing responsibilities  
- Resources: topics of interest for future reference
- Archives: inactive items

Return JSON: {{ "category": "...", "tags": [...], "summary": "..." }}

Capture:
{content}"""
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful knowledge organizer that responds only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            classification = json.loads(result_text)
            
            # Validate required fields
            if "category" not in classification or "tags" not in classification or "summary" not in classification:
                raise ValueError("Missing required fields in classification response")
            
            # Ensure category is valid
            if classification["category"] not in PARA_CATEGORIES:
                classification["category"] = "Resources"
            
            # Ensure tags is a list
            if not isinstance(classification["tags"], list):
                classification["tags"] = []
            
            return classification
            
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Retry {attempt + 1}/{max_retries} for classification: {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                print(f"Classification failed after {max_retries} attempts: {e}")
                # Fallback to Resources
                return {
                    "category": "Resources",
                    "tags": [],
                    "summary": "Classification failed - auto-generated summary"
                }


def slugify(summary: str) -> str:
    """
    Convert summary to filesystem-safe slug: my-idea-about-rag.md
    Truncate to 60 chars, lowercase, replace spaces with hyphens.
    """
    import re
    
    # Remove special characters, keep only alphanumeric and spaces
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', summary)
    
    # Replace spaces with hyphens
    slug = slug.replace(' ', '-')
    
    # Convert to lowercase
    slug = slug.lower()
    
    # Remove consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    # Truncate to 60 chars
    if len(slug) > 60:
        slug = slug[:60].rstrip('-')
    
    # Ensure we have something
    if not slug:
        slug = "untitled"
    
    return slug + ".md"


def write_wiki_note(capture: Dict[str, Any], classification: Dict[str, Any]) -> str:
    """
    Determine target path: wiki/{category}/{slug}.md
    Write YAML frontmatter + body per architecture §4.2
    Carry id and created from raw capture
    Initialize links: [] (populated in Phase 3)
    """
    from config import WIKI_DIR
    
    # Extract fields
    capture_id = capture["id"]
    timestamp = capture["timestamp"]
    category = classification["category"]
    tags = classification["tags"]
    summary = classification["summary"]
    
    # Get content from capture (handle different types)
    if capture["type"] == "note":
        content = capture.get("content", "")
    elif capture["type"] == "link":
        content = f"URL: {capture.get('url', '')}\n"
        if "title" in capture:
            content += f"Title: {capture['title']}\n"
        if "preview" in capture:
            content += f"Preview: {capture['preview']}\n"
    elif capture["type"] == "file":
        content = f"File: {capture.get('filename', '')}\n"
        if "content" in capture:
            content += capture["content"]
        else:
            content += f"Path: {capture.get('path', '')}\n"
    else:
        content = ""
    
    # Generate slug from summary
    slug = slugify(summary)
    
    # Determine target directory
    category_dir = WIKI_DIR / category
    category_dir.mkdir(parents=True, exist_ok=True)
    
    # Build filepath
    filepath = category_dir / slug
    
    # Build YAML frontmatter
    frontmatter = f"""---
id: {capture_id}
title: "{summary}"
category: {category}
tags: {tags}
created: {timestamp}
links: []
embedding_id: {capture_id}
---

"""
    
    # Write file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(frontmatter)
        f.write(content)
    
    return str(filepath)


def mark_processed(capture_path: str) -> None:
    """
    Move raw JSON to raw/processed/ OR add "processed": true flag
    Prevents re-classification on subsequent runs.
    """
    from config import RAW_PROCESSED_DIR
    
    # Ensure processed directory exists
    RAW_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    source_path = Path(capture_path)
    if not source_path.exists():
        print(f"Warning: Source file not found: {capture_path}")
        return
    
    # Move to processed directory
    destination_path = RAW_PROCESSED_DIR / source_path.name
    
    try:
        import shutil
        shutil.move(str(source_path), str(destination_path))
    except Exception as e:
        print(f"Warning: Could not move {capture_path} to processed: {e}")


def run_classification_pipeline() -> None:
    """
    Orchestrate: load → classify → write → mark processed
    Print summary: Classified 12 captures → wiki/
    """
    # Load unprocessed captures
    captures = load_raw_captures()
    
    if not captures:
        print("No unprocessed captures found.")
        return
    
    print(f"Processing {len(captures)} captures...")
    
    classified_count = 0
    failed_count = 0
    
    for capture in captures:
        try:
            # Prepare content for classification
            if capture["type"] == "note":
                content = capture.get("content", "")
            elif capture["type"] == "link":
                content = f"URL: {capture.get('url', '')}\n"
                if "title" in capture:
                    content += f"Title: {capture['title']}\n"
                if "preview" in capture:
                    content += f"Preview: {capture['preview']}\n"
            elif capture["type"] == "file":
                content = f"File: {capture.get('filename', '')}\n"
                if "content" in capture:
                    content += capture["content"]
            else:
                content = ""
            
            # Classify the capture
            classification = classify_capture(content)
            
            # Write wiki note
            wiki_path = write_wiki_note(capture, classification)
            
            # Mark as processed
            raw_filename = f"{capture['id']}_{capture['timestamp'].replace(':', '-').replace('Z', '')}.json"
            raw_path = str(RAW_DIR / raw_filename)
            mark_processed(raw_path)
            
            print(f"[OK] {capture['id']} -> {classification['category']}: {wiki_path}")
            classified_count += 1
            
        except Exception as e:
            print(f"[FAIL] Failed to process {capture['id']}: {e}")
            failed_count += 1
    
    print(f"\nClassification complete: {classified_count} classified, {failed_count} failed")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Classify raw captures into PARA-organized wiki notes")
    parser.add_argument("--force", action="store_true", help="Force reclassification of already processed captures")
    
    args = parser.parse_args()
    
    if args.force:
        print("Force mode: Moving processed files back to raw/ for reclassification...")
        # Move all files from processed back to raw
        if RAW_PROCESSED_DIR.exists():
            import shutil
            for file in RAW_PROCESSED_DIR.glob("*.json"):
                dest = RAW_DIR / file.name
                shutil.move(str(file), str(dest))
            print(f"Moved {len(list(RAW_PROCESSED_DIR.glob('*.json')))} files back to raw/")
    
    # Run the classification pipeline
    run_classification_pipeline()
