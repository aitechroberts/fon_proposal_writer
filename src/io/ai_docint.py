import os, io
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient

_ENDPOINT = os.getenv("DOCUMENTINTELLIGENCE_ENDPOINT")
_KEY      = os.getenv("DOCUMENTINTELLIGENCE_API_KEY")

_client = DocumentIntelligenceClient(_ENDPOINT, AzureKeyCredential(_KEY))

def extract_tables_and_forms(pdf_path: str):
    # LRO pattern per SDK
    with open(pdf_path, "rb") as f:
        poller = _client.begin_analyze_document("prebuilt-layout", body=f)
    result = poller.result()  # includes pages, paragraphs, tables, styles, etc.

    # Flatten tables to simple dicts; optionally feed into LLM stage as structured hints
    tables = []
    for t in result.tables or []:
        grid = []
        for r in t.cells:
            # Collect by row index
            while len(grid) <= r.row_index:
                grid.append([])
            grid[r.row_index].append((r.column_index, r.content))
        # sort columns per row
        grid = [ [c for _, c in sorted(row, key=lambda x: x[0])] for row in grid ]
        tables.append({"page": (t.bounding_regions or [])[0].page_number if t.bounding_regions else None,
                       "rows": grid})
    return {"tables": tables, "styles": getattr(result, "styles", None)}
