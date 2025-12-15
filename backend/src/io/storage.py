# src/io/storage.py
import csv, json, pathlib
from azure.storage.blob import BlobServiceClient
from src.config import settings

_bsc = BlobServiceClient.from_connection_string(settings.az_blob_conn)
_cont = _bsc.get_container_client(settings.az_blob_container)

def save_json(data, path_local: str):
    with open(path_local, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    _upload(path_local)

def save_csv(rows, path_local: str):
    fields = ["id","label","category","modality","section","page_start","page_end","quote","confidence"]
    with open(path_local, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k,"") for k in fields})
    _upload(path_local)

def _upload(path_local: str):
    p = pathlib.Path(path_local)
    blob = _cont.get_blob_client(p.name)
    with open(p, "rb") as fh:
        blob.upload_blob(fh, overwrite=True)
