from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

EXCEL_FILES = {
    "periphery": RAW_DIR / "מדד הפריפריאליות 2020 כלל היישובים בישראל.xlsx",
    "socio_municipal": RAW_DIR / "המדד החברתי-כלכלי 2021 רשויות מקומיות.xlsx",
    "socio_regional": RAW_DIR / "המדד החברתי-כלכלי 2021 יישובים במועצות אזוריות.xlsx",
}

PERIPH_SHEET = "לוח 2"
SOCIO_MUN_SHEET = "לוח א1 table A1"
SOCIO_REG_SHEET = "לוח ב table B"
