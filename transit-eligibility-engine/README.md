# מנוע זכאות תחבורה (Transit Eligibility Engine)

מיקרו‑פרויקט מקומי שמממש קו ETL + מנוע חיפוש ושרתי API כדי:

- לאסוף נתוני פריפריאליות ואשכולות סוציו‑אקונומיים ממסמכי Excel של הלשכה המרכזית לסטטיסטיקה (CBS).
- לנרמל ולמפות שמות יישובים בעברית, לבצע חיפוש דטרמיניסטי + fuzzy ולהחזיר `is_eligible` לפי כללי מדיניות.

**למה זה קיים?**

בתכנון מוצר תחבורתי רוצים לאפשר למשתמשים לבדוק זכאות להנחות על‑פי מקום מגורים שנכתב במחרוזת חופשית (כתובת בשפה חופשית, טעויות הקלדה וכתובות חלקיות). הפרויקט מראה גישת עבודה פשוטה, שקופה וניתנת לשחזור.

**עקרון הפעולה (בקצרה)**

1. ETL: קורא שלוש גלילי Excel, מוציא עמודות מפתח (`code`, `name`, אשכולות) ומייצר `data/processed/master_localities.*`.
2. Normalizer: מנקה מחרוזות עבריות (הסרת ניקוד, ריווח, סימני ציטוט ואיחוד תווים).
3. Index / Matcher: `LocalityIndex` — חיפוש exact-first (כולל whole‑word/substring), ואחריו RapidFuzz לפתרון טייפו/שגיאות הקלדה.
4. Eligibility Engine: `explain_eligibility()` מחזיר הסבר תקין בעברית עם שדות `periphery_cluster`, `socio_cluster`, `is_eligible` ו`reason` אנושי.
5. API: FastAPI עם נקודות קצה `/resolve` (ממשק UI) ו`/api/v1/eligibility/check` (JSON) ו־UI סטטי בסיסי.

**אתגרים שנתקלו ופתרונות**

- קבצי Excel עם כותרות מרובות ושדות לא אחידים → פתרון: זיהוי שורת כותרת דינמי (`detect_header_row`) + חיפוש רגקס על שמות עמודות.
- נתוני NaN / סוגים לא צפויים שקרסו בנרמול או ב‑Pydantic → פתרון: חיזוק `normalize_hebrew()` ויישור טיפוסי `rationale: Dict[str, Any]` ב־Pydantic.
- שגיאות זיהוי בגלל שמות קצרצרים וחופפים ("תל", "התאנה") → פתרון: עדיפות ל־exact whole‑word/substring לפני fuzzy; דה־דופינג תוצאות fuzzy.
- UX לבחירת מועמד במצב אמביגיו — הוחזרו תוצאות `AMBIGUOUS_MATCH` וה־UI מציג כפתור בחירה (נדרש סבב אישור נוסף).

**איך להפעיל (מהיר)**

```bash
# סביבת פיתוח (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# לבנות את המאסטר (העתק קבצי ה‑CBS ל data/raw/ לפי src/config.py)
python -m src.etl

# להריץ את ה‑API (ברירת מחדל 127.0.0.1:8001 אם 8000 תפוס)
.venv\Scripts\python.exe -m uvicorn src.app:app --host 127.0.0.1 --port 8001 --reload
```

**קבצים חשובים**

- `src/etl.py` — קריאה, מיפוי ויצירת `master_localities`.
- `src/normalizer.py` — נרמול טקסט עברי.
- `src/matcher.py` — `LocalityIndex` ו־resolve.
- `src/engine.py` — חישוב והסברת זכאות.
- `src/app.py` — FastAPI + נקודות קצה.

**תרשים ארכיטקטורה**

ראה את הקובץ: `docs/architecture.svg` — מדגים את זרימת הנתונים בין ה־ETL, אינדקס החיפוש, מנוע הזכאות וה־API/UI.

**בדיקות ו‑QA**

- `src/scripts/run_qa_matrix.py` — מקרי בדיקה TC‑01..TC‑08 לריצת אינטגרציה על ה־API, שומר תוצאה ב־`data/qa_results.json` (מוגדר כקובץ נגזר — נמחק מה‑repo ותוכל לבנות מחדש).
- `tests/` — בדיקות יחידה בסיסיות עבור ETL, Matcher ו־API.

רעיונות לשיפורים מיידיים:

- לפצל `src/etl.py` ל־`read/transform/write` עם פונקציות ברורות ויחידות בדיקה.
- לשפר את `LocalityIndex` לטעינה זכרון יעילה יותר (numpy/rapidfuzz.cdist או token‑based index).
- להוסיף endpoint לקונפירמציה `POST /api/v1/eligibility/confirm` כדי שה־UI יאשר בחירה ממועמדים במצב AMBIGUOUS.

---

תמונה/תרשים מצורף: `docs/architecture.svg`

אם תרצה, אני יכול גם:

- להמיר את ה־SVG לתמונה PNG בגודל מותאם ולצרף אותה ל־README כמובנה.
- לבצע את הרה‑פקטור המוצע ב־ETL וב־matcher ולהריץ את ה‑tests.

