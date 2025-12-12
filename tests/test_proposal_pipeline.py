# tests/test_proposal_pipeline.py
"""
Tests for the proposal writing pipeline.

Run from project root:
    cd /home/jroberts/fon_proposal_writer
    uv run python tests/test_proposal_pipeline.py
    uv run python tests/test_proposal_pipeline.py --full

Requires .env file in project root with Azure credentials.
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock

# Determine project root (parent of tests/)
PROJECT_ROOT = Path(__file__).parent.parent

# Add app paths so imports work
sys.path.insert(0, str(PROJECT_ROOT / "app"))
sys.path.insert(0, str(PROJECT_ROOT / "app" / "src"))

# Change working directory to project root so config.py finds .env
os.chdir(PROJECT_ROOT)
print(f"Working directory: {os.getcwd()}")

import pytest


# =============================================================================
# Requirements Data Loading
# =============================================================================

# Path to the real requirements Excel file
REQUIREMENTS_XLSX_PATH = PROJECT_ROOT / "JEDI.matrix.xlsx"


def load_requirements_from_xlsx(xlsx_path: Path = REQUIREMENTS_XLSX_PATH) -> List[Dict[str, Any]]:
    """
    Load requirements from the Excel compliance matrix.
    
    Args:
        xlsx_path: Path to the Excel file
        
    Returns:
        List of requirement dictionaries
    """
    import pandas as pd
    
    if not xlsx_path.exists():
        print(f"⚠ Requirements file not found: {xlsx_path}")
        return MOCK_REQUIREMENTS
    
    try:
        df = pd.read_excel(xlsx_path)
        
        print(f"   Excel columns: {list(df.columns)}")
        
        # Create a column name mapping: lowercase_underscore -> original
        col_mapping = {}
        for col in df.columns:
            normalized = col.lower().replace(" ", "_")
            col_mapping[col] = normalized
        
        # Rename columns to normalized form
        df = df.rename(columns=col_mapping)
        
        requirements = df.to_dict(orient="records")
        print(f"✓ Loaded {len(requirements)} requirements from {xlsx_path.name}")
        
        # Debug: show category distribution
        categories = df.get("category", pd.Series())
        if not categories.empty:
            category_counts = categories.value_counts()
            print(f"   Categories found: {len(category_counts)}")
            for cat, count in category_counts.head(15).items():
                print(f"      - {cat}: {count}")
        
        return requirements
        
    except Exception as e:
        print(f"⚠ Failed to load requirements: {e}")
        import traceback
        traceback.print_exc()
        return MOCK_REQUIREMENTS


# Fallback mock data if xlsx not available
MOCK_REQUIREMENTS: List[Dict[str, Any]] = [
    {
        "id": "REQ-001",
        "category": "Technical Approach & Capability",
        "modality": "SHALL",
        "quote": "The contractor shall provide a technical approach that demonstrates understanding of the project requirements.",
        "section": "Section C",
        "page_start": 10,
        "page_end": 10,
        "source": "llm",
        "confidence": 0.95
    },
    {
        "id": "REQ-002",
        "category": "Technical Approach & Capability",
        "modality": "MUST",
        "quote": "The technical solution must integrate with existing government systems.",
        "section": "Section C",
        "page_start": 11,
        "page_end": 11,
        "source": "llm",
        "confidence": 0.90
    },
    {
        "id": "REQ-003",
        "category": "Schedule & Milestones",
        "modality": "SHALL",
        "quote": "The contractor shall provide a detailed schedule with key milestones.",
        "section": "Section C",
        "page_start": 15,
        "page_end": 15,
        "source": "llm",
        "confidence": 0.92
    },
    {
        "id": "REQ-004",
        "category": "Personnel & Qualifications",
        "modality": "SHALL",
        "quote": "Key personnel shall have at least 5 years of relevant experience.",
        "section": "Section L",
        "page_start": 25,
        "page_end": 25,
        "source": "llm",
        "confidence": 0.88
    },
    {
        "id": "REQ-005",
        "category": "Quality Assurance",
        "modality": "MUST",
        "quote": "The contractor must maintain ISO 9001 certification.",
        "section": "Section C",
        "page_start": 30,
        "page_end": 30,
        "source": "llm",
        "confidence": 0.95
    },
    {
        "id": "REQ-006",
        "category": "Security (Personnel & Facility)",
        "modality": "SHALL",
        "quote": "All personnel shall possess or be eligible for Secret clearance.",
        "section": "Section H",
        "page_start": 35,
        "page_end": 35,
        "source": "llm",
        "confidence": 0.99
    },
]


def get_requirements() -> List[Dict[str, Any]]:
    """Get requirements - from xlsx if available, otherwise mock data."""
    if REQUIREMENTS_XLSX_PATH.exists():
        return load_requirements_from_xlsx()
    return MOCK_REQUIREMENTS


# =============================================================================
# Unit Tests (No Azure Required)
# =============================================================================

class TestSignatures:
    """Test DSPy signature definitions."""
    
    def test_signatures_import(self):
        """Test that signatures can be imported."""
        from src.proposal.signatures import (
            WriteSectionSinglePass,
            AnalyzeSectionThemes,
            DraftSectionFromThemes,
            PROPOSAL_SECTIONS,
            CATEGORY_ORDER,
            get_section_context,
        )
        
        assert WriteSectionSinglePass is not None
        assert AnalyzeSectionThemes is not None
        assert DraftSectionFromThemes is not None
    
    def test_proposal_sections_structure(self):
        """Test the proposal sections configuration."""
        from src.proposal.signatures import PROPOSAL_SECTIONS, CATEGORY_ORDER
        
        # Should have 4 parts
        assert len(PROPOSAL_SECTIONS) == 4
        
        # Should have 12 categories
        assert len(CATEGORY_ORDER) == 12
        
        # All categories in order should be in sections
        all_categories = []
        for categories in PROPOSAL_SECTIONS.values():
            all_categories.extend(categories)
        
        assert set(all_categories) == set(CATEGORY_ORDER)
    
    def test_get_section_context(self):
        """Test section context generation."""
        from src.proposal.signatures import get_section_context
        
        context = get_section_context("Technical Approach & Capability")
        
        assert "Part 1" in context
        assert "Technical Approach & Capability" in context
        assert "Section 1 of 2" in context


class TestModulesStructure:
    """Test module structure without requiring Azure."""
    
    def test_modules_import(self):
        """Test that modules can be imported."""
        from src.proposal.modules import (
            SinglePassWriter,
            TwoStageWriter,
            ProposalGenerator,
            run_proposal_pipeline,
            ensure_dspy_configured,
        )
        
        assert SinglePassWriter is not None
        assert TwoStageWriter is not None
        assert ProposalGenerator is not None


class TestWordExport:
    """Test Word document export functionality."""
    
    def test_export_word_basic(self):
        """Test basic Word export with mock sections."""
        from src.proposal.export_word import export_proposal_to_word
        
        sections = [
            {
                "part": "Part 1: The Promise (BLUF)",
                "category": "Technical Approach & Capability",
                "content": "Our technical approach demonstrates deep understanding...",
            },
            {
                "part": "Part 1: The Promise (BLUF)",
                "category": "Schedule & Milestones",
                "content": "We propose the following schedule with key milestones...",
            },
        ]
        
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            output_path = Path(f.name)
        
        try:
            result = export_proposal_to_word(sections, output_path)
            
            assert result.exists()
            assert result.suffix == ".docx"
            assert result.stat().st_size > 0
        finally:
            output_path.unlink(missing_ok=True)
    
    def test_sections_to_text(self):
        """Test text conversion."""
        from src.proposal.export_word import sections_to_text
        
        sections = [
            {
                "part": "Part 1: Test",
                "category": "Test Category",
                "content": "Test content here.",
            },
        ]
        
        text = sections_to_text(sections)
        
        assert "Part 1: Test" in text
        assert "Test Category" in text
        assert "Test content here." in text


class TestCategoryFiltering:
    """Test requirement filtering by category."""
    
    def test_filter_requirements(self):
        """Test that requirements are properly filtered by category."""
        from src.proposal.modules import ProposalGenerator
        from src.proposal.signatures import CATEGORY_ORDER
        
        # Mock DSPy to avoid needing Azure
        with patch('src.proposal.modules.ensure_dspy_configured'):
            with patch('src.proposal.modules.SinglePassWriter'):
                generator = ProposalGenerator(use_two_stage=False)
                
                by_category = generator.filter_requirements_by_category(MOCK_REQUIREMENTS)
                
                # Check that categories are created
                assert "Technical Approach & Capability" in by_category
                assert len(by_category["Technical Approach & Capability"]) == 2
                
                assert "Schedule & Milestones" in by_category
                assert len(by_category["Schedule & Milestones"]) == 1
                
                # Categories not in mock data should be empty
                assert "Operations & Sustainment" in by_category
                assert len(by_category["Operations & Sustainment"]) == 0


# =============================================================================
# Integration Tests (Require Azure Credentials)
# =============================================================================

@pytest.mark.skipif(
    not os.getenv("AZURE_API_KEY"),
    reason="Azure credentials not available"
)
class TestIntegration:
    """Integration tests that require Azure OpenAI credentials."""
    
    def test_dspy_initialization(self):
        """Test that DSPy can be initialized."""
        from src.proposal.modules import ensure_dspy_configured
        
        # Should not raise
        ensure_dspy_configured()
    
    def test_single_pass_writer(self):
        """Test single-pass writer with real Azure OpenAI."""
        from src.proposal.modules import SinglePassWriter, ensure_dspy_configured
        
        ensure_dspy_configured()
        
        writer = SinglePassWriter()
        
        # Use real requirements if available
        requirements = get_requirements()[:3]  # Just test with first 3
        
        result = writer.forward(
            category="Technical Approach & Capability",
            requirements=requirements,
            section_context="Test context"
        )
        
        assert isinstance(result, str)
        assert len(result) > 50  # Should have substantial content
    
    def test_full_pipeline_single_pass(self):
        """Test the full proposal pipeline with single-pass writer using real data."""
        from src.proposal.modules import run_proposal_pipeline
        
        requirements = get_requirements()
        sections = run_proposal_pipeline(requirements, use_two_stage=False)
        
        assert isinstance(sections, list)
        assert len(sections) == 12  # All 12 categories
        
        # Check structure
        for section in sections:
            assert "part" in section
            assert "category" in section
            assert "content" in section
            assert isinstance(section["content"], str)
    
    def test_full_pipeline_two_stage(self):
        """Test the full proposal pipeline with two-stage writer using real data."""
        from src.proposal.modules import run_proposal_pipeline
        
        requirements = get_requirements()
        sections = run_proposal_pipeline(requirements, use_two_stage=True)
        
        assert isinstance(sections, list)
        assert len(sections) == 12


# =============================================================================
# CLI Test Runner
# =============================================================================

def run_quick_test():
    """Quick test runner for manual testing."""
    print("=" * 60)
    print("Running quick tests...")
    print("=" * 60)
    
    # Test imports
    print("\n1. Testing imports...")
    try:
        from src.proposal.signatures import PROPOSAL_SECTIONS, CATEGORY_ORDER
        from src.proposal.modules import ProposalGenerator, run_proposal_pipeline
        from src.proposal.export_word import export_proposal_to_word
        print("   ✓ All imports successful")
    except Exception as e:
        print(f"   ✗ Import failed: {e}")
        return False
    
    # Load requirements
    print("\n2. Loading requirements...")
    requirements = get_requirements()
    print(f"   ✓ Loaded {len(requirements)} requirements")
    
    # Test category filtering
    print("\n3. Testing category filtering...")
    with patch('src.proposal.modules.ensure_dspy_configured'):
        with patch('src.proposal.modules.SinglePassWriter'):
            generator = ProposalGenerator(use_two_stage=False)
            by_category = generator.filter_requirements_by_category(requirements)
            print(f"   ✓ Filtered into {len(by_category)} categories")
            for cat, reqs in by_category.items():
                if reqs:
                    print(f"      - {cat}: {len(reqs)} requirements")
    
    # Test Word export
    print("\n4. Testing Word export...")
    sections = [
        {"part": "Part 1: Test", "category": "Test", "content": "Test content"}
    ]
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        path = Path(f.name)
    try:
        export_proposal_to_word(sections, path)
        print(f"   ✓ Word export successful: {path.stat().st_size} bytes")
    finally:
        path.unlink(missing_ok=True)
    
    # Check Azure credentials using settings (same as working pipeline)
    print("\n5. Checking Azure credentials (via src.config.settings)...")
    from src.config import settings
    if settings.azure_api_key:
        print("   ✓ AZURE_API_KEY is set")
        print(f"   ✓ AZURE_API_BASE: {settings.azure_api_base[:40]}...")
        print(f"   ✓ AZURE_OPENAI_DEPLOYMENT: {settings.azure_openai_deployment}")
    else:
        print("   ⚠ AZURE_API_KEY not set - check .env file")
        return True
    
    print("\n" + "=" * 60)
    print("Quick tests completed!")
    print("=" * 60)
    
    return True


def run_full_integration_test():
    """
    Run a full integration test with real Azure OpenAI.
    
    This will generate a proposal document from the requirements xlsx.
    """
    print("=" * 60)
    print("Running FULL Integration Test")
    print("=" * 60)
    
    # Check credentials using the same settings pattern as working pipeline
    print("\n0. Checking Azure configuration (via src.config.settings)...")
    from src.config import settings
    
    if not settings.azure_api_key:
        print("   ✗ AZURE_API_KEY not set. Cannot run integration test.")
        print("   Make sure .env file exists in project root.")
        return False
    
    print(f"   ✓ AZURE_API_KEY: {'*' * 10}...{settings.azure_api_key[-4:]}")
    print(f"   ✓ AZURE_API_BASE: {settings.azure_api_base}")
    print(f"   ✓ AZURE_OPENAI_DEPLOYMENT: {settings.azure_openai_deployment}")
    print(f"   ✓ AZURE_API_VERSION: {settings.azure_api_version}")
    
    # Load requirements
    print("\n1. Loading requirements from xlsx...")
    requirements = get_requirements()
    print(f"   ✓ Loaded {len(requirements)} requirements")
    
    # Filter to the proposal-writing categories and save for verification
    print("\n2. Saving writing requirements for verification...")
    from src.proposal.signatures import CATEGORY_ORDER
    import pandas as pd

    writing_reqs = [
        r for r in requirements
        if str(r.get("category", "")).strip() in CATEGORY_ORDER
    ]

    # Sort by category order, then by requirement id for readability
    cat_rank = {c: i for i, c in enumerate(CATEGORY_ORDER)}
    writing_reqs = sorted(
        writing_reqs,
        key=lambda r: (
            cat_rank.get(str(r.get("category", "")).strip(), 999),
            str(r.get("id", "")),
        ),
    )

    output_dir = PROJECT_ROOT / "test-proposals"
    output_dir.mkdir(exist_ok=True)

    writing_xlsx_path = output_dir / "writing_requirements.xlsx"
    pd.DataFrame(writing_reqs).to_excel(writing_xlsx_path, index=False)
    print(f"   ✓ Saved {len(writing_reqs)} writing requirements to {writing_xlsx_path}")

    # Run pipeline
    print("\n2. Running proposal pipeline (this may take a few minutes)...")
    from src.proposal.modules import run_proposal_pipeline
    
    try:
        sections = run_proposal_pipeline(requirements, use_two_stage=False)
        print(f"   ✓ Generated {len(sections)} sections")
    except Exception as e:
        print(f"   ✗ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Export to Word
    print("\n3. Exporting to Word document...")
    from src.proposal.export_word import export_proposal_to_word, sections_to_text

    # Save text version
    text_path = output_dir / "test-proposal.txt"
    text_content = sections_to_text(sections)
    text_path.write_text(text_content, encoding="utf-8")
    print(f"   ✓ Saved text: {text_path}")
    
    # Save Word version
    docx_path = output_dir / "test-proposal.docx"
    export_proposal_to_word(sections, docx_path, title="Test Proposal")
    print(f"   ✓ Saved Word: {docx_path}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Integration Test Complete!")
    print("=" * 60)
    print(f"\nOutputs saved to: {output_dir}")
    print(f"  - {writing_xlsx_path.name} ({writing_xlsx_path.stat().st_size:,} bytes)")
    print(f"  - {text_path.name} ({text_path.stat().st_size:,} bytes)")
    print(f"  - {docx_path.name} ({docx_path.stat().st_size:,} bytes)")
    
    # Print section summary
    print("\nSection Summary:")
    total_chars = 0
    for section in sections:
        content_len = len(section.get("content", ""))
        total_chars += content_len
        status = "✓" if content_len > 100 else "⚠"
        print(f"  {status} {section['category']}: {content_len:,} chars")
    print(f"\nTotal content: {total_chars:,} characters")
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the proposal pipeline")
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run full integration test (requires Azure credentials)"
    )
    args = parser.parse_args()
    
    if args.full:
        success = run_full_integration_test()
    else:
        success = run_quick_test()
    
    sys.exit(0 if success else 1)

