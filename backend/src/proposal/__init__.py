# app/src/proposal/__init__.py
"""
Proposal writing module for generating government proposal documents
from extracted RFP requirements.
"""

from .signatures import WriteSectionSinglePass, AnalyzeSectionThemes, DraftSectionFromThemes
from .modules import SinglePassWriter, TwoStageWriter, ProposalGenerator
from .export_word import export_proposal_to_word

__all__ = [
    "WriteSectionSinglePass",
    "AnalyzeSectionThemes", 
    "DraftSectionFromThemes",
    "SinglePassWriter",
    "TwoStageWriter",
    "ProposalGenerator",
    "export_proposal_to_word",
]

