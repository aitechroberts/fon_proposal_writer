# app/src/proposal/modules.py
"""
DSPy modules for proposal writing pipeline.

Two approaches are provided:
- SinglePassWriter: One LLM call per section (faster, primary approach)
- TwoStageWriter: Theme analysis then draft (alternative, higher quality)
- ProposalGenerator: Orchestrates the full proposal generation
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from functools import wraps

import dspy
import litellm

from .signatures import (
    WriteSectionSinglePass,
    AnalyzeSectionThemes,
    DraftSectionFromThemes,
    PROPOSAL_SECTIONS,
    CATEGORY_ORDER,
    get_section_context,
)

logger = logging.getLogger(__name__)

# Flag to track if DSPy has been initialized
_dspy_initialized = False


def ensure_dspy_configured() -> None:
    """
    Ensure DSPy is configured for Azure OpenAI.
    
    This function is idempotent - it will only configure DSPy once per process.
    Uses the same configuration pattern as the main extraction pipeline (main.py).
    """
    global _dspy_initialized
    
    if _dspy_initialized:
        logger.debug("DSPy already initialized, skipping")
        return
    
    # Check if DSPy is already configured (from extraction pipeline)
    try:
        current_lm = dspy.settings.lm
        if current_lm is not None:
            logger.info("DSPy already configured (likely from extraction pipeline)")
            _dspy_initialized = True
            return
    except Exception:
        pass
    
    # Need to configure DSPy ourselves - use same pattern as main.py
    logger.info("Initializing DSPy for proposal generation...")
    
    # Use the settings singleton (same as working extraction pipeline)
    from src.config import settings
    
    if not settings.azure_api_key:
        raise ValueError("AZURE_API_KEY not configured - check .env file")
    if not settings.azure_api_base:
        raise ValueError("AZURE_API_BASE not configured - check .env file")
    
    base = settings.azure_api_base.rstrip("/")
    logger.info(f"Using Azure OpenAI: base={base}, deployment={settings.azure_openai_deployment}")
    
    # Patch litellm to force max_tokens (same as main pipeline)
    _original_litellm_completion = litellm.completion
    
    @wraps(_original_litellm_completion)
    def _force_max_tokens_completion(*args, **kwargs):
        kwargs['max_tokens'] = 32000
        return _original_litellm_completion(*args, **kwargs)
    
    litellm.completion = _force_max_tokens_completion
    
    # Set up environment for litellm (same as main.py _init_dspy_direct)
    os.environ["AZURE_API_KEY"] = settings.azure_api_key
    os.environ["AZURE_API_BASE"] = base
    os.environ["AZURE_API_VERSION"] = settings.azure_api_version
    os.environ["OPENAI_API_KEY"] = settings.azure_api_key
    
    litellm.drop_params = True
    litellm.set_verbose = False
    
    # Create DSPy LM (same pattern as main.py)
    azure_model = f"azure/{settings.azure_openai_deployment}"
    
    lm = dspy.LM(
        model=azure_model,
        api_key=settings.azure_api_key,
        api_base=base,              # litellm will append /openai/deployments/<deployment>
        api_version=settings.azure_api_version,
        temperature=0.0,
        max_tokens=32000,
    )
    
    # Configure DSPy
    dspy.configure(lm=lm, adapter=dspy.JSONAdapter(), track_usage=False, cache=False)
    
    _dspy_initialized = True
    logger.info(f"Configured DSPy for proposal generation: deployment={settings.azure_openai_deployment}")

LOG_LLM = os.getenv("LOG_LLM", "0") in ("1", "true", "TRUE", "yes", "YES")
RAW_DIR = Path(os.getenv("RAW_DUMP_DIR", "raw_llm"))


def _dump_raw(name: str, idx: int, payload: Any) -> None:
    """Dump raw LLM output for debugging."""
    if not LOG_LLM:
        return
    try:
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        p = RAW_DIR / f"{name}_{idx:06d}.txt"
        with open(p, "w", encoding="utf-8") as f:
            if isinstance(payload, (dict, list)):
                f.write(json.dumps(payload, ensure_ascii=False, indent=2))
            else:
                f.write(str(payload))
    except Exception as e:
        logger.warning("Failed to write raw dump %s: %s", name, e)


def _safe_json_loads(s: str) -> Any:
    """Safely parse JSON, handling common LLM output issues."""
    if not s:
        return {}
    
    # Try direct parse first
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON from markdown code blocks
    import re
    
    # Look for ```json ... ``` blocks
    m = re.search(r"```json\s*(.+?)\s*```", s, flags=re.S | re.I)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    
    # Look for any ``` ... ``` blocks
    m = re.search(r"```\s*(.+?)\s*```", s, flags=re.S)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    
    # Try to find JSON object or array
    start = None
    for i, ch in enumerate(s):
        if ch in "{[":
            start = i
            break
    
    if start is not None:
        for end in (s.rfind("}"), s.rfind("]")):
            if end != -1 and end > start:
                candidate = s[start:end + 1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    pass
    
    logger.warning("Could not parse JSON from response")
    return {}


# =============================================================================
# APPROACH A: Single-Pass Section Writer
# =============================================================================

class SinglePassWriter(dspy.Module):
    """
    Write a proposal section in a single LLM call.
    
    This is the primary (faster) approach - one call per section.
    """
    
    def __init__(self, retries: int = 2, retry_sleep: float = 0.5):
        super().__init__()
        self.pred = dspy.Predict(WriteSectionSinglePass)
        self.retries = retries
        self.retry_sleep = retry_sleep
        self._call_count = 0
    
    def forward(
        self,
        category: str,
        requirements: List[Dict[str, Any]],
        section_context: Optional[str] = None
    ) -> str:
        """
        Generate proposal content for a section.
        
        Args:
            category: Section category name
            requirements: List of requirement dicts for this category
            section_context: Optional context about section position
            
        Returns:
            Generated proposal text for the section
        """
        self._call_count += 1
        
        if not requirements:
            logger.warning(f"No requirements for category '{category}', returning placeholder")
            return f"[No specific requirements identified for {category}]"
        
        # Prepare inputs
        reqs_json = json.dumps(requirements, ensure_ascii=False, indent=2)
        context = section_context or get_section_context(category)
        
        logger.info(
            f"[SinglePassWriter] Category: {category}, "
            f"Requirements: {len(requirements)}, Context: {context[:50]}..."
        )
        
        # First attempt
        try:
            out = self.pred(
                category=category,
                requirements_json=reqs_json,
                section_context=context
            )
            text = getattr(out, "proposal_text", None) or ""
            _dump_raw("proposal_single_pass", self._call_count, text)
            
            if text.strip():
                logger.info(f"[SinglePassWriter] Success: {len(text)} chars")
                return text.strip()
        except Exception as e:
            logger.error(f"[SinglePassWriter] First attempt failed: {e}")
        
        # Retries with more explicit instruction
        for r in range(self.retries):
            time.sleep(self.retry_sleep)
            try:
                enhanced_context = (
                    f"{context}\n\n"
                    "IMPORTANT: Write professional proposal content addressing ALL requirements. "
                    "Output ONLY the proposal text, no headers or JSON."
                )
                
                out = self.pred(
                    category=category,
                    requirements_json=reqs_json,
                    section_context=enhanced_context
                )
                text = getattr(out, "proposal_text", None) or ""
                _dump_raw(f"proposal_single_pass_retry{r+1}", self._call_count, text)
                
                if text.strip():
                    logger.info(f"[SinglePassWriter] Retry {r+1} success: {len(text)} chars")
                    return text.strip()
            except Exception as e:
                logger.error(f"[SinglePassWriter] Retry {r+1} failed: {e}")
        
        logger.warning(f"[SinglePassWriter] All attempts failed for '{category}'")
        return f"[Content generation failed for {category}. Please review requirements manually.]"


# =============================================================================
# APPROACH B: Two-Stage Section Writer
# =============================================================================

class TwoStageWriter(dspy.Module):
    """
    Write a proposal section in two stages:
    1. Analyze themes and compliance points
    2. Draft content based on analysis
    
    This is the alternative (higher quality) approach.
    """
    
    def __init__(self, retries: int = 1, retry_sleep: float = 0.5):
        super().__init__()
        self.theme_analyzer = dspy.Predict(AnalyzeSectionThemes)
        self.draft_writer = dspy.Predict(DraftSectionFromThemes)
        self.retries = retries
        self.retry_sleep = retry_sleep
        self._call_count = 0
    
    def _analyze_themes(self, category: str, reqs_json: str) -> Dict[str, Any]:
        """Stage 1: Analyze requirements for themes."""
        try:
            out = self.theme_analyzer(
                category=category,
                requirements_json=reqs_json
            )
            raw = getattr(out, "themes_json", None) or "{}"
            _dump_raw(f"proposal_themes_{self._call_count}", 0, raw)
            return _safe_json_loads(raw)
        except Exception as e:
            logger.error(f"[TwoStageWriter] Theme analysis failed: {e}")
            return {
                "key_themes": [category],
                "critical_compliance": [],
                "important_considerations": [],
                "logical_groups": [],
                "writing_guidance": "Address all requirements systematically"
            }
    
    def _draft_from_themes(
        self,
        category: str,
        themes: Dict[str, Any],
        reqs_json: str
    ) -> str:
        """Stage 2: Draft content based on themes."""
        try:
            themes_json = json.dumps(themes, ensure_ascii=False, indent=2)
            out = self.draft_writer(
                category=category,
                themes_json=themes_json,
                requirements_json=reqs_json
            )
            text = getattr(out, "proposal_text", None) or ""
            _dump_raw(f"proposal_draft_{self._call_count}", 0, text)
            return text.strip()
        except Exception as e:
            logger.error(f"[TwoStageWriter] Draft writing failed: {e}")
            return ""
    
    def forward(
        self,
        category: str,
        requirements: List[Dict[str, Any]],
        section_context: Optional[str] = None
    ) -> str:
        """
        Generate proposal content using two-stage approach.
        
        Args:
            category: Section category name
            requirements: List of requirement dicts for this category
            section_context: Optional context (not used in this approach)
            
        Returns:
            Generated proposal text for the section
        """
        self._call_count += 1
        
        if not requirements:
            logger.warning(f"No requirements for category '{category}'")
            return f"[No specific requirements identified for {category}]"
        
        reqs_json = json.dumps(requirements, ensure_ascii=False, indent=2)
        
        logger.info(
            f"[TwoStageWriter] Category: {category}, Requirements: {len(requirements)}"
        )
        
        # Stage 1: Analyze themes
        themes = self._analyze_themes(category, reqs_json)
        logger.info(f"[TwoStageWriter] Themes identified: {themes.get('key_themes', [])}")
        
        # Stage 2: Draft content
        text = self._draft_from_themes(category, themes, reqs_json)
        
        if text:
            logger.info(f"[TwoStageWriter] Success: {len(text)} chars")
            return text
        
        # Retry if first attempt failed
        for r in range(self.retries):
            time.sleep(self.retry_sleep)
            themes = self._analyze_themes(category, reqs_json)
            text = self._draft_from_themes(category, themes, reqs_json)
            if text:
                logger.info(f"[TwoStageWriter] Retry {r+1} success: {len(text)} chars")
                return text
        
        logger.warning(f"[TwoStageWriter] All attempts failed for '{category}'")
        return f"[Content generation failed for {category}. Please review requirements manually.]"


# =============================================================================
# PROPOSAL GENERATOR ORCHESTRATOR
# =============================================================================

class ProposalGenerator:
    """
    Orchestrates the full proposal generation process.
    
    Filters requirements by category, processes them in the correct order,
    and produces a structured proposal document.
    """
    
    def __init__(self, use_two_stage: bool = False):
        """
        Initialize the proposal generator.
        
        Args:
            use_two_stage: If True, use TwoStageWriter; otherwise SinglePassWriter
        """
        self.use_two_stage = use_two_stage
        self.writer = TwoStageWriter() if use_two_stage else SinglePassWriter()
        logger.info(f"ProposalGenerator initialized with {'TwoStageWriter' if use_two_stage else 'SinglePassWriter'}")
    
    def filter_requirements_by_category(
        self,
        requirements: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Filter requirements into category buckets.
        
        Args:
            requirements: Full list of extracted requirements
            
        Returns:
            Dict mapping category names to lists of requirements
        """
        by_category: Dict[str, List[Dict[str, Any]]] = {
            cat: [] for cat in CATEGORY_ORDER
        }
        
        unmatched = 0
        for req in requirements:
            category = req.get("category", "")
            if category in by_category:
                by_category[category].append(req)
            else:
                unmatched += 1
        
        # Log category distribution
        for cat in CATEGORY_ORDER:
            count = len(by_category[cat])
            if count > 0:
                logger.info(f"Category '{cat}': {count} requirements")
        
        if unmatched > 0:
            logger.info(f"Unmatched requirements (not in proposal categories): {unmatched}")
        
        return by_category
    
    def generate_proposal(
        self,
        requirements: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate the full proposal from requirements.
        
        Args:
            requirements: Full list of extracted requirements
            
        Returns:
            List of section dicts with structure:
            [
                {
                    "part": "Part 1: The Promise (BLUF)",
                    "category": "Technical Approach & Capability",
                    "content": "...",
                    "requirement_count": 5
                },
                ...
            ]
        """
        logger.info(f"Starting proposal generation for {len(requirements)} requirements")
        
        # Filter requirements by category
        by_category = self.filter_requirements_by_category(requirements)
        
        # Process sections in order
        sections: List[Dict[str, Any]] = []
        
        for part_name, categories in PROPOSAL_SECTIONS.items():
            logger.info(f"Processing {part_name}")
            
            for category in categories:
                cat_reqs = by_category.get(category, [])
                context = get_section_context(category)
                
                t0 = time.perf_counter()
                content = self.writer(
                    category=category,
                    requirements=cat_reqs,
                    section_context=context
                )
                t1 = time.perf_counter()
                
                sections.append({
                    "part": part_name,
                    "category": category,
                    "content": content,
                    "requirement_count": len(cat_reqs),
                    "generation_time_sec": round(t1 - t0, 2)
                })
                
                logger.info(
                    f"  [{category}] {len(cat_reqs)} reqs -> {len(content)} chars in {t1-t0:.2f}s"
                )
        
        total_chars = sum(len(s["content"]) for s in sections)
        logger.info(f"Proposal generation complete: {len(sections)} sections, {total_chars} total chars")
        
        return sections
    
    def generate_text_document(
        self,
        sections: List[Dict[str, Any]]
    ) -> str:
        """
        Generate a plain text version of the proposal.
        
        Args:
            sections: List of section dicts from generate_proposal
            
        Returns:
            Plain text string with sections concatenated
        """
        lines: List[str] = []
        current_part = None
        
        for section in sections:
            part = section["part"]
            
            # Add part heading if changed
            if part != current_part:
                if current_part is not None:
                    lines.append("")  # Separator between parts
                lines.append("=" * 60)
                lines.append(part)
                lines.append("=" * 60)
                lines.append("")
                current_part = part
            
            # Add section
            lines.append("-" * 40)
            lines.append(section["category"])
            lines.append("-" * 40)
            lines.append("")
            lines.append(section["content"])
            lines.append("")
        
        return "\n".join(lines)


def run_proposal_pipeline(
    requirements: List[Dict[str, Any]],
    use_two_stage: bool = False
) -> List[Dict[str, Any]]:
    """
    Run the proposal writing pipeline.
    
    Args:
        requirements: List of extracted requirement dicts
        use_two_stage: Whether to use the two-stage writer approach
        
    Returns:
        List of section dicts with part, category, content, and metadata
    """
    # Ensure DSPy is configured (idempotent - safe to call multiple times)
    ensure_dspy_configured()
    
    generator = ProposalGenerator(use_two_stage=use_two_stage)
    return generator.generate_proposal(requirements)

