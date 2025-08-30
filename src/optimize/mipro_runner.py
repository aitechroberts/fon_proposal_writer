# src/optimize/mipro_runner.py
import dspy, json, pathlib
from src.extraction.modules import Extractor, Classifier, Grounder

def load_pairs(dir_path):  # list[(input_chunk_text, expected_json_array_str)]
    pairs = []
    for p in pathlib.Path(dir_path).glob("*.json"):
        ex = json.loads(p.read_text())
        pairs.append((ex["chunk_text"], json.dumps(ex["expected_reqs"])))
    return pairs

def loss_fn(pred_json: str, gold_json: str) -> float:
    # tiny metric: F1 on ID’d modalities; extend later
    # ... (implement quickly for signal)
    return 1.0

def optimize(train_dir="data/gold/train", val_dir="data/gold/val"):
    trainset = [(t, g) for (t,g) in load_pairs(train_dir)]
    valset   = [(t, g) for (t,g) in load_pairs(val_dir)]

    program = dspy.Module()  # compile a minimal pipeline under one optimizer
    program.extract = Extractor()
    program.classify = Classifier()
    program.ground   = Grounder()

    opt = dspy.MIPROv2(  # jointly optimize instructions + few-shots
        metric=loss_fn, max_bootstrapped_demos=8, init_temperature=0.7
    )
    compiled = opt.compile(program, trainset=trainset, valset=valset)
    return compiled
