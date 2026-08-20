from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path

from .models import ResolveRequest, ResolveResponse, ResolveCandidate
from .etl import build_master
from .matcher import LocalityIndex
from .engine import explain_eligibility

app = FastAPI(title="Transit Eligibility Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Build master at startup
MASTER_DF = None
INDEX = None


# Serve static frontend from src/static at /static and return index.html at /
static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", include_in_schema=False)
def root():
    index = static_dir / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"detail": "Not Found"}


@app.on_event("startup")
def startup_event():
    global MASTER_DF, INDEX
    try:
        MASTER_DF = build_master()
        INDEX = LocalityIndex(MASTER_DF)
    except Exception:
        MASTER_DF = None
        INDEX = None


@app.post("/resolve", response_model=ResolveResponse)
def resolve(req: ResolveRequest):
    global INDEX
    if INDEX is None:
        raise HTTPException(status_code=503, detail="Index not ready")
    candidates = INDEX.resolve(req.address)
    c_objs = [ResolveCandidate(locality_code=c[0], locality_name=c[1], score=c[2], matched_by=c[3]) for c in candidates]
    top = c_objs[0] if c_objs else None
    ambiguous = len(c_objs) > 1 and c_objs[0].score - c_objs[1].score < 10
    confidence = top.score / 100.0 if top else 0.0
    rationale = {}
    if top:
        try:
            mask = MASTER_DF["code"].astype(str) == str(top.locality_code)
            if mask.any():
                row = MASTER_DF[mask].iloc[0]
                rationale = explain_eligibility(row)
            else:
                rationale = {}
        except Exception:
            rationale = {}
    return ResolveResponse(query=req.address, candidates=c_objs, top_candidate=top, ambiguous=ambiguous, confidence=confidence, rationale=rationale)


@app.post("/api/v1/eligibility/check")
def api_check(payload: dict):
    global INDEX, MASTER_DF
    try:
        raw = payload.get("raw_address") or payload.get("address")
    except Exception:
        raw = None
    if not raw or not str(raw).strip():
        return {
            "status": "INVALID_INPUT",
            "data": None,
            "error": {"code": "EMPTY_QUERY", "message": "מחרוזת הכתובת אינה יכולה להיות ריקה."},
        }

    if INDEX is None:
        raise HTTPException(status_code=503, detail="Index not ready")

    try:
        candidates = INDEX.resolve(raw)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not candidates:
        return {
            "status": "NOT_FOUND",
            "data": None,
            "error": {"code": "LOCALITY_NOT_RESOLVED", "message": "לא זוהה שם יישוב מוכר בכתובת שהוזנה. אנא ודא כי שם היישוב מופיע במפורש."},
        }

    # build full candidate info from master
    def row_for(code):
        s = str(code)
        try:
            row = MASTER_DF[MASTER_DF["code"].astype(str) == s].iloc[0]
            return row
        except Exception:
            return None

    # ambiguous detection
    ambiguous = len(candidates) > 1 and (candidates[0][2] - candidates[1][2] <= 3)
    if ambiguous:
        cand_list = []
        for c in candidates[:6]:
            row = row_for(c[0])
            cand_list.append({
                "locality_id": int(c[0]) if str(c[0]).isdigit() else c[0],
                "locality_name": c[1],
                "regional_council": row.get("regional_council") if row is not None else None,
                "is_eligible": bool(row.get("is_eligible")) if row is not None else None,
            })
        return {
            "status": "AMBIGUOUS_MATCH",
            "data": {"query": raw, "candidates": cand_list},
            "error": {"code": "MULTIPLE_LOCALITIES_FOUND", "message": "אותרו מספר יישובים תואמים. אנא בחר את היישוב המדויק מתוך הרשימה."},
        }

    # single best match
    top = candidates[0]
    row = row_for(top[0])
    data = {
        "query": raw,
        "matched_locality": {
            "locality_id": int(top[0]) if str(top[0]).isdigit() else top[0],
            "locality_name": top[1],
            "regional_council": row.get("regional_council") if row is not None else None,
            "periphery_cluster": int(row.get("periphery_cluster")) if row is not None and row.get("periphery_cluster") is not None else None,
            "socio_cluster": int(row.get("socio_cluster")) if row is not None and row.get("socio_cluster") is not None else None,
        },
        "is_eligible": bool(row.get("is_eligible")) if row is not None else None,
        "confidence_score": round(top[2] / 100.0, 2),
        "eligibility_reasons": explain_eligibility(row) if row is not None else [],
    }
    return {"status": "SUCCESS", "data": data, "error": None}
