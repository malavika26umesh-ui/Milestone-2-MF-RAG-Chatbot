import re
from enum import Enum

class QueryCategory(Enum):
    FAQ = "faq"
    ADVISORY = "advisory"
    OUT_OF_SCOPE = "out_of_scope"
    PII_DETECTED = "pii_detected"

class QueryRouter:
    def __init__(self):
        # Patterns for advisory/comparative queries (§7.1)
        self.advisory_patterns = [
            r"should i",
            r"which is better",
            r"best fund",
            r"recommend",
            r"suggest a fund",
            r"investment advice",
            r"how much should i",
            r"is it good to",
            r"better than",
            r"vs",
            r"compare",
            r"ranking",
            r"i am \d+ years? old", # Personal situation
        ]
        
        # Heuristic PII patterns (§7.3)
        self.pii_patterns = {
            "PAN": r"[A-Z]{5}[0-9]{4}[A-Z]{1}",
            "Aadhaar": r"\d{4}\s?\d{4}\s?\d{4}",
            "Phone": r"\b\d{10}\b",
            "Email": r"[\w\.-]+@[\w\.-]+\.\w+",
        }

    def route(self, query: str) -> QueryCategory:
        query_lowered = query.lower().strip()
        
        # 1. Check for PII
        for label, pattern in self.pii_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                print(f"PII Detected: {label}")
                return QueryCategory.PII_DETECTED
        
        # 2. Check for Advisory
        for pattern in self.advisory_patterns:
            if re.search(pattern, query_lowered):
                print(f"Advisory Query Detected: matched '{pattern}'")
                return QueryCategory.ADVISORY
        
        # 3. Basic Out-of-Scope (very broad keywords not related to MF/HDFC)
        # For now, we assume most other things are FAQ or will be caught by LLM
        return QueryCategory.FAQ
