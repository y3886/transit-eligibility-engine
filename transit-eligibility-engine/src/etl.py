import re
from pathlib import Path
import pandas as pd
from .config import EXCEL_FILES, PERIPH_SHEET, SOCIO_MUN_SHEET, SOCIO_REG_SHEET, PROCESSED_DIR


def detect_header_row(raw_df: pd.DataFrame, keywords: list) -> int:
    for idx in range(min(15, len(raw_df))):
        row = raw_df.iloc[idx].tolist()
        joined = " ".join([str(x) for x in row])
        for kw in keywords:
            if re.search(kw, joined, flags=re.IGNORECASE):
                return idx
    return 0


def read_excel_sheet(path: Path, sheet_name: str, header_row: int | None = None, keywords: list | None = None) -> pd.DataFrame:
    if header_row is None:
        raw = pd.read_excel(path, sheet_name=sheet_name, header=None)
        header_row = detect_header_row(raw, keywords or [r"סמל", r"שם"])
    df = pd.read_excel(path, sheet_name=sheet_name, header=header_row, dtype=str)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def find_column(df: pd.DataFrame, patterns: list):
    for p in patterns:
        for col in df.columns:
            try:
                if re.search(p, str(col)):
                    return col
            except re.error:
                continue
    return None


def build_master() -> pd.DataFrame:
    # Use header rows observed during inspection
    periph = read_excel_sheet(EXCEL_FILES["periphery"], PERIPH_SHEET, header_row=3)
    socio_mun = read_excel_sheet(EXCEL_FILES["socio_municipal"], SOCIO_MUN_SHEET, header_row=4)
    socio_reg = read_excel_sheet(EXCEL_FILES["socio_regional"], SOCIO_REG_SHEET, header_row=8)

    # Map columns
    periph_code_col = find_column(periph, [r"סמל\s*יישוב", r"סמל"]) or periph.columns[0]
    periph_name_col = find_column(periph, [r"שם\s*יישוב", r"יישוב", r"שם"]) or (periph.columns[periph.columns.size - 1] if periph.columns.size > 1 else periph.columns[0])
    periph_reg_col = find_column(periph, [r"מועצה אזורית", r"שם\s*מועצה"]) or None
    periph_cluster_col = find_column(periph, [r"אשכול.*פריפריאליות", r"אשכול.*פריפרי", r"אשכול"]) or None
    periph_value_col = find_column(periph, [r"ערך.*פריפריאליות", r"ערך מדד"]) or periph_cluster_col

    periph = periph.rename(columns={periph_code_col: "code", periph_name_col: "name"})
    if periph_reg_col:
        periph = periph.rename(columns={periph_reg_col: "regional_name"})
    if periph_cluster_col:
        periph = periph.rename(columns={periph_cluster_col: "periphery_cluster"})
    if periph_value_col:
        periph = periph.rename(columns={periph_value_col: "periphery_value"})

    # Municipal
    mun_code_col = find_column(socio_mun, [r"סמל\s*יישוב", r"סמל"]) or socio_mun.columns[0]
    mun_cluster_col = find_column(socio_mun, [r"אשכול 2021", r"אשכול"]) or None
    socio_mun = socio_mun.rename(columns={mun_code_col: "code"})
    if mun_cluster_col:
        socio_mun = socio_mun.rename(columns={mun_cluster_col: "socio_cluster"})

    # Regional
    reg_code_col = find_column(socio_reg, [r"סמל\s*יישוב", r"סמל"]) or socio_reg.columns[0]
    reg_local_cluster = find_column(socio_reg, [r"אשכול.*יישוב", r"אשכול.*מקומי"]) or find_column(socio_reg, [r"אשכול"]) or None
    reg_regional_cluster = find_column(socio_reg, [r"אשכול.*מועצה", r"אשכול.*רשות", r"אשכול.*רש"]) or None
    socio_reg = socio_reg.rename(columns={reg_code_col: "code"})
    if reg_local_cluster:
        socio_reg = socio_reg.rename(columns={reg_local_cluster: "socio_cluster_local"})
    if reg_regional_cluster:
        socio_reg = socio_reg.rename(columns={reg_regional_cluster: "socio_cluster_regional"})

    cols = [c for c in ["code", "name", "regional_name", "periphery_cluster", "periphery_value"] if c in periph.columns]
    master = periph[cols].copy()

    # Filter rows with valid locality codes (numeric, typically 4 digits)
    master["code"] = master["code"].astype(str).str.strip()
    master = master[master["code"].str.match(r"^\d{1,6}$", na=False)].copy()

    if "socio_cluster" in socio_mun.columns:
        master = master.merge(socio_mun[["code", "socio_cluster"]], on="code", how="left")
    else:
        master["socio_cluster"] = pd.NA

    add_cols = [c for c in ["code", "socio_cluster_local", "socio_cluster_regional"] if c in socio_reg.columns]
    if add_cols:
        master = master.merge(socio_reg[add_cols], on="code", how="left")

    master["socio_cluster"] = master.get("socio_cluster").fillna(master.get("socio_cluster_local")).fillna(master.get("socio_cluster_regional"))
    master["socio_cluster"] = pd.to_numeric(master["socio_cluster"], errors="coerce").astype(pd.Int64Dtype())

    if "periphery_cluster" in master.columns:
        master["periphery_cluster"] = pd.to_numeric(master["periphery_cluster"], errors="coerce").astype(pd.Int64Dtype())
    else:
        master["periphery_cluster"] = pd.NA

    master["is_eligible"] = (master["periphery_cluster"].notna() & (master["periphery_cluster"] <= 5)) | (master["socio_cluster"].notna() & (master["socio_cluster"] <= 5))

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = PROCESSED_DIR / "master_localities.csv"
    json_path = PROCESSED_DIR / "master_localities.json"
    master.to_csv(csv_path, index=False)
    master.to_json(json_path, orient="records", force_ascii=False)

    return master


if __name__ == "__main__":
    m = build_master()
    print(f"Built master with {len(m)} rows")
