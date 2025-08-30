# src/extraction/signatures.py
import dspy

class ExtractReqs(dspy.Signature):
    """Given RFP chunk text (1-8 pages), return a JSON array of requirement objects.
    Each object: {id,label,category,modality,quote,section,page_start,page_end,confidence}
    Categories ∈ {Technical, AdminFormat, Submission, Eligibility, Other}.
    Modality ∈ {SHALL,MUST,SHOULD,MAY,WILL,REQUIRED,PROHIBITED}.
    Only return JSON."""
    chunk_text: str
    json: str  # JSON array

class ClassifyReq(dspy.Signature):
    """Normalize a single requirement object: ensure category/modality and short label.
    Input: one requirement JSON object. Output: the corrected object (JSON)."""
    req_json: str
    json: str

class GroundReq(dspy.Signature):
    """Given the requirement object and original chunk, return exact evidence:
    include start/end character offsets for the quote, refine pages/section if needed."""
    chunk_text: str
    req_json: str
    json: str
