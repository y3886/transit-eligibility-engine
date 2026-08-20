from typing import List, Tuple
from rapidfuzz import process, fuzz
from .normalizer import normalize_hebrew
import pandas as pd
import re


class LocalityIndex:
    def __init__(self, master_df: pd.DataFrame):
        self.df = master_df.copy()
        # ensure name column is string
        self.df["name"] = self.df["name"].fillna("").astype(str)
        self.df["nm_name"] = self.df["name"].apply(normalize_hebrew)
        # map normalized name -> code
        self.choices = {n: c for n, c in zip(self.df["nm_name"].tolist(), self.df["code"].astype(str).tolist()) if n}
        # prepare list of names sorted by length desc for exact-substring matching (prefer multi-word longer names)
        self.sorted_names = sorted(self.choices.keys(), key=lambda s: len(s), reverse=True)

    def resolve(self, query: str, limit: int = 5) -> List[Tuple[str, str, float, str]]:
        q = normalize_hebrew(query)
        if not q:
            return []
        # Exact string match
        if q in self.choices:
            code = self.choices[q]
            name = self.df.loc[self.df["code"].astype(str) == str(code), "name"].iat[0]
            return [(str(code), name, 100.0, "EXACT_MATCH")]

        # Exact whole-word / substring match priority: check if any official locality
        # name appears in the cleaned query as a whole token. Prefer longer names first.
        for nm in self.sorted_names:
            # match as a whole token using whitespace/punctuation boundaries
            pattern = rf'(?<!\S){re.escape(nm)}(?!\S)'
            if re.search(pattern, q):
                code = self.choices.get(nm)
                if code is None:
                    continue
                name = self.df.loc[self.df["code"].astype(str) == str(code), "name"].iat[0]
                return [(str(code), name, 100.0, "EXACT_MATCH")]

        # Fuzzy
        # Fuzzy fallback
        results = process.extract(q, list(self.choices.keys()), scorer=fuzz.WRatio, limit=limit * 2)
        out = []
        seen_codes = set()
        for name_match, score, _ in results:
            code = self.choices.get(name_match)
            if code is None:
                continue
            if code in seen_codes:
                continue
            seen_codes.add(code)
            name = self.df.loc[self.df["code"].astype(str) == str(code), "name"].iat[0]
            out.append((str(code), name, float(score), "fuzzy"))
            if len(out) >= limit:
                break
        return out
