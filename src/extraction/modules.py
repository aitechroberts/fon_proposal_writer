# src/extraction/modules.py
import json
import dspy
from .signatures import ExtractReqs, ClassifyReq, GroundReq

class Extractor(dspy.Module):
    def __init__(self):
        super().__init__()
        self.pred = dspy.Predict(ExtractReqs)

    def forward(self, chunk):
        out = self.pred(chunk_text=chunk["text"])
        return json.loads(out.json or "[]")

class Classifier(dspy.Module):
    def __init__(self):
        super().__init__()
        self.pred = dspy.Predict(ClassifyReq)

    def forward(self, req):
        out = self.pred(req_json=json.dumps(req))
        return json.loads(out.json)

class Grounder(dspy.Module):
    def __init__(self):
        super().__init__()
        self.pred = dspy.Predict(GroundReq)

    def forward(self, chunk, req):
        out = self.pred(chunk_text=chunk["text"], req_json=json.dumps(req))
        return json.loads(out.json)
