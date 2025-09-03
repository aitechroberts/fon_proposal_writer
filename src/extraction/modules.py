# src/extraction/modules.py
import json
import logging
from typing import Dict, List, Any
import dspy
from .signatures import ExtractReqs, ClassifyReq, GroundReq

logger = logging.getLogger(__name__)

class Extractor(dspy.Module):
    """Extract requirements from text chunks using DSPy."""
    
    def __init__(self):
        super().__init__()
        self.pred = dspy.Predict(ExtractReqs)

    def forward(self, chunk: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract requirements from a text chunk."""
        try:
            out = self.pred(chunk_text=chunk["text"])
            result = json.loads(out.requirements_json or "[]")
            
            # Ensure result is a list
            if not isinstance(result, list):
                logger.warning(f"Extractor returned non-list: {type(result)}")
                return []
                
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from extractor: {e}")
            logger.debug(f"Raw output: {out.requirements_json}")
            return []
        except Exception as e:
            logger.error(f"Extractor failed: {e}")
            return []

class Classifier(dspy.Module):
    """Classify and normalize requirement objects."""
    
    def __init__(self):
        super().__init__()
        self.pred = dspy.Predict(ClassifyReq)

    def forward(self, req: Dict[str, Any]) -> Dict[str, Any]:
        """Classify and normalize a single requirement."""
        try:
            out = self.pred(req_json=json.dumps(req, ensure_ascii=False))
            result = json.loads(out.classified_json)
            
            # Ensure result is a dict
            if not isinstance(result, dict):
                logger.warning(f"Classifier returned non-dict: {type(result)}")
                return req  # Return original if classification fails
                
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from classifier: {e}")
            logger.debug(f"Raw output: {out.classified_json}")
            return req
        except Exception as e:
            logger.error(f"Classifier failed: {e}")
            return req

class Grounder(dspy.Module):
    """Ground requirements with evidence from source text."""
    
    def __init__(self):
        super().__init__()
        self.pred = dspy.Predict(GroundReq)

    def forward(self, chunk: Dict[str, Any], req: Dict[str, Any]) -> Dict[str, Any]:
        """Ground a requirement with evidence from the source chunk."""
        try:
            out = self.pred(
                chunk_text=chunk["text"], 
                req_json=json.dumps(req, ensure_ascii=False)
            )
            result = json.loads(out.grounded_json)
            
            # Ensure result is a dict
            if not isinstance(result, dict):
                logger.warning(f"Grounder returned non-dict: {type(result)}")
                return req  # Return original if grounding fails
                
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from grounder: {e}")
            logger.debug(f"Raw output: {out.grounded_json}")
            return req
        except Exception as e:
            logger.error(f"Grounder failed: {e}")
            return req
