# src/extraction/signatures.py
import dspy
from dspy import InputField, OutputField

class ExtractReqs(dspy.Signature):
    """Given RFP chunk text, return a JSON array of requirement objects meaning any contract-like requirements
    or requests identified in the government proposal documents that a contractor responding to the RFP must address.
    Each object: {id,label,category,modality,quote,section,page_start,page_end,confidence}
    Categories ∈ {Technical, AdminFormat, Submission, Eligibility, Other}.
    Modality ∈ {SHALL,MUST,SHOULD,MAY,WILL,REQUIRED,PROHIBITED}.
    Only return JSON."""
    
    chunk_text: str = InputField(desc="The source text from a solicitation or instruction section.")
    requirements_json: str = OutputField(
        desc="A JSON array of requirement objects with fields: id, label, category, modality, quote, section, page_start, page_end",
        prefix="JSON:"
    )

class ClassifyReq(dspy.Signature):
    """Normalize a single requirement object: ensure category/modality and short label.
    Input: one requirement JSON object. Output: the corrected object (JSON)."""
    
    req_json: str = InputField(desc="A single requirement object as JSON string")
    classified_json: str = OutputField(
        desc="The normalized requirement object with corrected category and modality",
        prefix="JSON:"
    )

class GroundReq(dspy.Signature):
    """Given the requirement object and original chunk, return exact evidence:
    include start/end character offsets for the quote, refine pages/section if needed."""
    
    chunk_text: str = InputField(desc="The original chunk text containing the requirement")
    req_json: str = InputField(desc="The requirement object to ground with evidence")
    grounded_json: str = OutputField(
        desc="The requirement object with exact evidence including character offsets and refined location",
        prefix="JSON:"
    )
