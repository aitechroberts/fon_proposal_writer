# src/matrix/export.py
import json
import csv
from pathlib import Path
from typing import List, Dict, Any

def save_json(requirements: List[Dict[Any, Any]], output_path: str) -> None:
    """Save requirements to JSON file with proper formatting."""
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(requirements, f, indent=2, ensure_ascii=False)
    except Exception as e:
        raise RuntimeError(f"Failed to save JSON to {output_path}: {e}")

def save_csv(requirements: List[Dict[Any, Any]], output_path: str) -> None:
    """Save requirements to CSV file with standard columns."""
    if not requirements:
        return
    
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Define standard columns for compliance matrix
        columns = [
            "id", "label", "category", "modality", "section", 
            "page_start", "page_end", "quote", "confidence", "source"
        ]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
            writer.writeheader()
            
            for req in requirements:
                # Ensure all required fields exist with defaults
                row = {col: req.get(col, "") for col in columns}
                writer.writerow(row)
                
    except Exception as e:
        raise RuntimeError(f"Failed to save CSV to {output_path}: {e}")