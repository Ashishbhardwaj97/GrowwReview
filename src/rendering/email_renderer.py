from src.models.types import PulseReport
from src.config import AppConfig

def get_email_subject(report: PulseReport, config: AppConfig) -> str:
    """
    Generates the email subject using the template from config.
    Example template: "Groww Review Pulse — Week {iso_week}"
    """
    template = config.delivery.email_subject_template
    try:
        return template.format(iso_week=report.iso_week, product=report.product.capitalize())
    except KeyError:
        return template

def generate_deep_link(doc_id: str, heading_id: str) -> str:
    """
    Generates a deep link to the specific heading in the Google Doc.
    """
    return f"https://docs.google.com/document/d/{doc_id}/edit#heading={heading_id}"

def render_email_html(report: PulseReport, doc_id: str, heading_id: str) -> str:
    """
    Builds the HTML version of the email.
    """
    deep_link = generate_deep_link(doc_id, heading_id)
    
    html = [
        f'<div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">',
        f"<h2>{report.product.capitalize()} — Review Pulse — {report.iso_week}</h2>",
        f"<p>Total Reviews Processed: <strong>{report.total_reviews}</strong></p>",
        "<h3>Top Themes:</h3>",
        "<ul>"
    ]
    
    for theme in report.themes:
        html.append(f"<li><strong>{theme.name}:</strong> {theme.summary}</li>")
        
    html.extend([
        "</ul>",
        "<br/>",
        f'<p><a href="{deep_link}" style="display: inline-block; padding: 10px 20px; background-color: #0066cc; color: #ffffff; text-decoration: none; border-radius: 5px;">Read full report &rarr;</a></p>',
        "</div>"
    ])
    
    return "\n".join(html)

def render_email_text(report: PulseReport, doc_id: str, heading_id: str) -> str:
    """
    Builds the plain-text fallback version of the email.
    """
    deep_link = generate_deep_link(doc_id, heading_id)
    
    lines = [
        f"{report.product.capitalize()} — Review Pulse — {report.iso_week}",
        f"Total Reviews Processed: {report.total_reviews}",
        "",
        "Top Themes:"
    ]
    
    for theme in report.themes:
        lines.append(f"- {theme.name}: {theme.summary}")
        
    lines.extend([
        "",
        "Read full report here:",
        deep_link
    ])
    
    return "\n".join(lines)
