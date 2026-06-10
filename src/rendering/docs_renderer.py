import json
from typing import List, Dict, Any, Tuple
from src.models.types import PulseReport

class DocsRequestBuilder:
    def __init__(self, start_index: int = 1):
        self.current_index = start_index
        self.requests: List[Dict[str, Any]] = []

    def insert_text(self, text: str):
        if not text:
            return
        self.requests.append({
            "insertText": {
                "location": {"index": self.current_index},
                "text": text
            }
        })
        self.current_index += len(text)

    def update_paragraph_style(self, style: str, start: int, end: int):
        self.requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": start, "endIndex": end},
                "paragraphStyle": {"namedStyleType": style},
                "fields": "namedStyleType"
            }
        })

    def update_text_style(self, bold: bool = False, italic: bool = False, start: int = 0, end: int = 0):
        self.requests.append({
            "updateTextStyle": {
                "range": {"startIndex": start, "endIndex": end},
                "textStyle": {"bold": bold, "italic": italic},
                "fields": "bold,italic"
            }
        })

    def create_bullet_list(self, start: int, end: int):
        self.requests.append({
            "createParagraphBullets": {
                "range": {"startIndex": start, "endIndex": end},
                "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE"
            }
        })

def generate_docs_requests(report: PulseReport) -> List[Dict[str, Any]]:
    """
    Generates Google Docs API batchUpdate requests.
    Assumes insertion at index 1. The MCP server should shift indices 
    based on the actual end of the document.
    """
    builder = DocsRequestBuilder(start_index=1)
    
    # Section Heading
    product_name = report.product.capitalize()
    heading_text = f"{product_name} — Review Pulse — {report.iso_week}\n"
    start_heading = builder.current_index
    builder.insert_text(heading_text)
    builder.update_paragraph_style("HEADING_2", start_heading, builder.current_index)
    
    # Themes
    for theme in report.themes:
        builder.insert_text("\n")
        
        # Theme name (Bold) + Summary
        start_theme = builder.current_index
        theme_title = f"{theme.name}"
        builder.insert_text(theme_title)
        builder.update_text_style(bold=True, start=start_theme, end=builder.current_index)
        
        builder.insert_text(f": {theme.summary}\n")
        
        # Quotes
        if theme.quotes:
            builder.insert_text("Quotes:\n")
            start_quotes_list = builder.current_index
            for quote in theme.quotes:
                start_quote = builder.current_index
                builder.insert_text(f"{quote}\n")
                builder.update_text_style(italic=True, start=start_quote, end=builder.current_index - 1)
            builder.create_bullet_list(start_quotes_list, builder.current_index)
            
        # Action Ideas
        if theme.action_ideas:
            builder.insert_text("Action Ideas:\n")
            start_actions_list = builder.current_index
            for action in theme.action_ideas:
                builder.insert_text(f"{action}\n")
            builder.create_bullet_list(start_actions_list, builder.current_index)
            
    # Metadata footer
    builder.insert_text("\n")
    footer_text = f"Total Reviews: {report.total_reviews} | Generated at: {report.generated_at.isoformat()}\n"
    start_footer = builder.current_index
    builder.insert_text(footer_text)
    builder.update_text_style(italic=True, start=start_footer, end=builder.current_index)
    
    return builder.requests
