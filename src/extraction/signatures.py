# src/extraction/signatures.py
import dspy
from dspy import InputField, OutputField

class ExtractReqs(dspy.Signature):
    """You are a Federal proposal compliance analyst. Read all attached solicitation files (RFP Sections A–M, SOW/PWS, CDRLs, amendments, attachments). Prioritize Section L (Instructions) and Section M (Evaluation).
Deliver a BD-style “Submission Compliance Checklist” workbook with the following tabs and schemas. Cite the exact source for every row as: DocName, Section/Para, Page. If anything is not stated, write “MISSING” (don’t guess).

Tab 1 - Volumes & Tabs (authoritative spine)
Columns: Volume, Tab, Title/Topic, What to Provide (verbatim/summary), Page/Slide Limit, Format (PDF/Word/PPT/Excel), Font/Margins/Spacing, Required File Naming, Submission Destination (Portal/Email), Due (Date, Time, Time Zone), Owner, Source Citation, Notes.
- Capture exact volume/tab structure, mandatory contents per tab, and constraints.
- Include file-type rules (allowed/prohibited), email size limits, labeling conventions (“1 of 3”), ZIP allowed?

Tab 2 - Submission Logistics
Columns: Due Date/Time/TZ, Questions Due, Addenda Cutoff, Submission Method (Portal/Email+Address/URL), Subject-Line Format, Copy To, Validity Period (e.g., 90 days), Place of Delivery, Special Packaging/Labeling, Source Citation.

Tab 3 - Page/Slide & Formatting Rules
Columns: Applies To (Vol/Tab/All), Page/Slide Limit, Font, Size (pt), Margins, Spacing, Figures/Tables Count Toward Limit?, Appendices Allowed?, Source Citation.

Tab 4 - Orals (if applicable)
Columns: Platform (Teams/Webex/In-person), Duration (Brief/Break/Q&A), Max Presenters/Attendees, Content Allowed/Prohibited (e.g., price), Recording Allowed?, Participant List Due (timing), Deck Submission Timing/Format, Source Citation.

Tab 5 - Evaluation Matrix (Section M)
Columns: Factor, Subfactor, Standard/What “Acceptable” Means, Relative Importance, Weight/Points (if given), Trade-off vs Price, Risk Considerations, Clarifying Notes, Source Citation.

Tab 6 - Admin/Compliance (General)
Columns: Topic, Requirement (verbatim/summary), Clause/Reference (FAR/DFARS/etc.), Applicability (All/Specific Volume), Source Citation, Notes.
- Include: CDRL/DI- numbers, NAICS/PSC, contract type (FFP/T&M/etc.), PoP & place, security (CUI/NIST/ITAR), reviews/IBR/PMR, travel policy, gov’t portals, etc.

Tab 7 - Pre-Submission Checklist
Checkbox list derived from Tabs 1-6: Item, Owner, Status (Not Started/In Progress/Done), Due, Link to Evidence, Source Citation.

Output format: Provide as a single Excel file; mirror the column headers exactly; no free-text prose instead of tables. No hallucinations—leave MISSING where the docs are silent.
Quality gates:

Every row must have a Source Citation.

Page/slide limits and formats must be verbatim or clearly summarized from Section L.

Where Section L conflicts with SOW, treat Section L as controlling and note the discrepancy in Notes.

Surface red-flag risks (e.g., page cap conflicts, portal vs. email ambiguity) at the top of each tab."""
    
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
