import pandas as pd

def save_excel(reqs: list[dict], path: str):
    cols = ["id","label","category","modality","section","page_start","page_end","quote","confidence","source"]
    df = pd.DataFrame([{k: r.get(k,"") for k in cols} for r in reqs])
    with pd.ExcelWriter(path, engine="XlsxWriter") as wr:
        df.to_excel(wr, sheet_name="Compliance Matrix", index=False)
        ws = wr.sheets["Compliance Matrix"]
        ws.freeze_panes(1, 0)
        ws.set_column(0, len(cols)-1, 22)
