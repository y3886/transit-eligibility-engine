import httpx
import json

CASE_LIST = [
    ("TC-01", "רוטשילד 10, תל אביב"),
    ("TC-02", "הרצל 1, דימונה"),
    ("TC-03", "רבי עקיבא 30, בני ברק"),
    ("TC-04", "יפו 200, ירושלים"),
    ("TC-05", "מזכירות קיבוץ אילות"),
    ("TC-06", "העצמאות 5, כרמיאל."),
    ("TC-07", "משק 12, תראבין א-צאנע"),
    ("TC-08", "התאנה 14"),
]

OUT = []
client = httpx.Client(timeout=10.0)
for tc, addr in CASE_LIST:
    try:
        r = client.post('http://127.0.0.1:8001/api/v1/eligibility/check', json={'raw_address': addr})
        j = r.json()
    except Exception as e:
        j = {'error': str(e)}
    OUT.append({'case': tc, 'input': addr, 'status_code': r.status_code if 'r' in locals() else None, 'response': j})

with open('data/qa_results.json', 'w', encoding='utf-8') as f:
    json.dump(OUT, f, ensure_ascii=False, indent=2)

print('Wrote data/qa_results.json')
