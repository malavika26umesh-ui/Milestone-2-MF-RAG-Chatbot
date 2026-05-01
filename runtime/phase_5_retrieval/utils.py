import re

SCHEME_MAP = {
    "hdfc-large-cap-fund-direct-growth": ["hdfc large cap", "large cap fund"],
    "hdfc-focused-fund-direct-growth": ["hdfc focused", "focused fund"],
    "hdfc-elss-tax-saver-fund-direct-plan-growth": ["hdfc elss", "tax saver", "elss"],
    "hdfc-equity-fund-direct-growth": ["hdfc equity", "equity fund", "flexi cap"],
    "hdfc-balanced-advantage-fund-direct-growth": ["hdfc balanced advantage", "baf", "balanced advantage"],
}

def normalize_query(query: str) -> str:
    """Light normalization as per §5.1 of ragArchitecture.md"""
    # Lowercase, strip punctuation but keep question mark
    query = query.lower().strip()
    # Keep alphanumeric and spaces and question marks
    query = re.sub(r'[^a-z0-9\s\?]', '', query)
    return query

def detect_scheme(query: str) -> str | None:
    """Detect if a scheme is named in the query to support pre-filtering (§5.2)"""
    query_lowered = query.lower()
    for scheme_id, keywords in SCHEME_MAP.items():
        if any(kw in query_lowered for kw in keywords):
            return scheme_id
    return None
