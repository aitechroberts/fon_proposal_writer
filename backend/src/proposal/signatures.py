# app/src/proposal/signatures.py
"""
DSPy signatures for proposal writing pipeline.

Two approaches are provided:
- Approach A (Single-Pass): One LLM call per section - faster, simpler
- Approach B (Two-Stage): Theme analysis then draft - higher quality, more calls
"""

import dspy
from dspy import InputField, OutputField


# =============================================================================
# APPROACH A: Single-Pass Section Writer (Primary)
# =============================================================================

class WriteSectionSinglePass(dspy.Signature):
    """Write a complete proposal section that addresses all provided requirements.
    
    You are an expert government proposal writer. Given a category of requirements
    extracted from an RFP, write professional proposal content that:
    
    1. Addresses EVERY requirement in the provided list
    2. Uses clear, professional language appropriate for government proposals
    3. Demonstrates understanding and compliance with each requirement
    4. Organizes content logically with smooth transitions
    5. Avoids generic filler - be specific and substantive
    
    The output should be well-structured prose suitable for inclusion in a
    formal government proposal response. Do NOT include the section heading
    in your output - just the content. When you directly answer a requirement,
    cite its id AND modality in brackets (e.g., [REQ-001 MUST][REQ-002 SHOULD]
    or [8 SHALL]) inline with the relevant sentence.
    
    Input:
    - category: The section category name (e.g., "Technical Approach & Capability")
    - requirements_json: JSON array of requirement objects with fields like
      quote, modality (SHALL/MUST/SHOULD/MAY), section, page references
    - section_context: Context about where this section fits in the overall
      proposal structure (e.g., "Part 1: The Promise - Section 1 of 2")
    
    Output:
    - proposal_text: Professional proposal content addressing all requirements
    """
    
    category: str = InputField(
        desc="The section category name (e.g., 'Technical Approach & Capability')"
    )
    requirements_json: str = InputField(
        desc="JSON array of requirement objects with quote, modality, section, page_start, page_end fields"
    )
    section_context: str = InputField(
        desc="Context about this section's position in the proposal structure"
    )
    proposal_text: str = OutputField(
        desc=(
            "Professional proposal content addressing all requirements. "
            "Include bracketed requirement id+modality where addressed "
            "(e.g., [REQ-001 MUST][REQ-002 SHOULD] or [8 SHALL]). "
            "Well-structured prose only, no heading."
        )
    )


# =============================================================================
# APPROACH B: Two-Stage Section Writer (Alternative)
# =============================================================================

class AnalyzeSectionThemes(dspy.Signature):
    """Analyze requirements to extract key themes and compliance points.
    
    Before writing a proposal section, analyze the requirements to identify:
    1. Key themes that should be addressed
    2. Critical compliance points (SHALL/MUST requirements)
    3. Important considerations (SHOULD/MAY requirements)
    4. Logical groupings of related requirements
    5. Any potential conflicts or dependencies between requirements
    
    Output a structured JSON analysis that will guide the drafting phase.
    
    Input:
    - category: The section category name
    - requirements_json: JSON array of requirement objects
    
    Output:
    - themes_json: JSON object with structure:
      {
        "key_themes": ["theme1", "theme2", ...],
        "critical_compliance": [{"requirement_id": "...", "summary": "..."}],
        "important_considerations": [{"requirement_id": "...", "summary": "..."}],
        "logical_groups": [{"group_name": "...", "requirement_ids": [...]}],
        "writing_guidance": "Brief guidance on how to structure this section"
      }
    """
    
    category: str = InputField(
        desc="The section category name"
    )
    requirements_json: str = InputField(
        desc="JSON array of requirement objects to analyze"
    )
    themes_json: str = OutputField(
        desc="JSON object containing key themes, compliance points, and writing guidance",
        prefix="JSON:"
    )


class DraftSectionFromThemes(dspy.Signature):
    """Write a proposal section based on analyzed themes and requirements.
    
    Using the theme analysis and original requirements, write professional
    proposal content that:
    
    1. Addresses all identified themes systematically
    2. Ensures all critical compliance points are explicitly addressed
    3. Incorporates important considerations appropriately
    4. Follows the logical groupings suggested in the analysis
    5. Uses the writing guidance to structure the content
    
    The output should be polished, professional prose ready for inclusion
    in a government proposal. Do NOT include the section heading. When you
    directly answer a requirement, cite its id AND modality in brackets
    (e.g., [REQ-001 MUST] or [12 SHALL]).
    
    Input:
    - category: The section category name
    - themes_json: The analyzed themes and guidance from AnalyzeSectionThemes
    - requirements_json: Original requirement objects for reference
    
    Output:
    - proposal_text: Professional proposal content organized around themes
    """
    
    category: str = InputField(
        desc="The section category name"
    )
    themes_json: str = InputField(
        desc="Analyzed themes, compliance points, and writing guidance"
    )
    requirements_json: str = InputField(
        desc="Original requirement objects for reference during writing"
    )
    proposal_text: str = OutputField(
        desc=(
            "Professional proposal content organized around identified themes. "
            "Include bracketed requirement id+modality where addressed "
            "(e.g., [REQ-001 MUST][REQ-002 SHOULD] or [12 SHALL])."
        )
    )


# =============================================================================
# PROPOSAL STRUCTURE CONFIGURATION
# =============================================================================

# Categories to process in the specified order, grouped by proposal part
PROPOSAL_SECTIONS = {
    "Part 1: The Promise (BLUF)": [
        "Personnel & Qualifications",
        "Past Performance",
        "Technical Approach & Capability",
        "Schedule & Milestones",
    ],
    "Part 2: The Solution (Customer Focus)": [
        "Performance & Deliverables",
        "Operations & Sustainment",
        "Customer Service & Communications",
    ],
    "Part 3: The People (Low Risk)": [
        "Training & Workforce Development",
        "Management & Staffing",
    ],
    "Part 4: The Safety Net (Compliance)": [
        "Quality Assurance",
        "Security (Personnel & Facility)",
        "Risk Management & Oversight Authority",
        "Flowdowns & Subcontracting",
    ],
}

# Flat list of categories in processing order
CATEGORY_ORDER = [
    "Personnel & Qualifications",
    "Past Performance",
    "Technical Approach & Capability",
    "Schedule & Milestones",
    "Performance & Deliverables",
    "Operations & Sustainment",
    "Customer Service & Communications",
    "Training & Workforce Development",
    "Management & Staffing",
    "Quality Assurance",
    "Security (Personnel & Facility)",
    "Risk Management & Oversight Authority",
    "Flowdowns & Subcontracting",
]

# Part descriptions for context
PART_DESCRIPTIONS = {
    "Part 1: The Promise (BLUF)": "Address the strategy immediately and prove reality",
    "Part 2: The Solution (Customer Focus)": "Pivot to solving their specific problems and long-term value",
    "Part 3: The People (Low Risk)": "Demonstrate low transition risk and high retention",
    "Part 4: The Safety Net (Compliance)": "Ensure all pass/fail requirements are met with precision",
}


def get_section_context(category: str) -> str:
    """Generate context string for a category's position in the proposal."""
    for part_name, categories in PROPOSAL_SECTIONS.items():
        if category in categories:
            section_num = categories.index(category) + 1
            total_in_part = len(categories)
            part_desc = PART_DESCRIPTIONS.get(part_name, "")
            
            return (
                f"{part_name} - Section {section_num} of {total_in_part}\n"
                f"Goal: {part_desc}\n"
                f"Category: {category}"
            )
    
    return f"Category: {category}"

