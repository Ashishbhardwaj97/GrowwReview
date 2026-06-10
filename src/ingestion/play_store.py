import time
import logging
import datetime as dt
from typing import List

from google_play_scraper import reviews, Sort

from src.models.types import RawReview
from src.config import IngestionConfig
from src.utils.helpers import current_iso_week, iso_week_to_date_range

logger = logging.getLogger(__name__)

def fetch_reviews(
    product_id: str,
    config: IngestionConfig,
    iso_week: str
) -> List[RawReview]:
    """
    Fetches reviews from Google Play Store for the given product.
    Collects reviews up to `config.window_weeks` back from the start of `iso_week`.
    """
    start_date, _ = iso_week_to_date_range(iso_week)
    cutoff_date = start_date - dt.timedelta(weeks=config.window_weeks)
    cutoff_datetime = dt.datetime.combine(cutoff_date, dt.time.min)

    logger.info(f"Fetching reviews for {product_id} back to {cutoff_datetime.isoformat()}")

    continuation_token = None
    all_raw_reviews: List[RawReview] = []
    
    while len(all_raw_reviews) < config.max_reviews:
        # Fetch a page of reviews
        result, continuation_token = reviews(
            product_id,
            lang=config.language,
            country='in', # Defaulting to India for Groww
            sort=Sort.NEWEST,
            count=199,
            continuation_token=continuation_token
        )
        
        if not result:
            break
            
        oldest_in_batch = result[-1]['at']
        
        for r in result:
            review_at = r['at']
            if review_at < cutoff_datetime:
                continue
                
            raw_review = RawReview(
                review_id=r['reviewId'],
                text=r['content'] if r['content'] else "",
                rating=r['score'],
                app_version=r['reviewCreatedVersion'],
                created_at=review_at
            )
            all_raw_reviews.append(raw_review)
            
        if oldest_in_batch < cutoff_datetime:
            logger.info("Reached reviews older than cutoff date. Stopping.")
            break
            
        if not continuation_token:
            break
            
        # Rate limiting between pages
        time.sleep(1.0)
        
    all_raw_reviews = all_raw_reviews[:config.max_reviews]
    logger.info(f"Fetched {len(all_raw_reviews)} reviews.")
    return all_raw_reviews

if __name__ == "__main__":
    import argparse
    from src.utils.helpers import setup_logging
    
    setup_logging()
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--product", required=True)
    parser.add_argument("--weeks", type=int, default=2)
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()
    
    config = IngestionConfig(
        window_weeks=args.weeks,
        max_reviews=args.limit,
        language="en"
    )
    
    # For Play Store, product id usually needs to be the package name. 
    # E.g. 'com.nextbillion.groww' instead of just 'groww'.
    # For testing from command line we just pass the exact string
    
    iso = current_iso_week()
    res = fetch_reviews(
        product_id=args.product,
        config=config,
        iso_week=iso
    )
    
    for r in res[:5]:
        print(r)
    print(f"Total fetched: {len(res)}")
