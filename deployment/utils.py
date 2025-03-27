from pypdf import PdfReader
import pandas as pd

def read_csv_xlsx(path: str) -> str:
    if path.endswith(".xlsx"):
        df = pd.read_excel(path)
        return df.to_string(index=False)
    else:
        df = pd.read_csv(path)
        return df.to_string(index=False)

def read_pdf(path: str) -> str:
    with open(path, "rb") as f:
        reader = PdfReader(f)
        text = ""
        for page in reader.pages:
            text += page.extractText()

    return text

