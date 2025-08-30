import yaml, pathlib, dspy
from dataclasses import dataclass

@dataclass
class Variant:
    name: str
    temperature: float
    flags: dict

def load_variant(path="config.yaml") -> Variant:
    data = yaml.safe_load(pathlib.Path(path).read_text())
    name = data.get("default_variant", "conservative")
    cfg  = data["prompt_variants"][name]
    return Variant(name=name, temperature=float(cfg.get("temperature", 0.0)), flags=cfg)

def apply_variant(variant: Variant):
    # adjust LM temperature at runtime without restarting
    current = dspy.settings.get("lm")
    dspy.configure(lm=dspy.LM(current.model, model_type=current.model_type,
                              temperature=variant.temperature, max_tokens=current.max_tokens))
