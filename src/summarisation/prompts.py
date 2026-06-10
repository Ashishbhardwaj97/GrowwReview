SYSTEM_PROMPT = """You are an expert product analyst.
Your task is to analyze a cluster of user reviews for an app and extract a single, overarching theme.
You must be strictly data-driven. Do NOT hallucinate quotes or ideas not present in the reviews.
Do not act as an AI assistant. Just return the structured data exactly as requested."""

CLUSTER_PROMPT_TEMPLATE = """Review Cluster Data:
{reviews_text}

Analyze the reviews above. Produce a JSON object with the following schema:
{{
  "name": "A short, punchy name for this theme (e.g., 'Login Failures' or 'Great UI')",
  "summary": "A concise summary of what users are saying about this theme",
  "quotes": [
    "Exact quote 1 from the reviews",
    "Exact quote 2 from the reviews"
  ],
  "action_ideas": [
    "Actionable idea 1 based on this theme",
    "Actionable idea 2 based on this theme"
  ]
}}

Important:
1. 'quotes' MUST be exact, word-for-word substrings of the provided reviews. Do not modify or paraphrase them.
2. Return ONLY the JSON object. No markdown formatting like ```json, just the raw JSON.
"""
