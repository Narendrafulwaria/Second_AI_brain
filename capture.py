import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

import requests
from bs4 import BeautifulSoup

from config import RAW_DIR


def generate_id() -> str:
    """Return an 8-character hex string from uuid.uuid4()."""
    return uuid.uuid4().hex[:8]


def get_timestamp() -> str:
    """Return UTC time in ISO 8601 format: 2026-07-16T10:30:00Z"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def detect_type(args: argparse.Namespace) -> str:
    """Parse CLI arguments and return 'note', 'link', or 'file'."""
    provided = [args.note, args.link, args.file]
    count = sum(1 for x in provided if x is not None)
    
    if count == 0:
        raise ValueError("Must provide one of: --note, --link, --file")
    if count > 1:
        raise ValueError("Must provide exactly one of: --note, --link, --file")
    
    if args.note is not None:
        return "note"
    elif args.link is not None:
        return "link"
    else:
        return "file"


def extract_content(capture_type: str, source: str) -> Dict[str, Any]:
    """Extract content based on capture type."""
    if capture_type == "note":
        return {"content": source}
    
    elif capture_type == "link":
        # Store URL as source, optionally fetch page title/text
        result = {"url": source}
        try:
            response = requests.get(source, timeout=10)
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
            print(f"Warning: Could not fetch link content: {e}")
        return result
    
    elif capture_type == "file":
        file_path = Path(source)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {source}")
        
        # Try to read as text file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {"content": content, "filename": file_path.name}
        except UnicodeDecodeError:
            # Binary file - store reference only
            return {"filename": file_path.name, "path": str(file_path), "binary": True}
    
    else:
        raise ValueError(f"Unknown capture type: {capture_type}")


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
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Capture notes, links, or files into SecondSelf")
    parser.add_argument("--note", type=str, help="Capture a text note")
    parser.add_argument("--link", type=str, help="Capture a URL link")
    parser.add_argument("--file", type=str, help="Capture a file")
    
    args = parser.parse_args()
    
    try:
        # Detect capture type
        capture_type = detect_type(args)
        
        # Get source based on type
        if capture_type == "note":
            source = args.note
        elif capture_type == "link":
            source = args.link
        else:
            source = args.file
        
        # Extract content
        content_data = extract_content(capture_type, source)
        
        # Build capture object
        capture = {
            "id": generate_id(),
            "timestamp": get_timestamp(),
            "type": capture_type,
            **content_data
        }
        
        # Save capture
        filepath = save_capture(capture)
        print(f"Captured: {filepath}")
        
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
