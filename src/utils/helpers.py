import datetime
import logging
import sys

def current_iso_week() -> str:
    """Returns the current ISO week in format YYYY-Www, e.g., 2026-W23."""
    today = datetime.date.today()
    year, week, _ = today.isocalendar()
    return f"{year}-W{week:02d}"

def iso_week_to_date_range(iso_week: str) -> tuple[datetime.date, datetime.date]:
    """Returns the start (Monday) and end (Sunday) dates for a given ISO week."""
    year_str, week_str = iso_week.split('-W')
    year = int(year_str)
    week = int(week_str)
    start_date = datetime.date.fromisocalendar(year, week, 1)
    end_date = datetime.date.fromisocalendar(year, week, 7)
    return start_date, end_date

def setup_logging(level: int = logging.INFO):
    """Sets up structured logging."""
    logger = logging.getLogger()
    if logger.hasHandlers():
        logger.handlers.clear()
        
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)
