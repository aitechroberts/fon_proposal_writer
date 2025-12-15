import yaml
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any

import dspy

logger = logging.getLogger(__name__)

@dataclass
class Variant:
    name: str
    temperature: float
    flags: Dict[str, Any]

def load_variant(path: str = "config.yaml") -> Variant:
    """Load configuration variant from YAML file."""
    try:
        config_path = Path(path)
        if not config_path.exists():
            logger.warning(f"Config file {path} not found, using defaults")
            return Variant(name="conservative", temperature=0.0, flags={})
        
        data = yaml.safe_load(config_path.read_text())
        name = data.get("default_variant", "conservative")
        
        if "prompt_variants" not in data or name not in data["prompt_variants"]:
            logger.warning(f"Variant {name} not found in config, using defaults")
            return Variant(name="conservative", temperature=0.0, flags={})
        
        cfg = data["prompt_variants"][name]
        return Variant(
            name=name, 
            temperature=float(cfg.get("temperature", 0.0)), 
            flags=cfg
        )
    except Exception as e:
        logger.error(f"Failed to load variant from {path}: {e}")
        return Variant(name="conservative", temperature=0.0, flags={})

def apply_variant(variant: Variant) -> None:
    """Apply variant configuration to DSPy settings."""
    try:
        # Get current LM configuration
        current_lm = dspy.settings.lm
        if current_lm is None:
            logger.warning("No DSPy LM configured, cannot apply variant")
            return
        
        # Create new LM with updated temperature
        new_lm = dspy.LM(
            model=current_lm.model,
            model_type=getattr(current_lm, 'model_type', 'chat'),
            temperature=variant.temperature,
            max_tokens=getattr(current_lm, 'max_tokens', 4000)
        )
        
        # Update DSPy configuration
        dspy.configure(lm=new_lm, adapter=dspy.settings.adapter)
        
        logger.info(f"Applied variant '{variant.name}' with temperature {variant.temperature}")
        
    except Exception as e:
        logger.error(f"Failed to apply variant {variant.name}: {e}")
