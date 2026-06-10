import json
import time
from collections import deque
from typing import List, Dict, Any, Optional
from datetime import datetime
import tiktoken
from fuzzywuzzy import fuzz

from groq import Groq

from src.models.types import Cluster, Theme, PulseReport, CleanReview
from src.config import LlmConfig
from src.summarisation.prompts import SYSTEM_PROMPT, CLUSTER_PROMPT_TEMPLATE
from src.utils.helpers import setup_logging
import logging

logger = logging.getLogger(__name__)

class GroqSummariser:
    def __init__(self, config: LlmConfig):
        self.config = config
        self.client = Groq(api_key=config.api_key, max_retries=5, timeout=120.0)
        self.model = config.model
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens_per_run
        
        # Approximate tokenizer since we just need a budget guard
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.tokenizer = None
            
        self.tokens_used = 0
        self.request_history = deque()
        self.rpm_limit = config.rpm_limit
        self.tpm_limit = config.tpm_limit

    def _count_tokens(self, text: str) -> int:
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        # Fallback approximation: 1 token ~= 4 chars
        return len(text) // 4

    def _validate_quotes(self, quotes: List[str], reviews: List[CleanReview], threshold: int = 85) -> List[str]:
        valid_quotes = []
        original_texts = [r.clean_text for r in reviews] + [r.original_text for r in reviews]
        
        for quote in quotes:
            best_score = 0
            for text in original_texts:
                score = fuzz.partial_ratio(quote.lower(), text.lower())
                if score > best_score:
                    best_score = score
            
            if best_score >= threshold:
                valid_quotes.append(quote)
            else:
                logger.warning(f"Discarded fabricated quote (score {best_score}): '{quote}'")
                
        return valid_quotes

    def _enforce_rate_limits(self, estimated_tokens: int):
        while True:
            now = time.time()
            # Clean up history older than 60 seconds
            while self.request_history and now - self.request_history[0][0] > 60:
                self.request_history.popleft()
                
            current_rpm = len(self.request_history)
            current_tpm = sum(t for _, t in self.request_history)
            
            # Leave a small buffer for limits (e.g., limit-1 for RPM, limit-500 for TPM)
            safe_rpm_limit = max(1, self.rpm_limit - 1)
            safe_tpm_limit = max(1000, self.tpm_limit - 500)
            
            if current_rpm >= safe_rpm_limit or (current_tpm + estimated_tokens) > safe_tpm_limit:
                if self.request_history:
                    wait_time = 60 - (now - self.request_history[0][0]) + 0.1
                    if wait_time > 0:
                        logger.info(f"Rate limit approaching (RPM: {current_rpm}/{self.rpm_limit}, TPM: {current_tpm}/{self.tpm_limit}). Sleeping for {wait_time:.1f}s...")
                        time.sleep(wait_time)
                else:
                    if estimated_tokens > safe_tpm_limit:
                        logger.warning(f"Single request estimated at {estimated_tokens} tokens, exceeding TPM limit of {self.tpm_limit}. Proceeding, but may fail.")
                        break
            else:
                break

    def process_cluster(self, cluster: Cluster) -> Optional[Theme]:
        # Skip miscellaneous/noise cluster for theming if we want, but usually cluster_id=0 is miscellaneous
        # We can still summarise it if we want. Let's summarise all provided clusters.
        
        reviews_text = "\n".join(f"- {r.clean_text}" for r in cluster.reviews)
        user_prompt = CLUSTER_PROMPT_TEMPLATE.format(reviews_text=reviews_text)
        
        prompt_tokens = self._count_tokens(SYSTEM_PROMPT) + self._count_tokens(user_prompt)
        if self.tokens_used + prompt_tokens > self.max_tokens:
            logger.error(f"Token budget exceeded ({self.tokens_used} + {prompt_tokens} > {self.max_tokens}). Skipping remaining clusters.")
            return None

        # Expected output token buffer (~500 tokens for JSON payload)
        estimated_total_tokens = prompt_tokens + 500
        self._enforce_rate_limits(estimated_total_tokens)

        logger.info(f"Summarising cluster {cluster.cluster_id} (size: {cluster.size})...")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from Groq")
                
            data = json.loads(content)
            
            # Update token usage
            if response.usage and response.usage.total_tokens:
                actual_tokens = response.usage.total_tokens
                self.tokens_used += actual_tokens
            else:
                actual_tokens = prompt_tokens + self._count_tokens(content)
                self.tokens_used += actual_tokens
                
            self.request_history.append((time.time(), actual_tokens))
                
            raw_quotes = data.get("quotes", [])
            valid_quotes = self._validate_quotes(raw_quotes, cluster.reviews)
            
            return Theme(
                name=data.get("name", "Unknown Theme"),
                summary=data.get("summary", ""),
                quotes=valid_quotes,
                action_ideas=data.get("action_ideas", []),
                cluster_id=cluster.cluster_id,
                size=cluster.size,
                avg_rating=cluster.avg_rating
            )
            
        except Exception as e:
            logger.error(f"Failed to summarise cluster {cluster.cluster_id}: {e}", exc_info=True)
            return None

    def summarise(self, clusters: List[Cluster], product: str, iso_week: str) -> PulseReport:
        self.tokens_used = 0
        themes = []
        total_reviews = 0
        
        for cluster in clusters:
            if cluster.cluster_id == -1:
                # Explicitly skip noise cluster if it was somehow passed in
                continue
                
            theme = self.process_cluster(cluster)
            if theme:
                themes.append(theme)
            
            total_reviews += cluster.size
            
        return PulseReport(
            product=product,
            iso_week=iso_week,
            total_reviews=total_reviews,
            themes=themes,
            generated_at=datetime.now()
        )

if __name__ == "__main__":
    # Simple standalone test stub
    print("Summariser module ready.")
