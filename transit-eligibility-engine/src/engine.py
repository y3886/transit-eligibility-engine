from typing import Dict, Any
import pandas as pd


def explain_eligibility(row: pd.Series) -> Dict[str, Any]:
    reasons = {}
    periph = row.get("periphery_cluster")
    socio = row.get("socio_cluster")
    per = int(periph) if pd.notna(periph) else None
    soc = int(socio) if pd.notna(socio) else None
    reasons["periphery_cluster"] = per
    reasons["socio_cluster"] = soc

    eligible = False
    # both
    if per is not None and per <= 5 and soc is not None and soc <= 5:
        eligible = True
        reasons["reason"] = f"זכאי להנחה: עומד בשני התנאים (אשכול פריפריאלי {per} וסוציו-אקונומי {soc})."
    # periphery only
    elif per is not None and per <= 5:
        eligible = True
        reasons["reason"] = f"זכאי להנחה: היישוב משתייך לאשכול פריפריאלי {per} (זכאות באשכולות 1–5)."
    # socio only
    elif soc is not None and soc <= 5:
        eligible = True
        reasons["reason"] = f"זכאי להנחה: היישוב משתייך לאשכול סוציו-אקונומי {soc} (זכאות באשכולות 1–5)."
    else:
        reasons["reason"] = f"אינו זכאי להנחה: אשכול פריפריאלי {per} ואשכול סוציו-אקונומי {soc} (שניהם מעל 5)."

    reasons["is_eligible"] = bool(eligible)
    return reasons
