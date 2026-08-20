import pandas as pd
from pathlib import Path
import re

BASE = Path(__file__).resolve().parent.parent
RAW = BASE / "data" / "raw"

files = [
    ("periphery", "מדד הפריפריאליות 2020 כלל היישובים בישראל.xlsx", 'לוח 2'),
    ("socio_mun", "המדד החברתי-כלכלי 2021 רשויות מקומיות.xlsx", 'לוח א1 table A1'),
    ("socio_reg", "המדד החברתי-כלכלי 2021 יישובים במועצות אזוריות.xlsx", 'לוח ב table B'),
]

def detect_header(raw_df, keywords):
    for idx in range(min(15, len(raw_df))):
        row = raw_df.iloc[idx].tolist()
        row = [str(x) for x in row]
        joined = " ".join(row)
        for kw in keywords:
            if re.search(kw, joined, flags=re.IGNORECASE):
                return idx
    return 0

for key, fname, sheet in files:
    path = RAW / fname
    print('\n===', key, fname, 'sheet=', sheet, 'path=', path)
    if not path.exists():
        print('MISSING:', path)
        continue
    raw = pd.read_excel(path, sheet_name=sheet, header=None)
    print('\n-- sample raw rows (0..11) --')
    for i in range(min(12, len(raw))):
        row = raw.iloc[i].tolist()
        cells = []
        for c in row[:12]:
            s = str(c)
            s = s.replace('\n', ' ').strip()
            cells.append(s[:60])
        print(i, ' | ', ' | '.join(cells))

    header_row = detect_header(raw, [r"סמל", r"שם", r"אשכול", r"יישוב", r"רשויות"]) 
    print('\nDetected header_row index:', header_row)
    print('Header row content:')
    print(raw.iloc[header_row].tolist())

    df = pd.read_excel(path, sheet_name=sheet, header=header_row, dtype=str)
    print('\nParsed columns:')
    print(df.columns.tolist()[:40])
    print('\nFirst 5 rows:')
    print(df.head(5).to_string(index=False))

print('\nDone')
