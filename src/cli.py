import argparse
import asyncio
import json
import logging
import os
from datetime import datetime
from dataclasses import asdict

from src.config import load_config
from src.utils.helpers import setup_logging, current_iso_week
from src.utils.run_log import RunLogManager
from src.ingestion.play_store import fetch_reviews
from src.preprocessing import preprocess
from src.embedding.embedder import get_embedder
from src.clustering.clusterer import Clusterer
from src.summarisation.summariser import GroqSummariser
from src.rendering.docs_renderer import generate_docs_requests
from src.rendering.email_renderer import render_email_html, render_email_text, get_email_subject
from src.delivery.mcp_client import MCPClient
from src.models.types import RunRecord

logger = logging.getLogger(__name__)

def run_pipeline(args):
    config = load_config()
    setup_logging()
    
    product = args.product
    iso_week = current_iso_week() if args.week == "auto" else args.week
    
    run_log = RunLogManager(config)
    
    # Layer 1 Idempotency Check
    if not args.force and run_log.has_run(product, iso_week):
        logger.info(f"Run for {product} {iso_week} already successfully completed. Skipping pipeline.")
        return
        
    logger.info(f"Starting Groww Review Pulse pipeline for {product} week {iso_week}")
    
    try:
        # 1. Ingestion
        logger.info("Stage 1: Ingesting reviews...")
        raw_reviews = fetch_reviews(
            product_id=config.product.play_store_id,
            config=config.ingestion,
            iso_week=iso_week
        )
        logger.info(f"Ingested {len(raw_reviews)} raw reviews.")
        
        # Save raw reviews to JSON if requested
        if args.export_raw:
            os.makedirs("data", exist_ok=True)
            export_path = f"data/raw_reviews_{product}_{iso_week}.json"
            
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump([asdict(r) for r in raw_reviews], f, default=str, indent=2)
            logger.info(f"Exported raw reviews to {export_path}")
        
        # 2. Preprocessing
        logger.info("Stage 2: Preprocessing reviews...")
        clean_reviews = preprocess(raw_reviews, config.preprocessing)
        logger.info(f"Cleaned {len(clean_reviews)} reviews.")
        
        if not clean_reviews:
            logger.warning("No reviews left after preprocessing. Exiting pipeline.")
            return

        # 3. Embedding
        logger.info("Stage 3: Embedding reviews...")
        embedder = get_embedder(config)
        embedded_reviews = embedder.embed(clean_reviews)
        
        # 4. Clustering
        logger.info("Stage 4: Clustering reviews...")
        clusterer = Clusterer(config.clustering)
        clusters = clusterer.cluster(embedded_reviews)
        logger.info(f"Found {len(clusters)} clusters.")
        
        # 5. LLM Summarisation
        logger.info("Stage 5: LLM Summarisation...")
        summariser = GroqSummariser(config.llm)
        report = summariser.summarise(clusters, product, iso_week)
        logger.info(f"Generated {len(report.themes)} themes in the pulse report.")
        
        # 6. Rendering
        logger.info("Stage 6: Rendering Docs and Email payloads...")
        docs_requests = generate_docs_requests(report)
        section_heading = f"{config.product.display_name} — Review Pulse — {iso_week}"
        
        docs_payload = {
            "docId": config.delivery.google_doc_id,
            "sectionHeading": section_heading,
            "bodyRequests": docs_requests
        }
        
        email_subject = get_email_subject(report, config)
        
        # Dry Run Check
        if args.dry_run:
            logger.info("DRY RUN: Pipeline completed up to rendering.")
            logger.info(f"Would append Docs section: '{section_heading}' to {config.delivery.google_doc_id}")
            logger.info(f"Would send email with subject: '{email_subject}'")
            return

        # 7. Delivery via MCP
        logger.info("Stage 7: Remote MCP Integration...")
        
        async def run_mcp_delivery():
            mcp = MCPClient(config)
            await mcp.start()
            
            try:
                # Layer 2 Idempotency: Google Docs
                logger.info(f"Checking if Docs section '{section_heading}' exists...")
                find_res = await mcp.find_doc_section({
                    "docId": config.delivery.google_doc_id, 
                    "sectionHeading": section_heading
                })
                
                heading_id = None
                if find_res and find_res.get("found"):
                    heading_id = find_res.get("headingId")
                    logger.info(f"Section already exists (headingId: {heading_id}). Skipping Docs append.")
                else:
                    logger.info("Appending new section to Google Docs...")
                    append_res = await mcp.append_doc_section(docs_payload)
                    heading_id = append_res.get("headingId") if append_res else "unknown"
                    logger.info(f"Docs updated successfully. Heading ID: {heading_id}")

                # Prepare Email Payload
                email_html = render_email_html(report, config.delivery.google_doc_id, heading_id)
                email_text = render_email_text(report, config.delivery.google_doc_id, heading_id)
                
                email_payload = {
                    "to": config.delivery.stakeholders,
                    "subject": email_subject,
                    "htmlBody": email_html,
                    "textBody": email_text
                }
                
                # Layer 3 Idempotency: Gmail
                logger.info(f"Checking if email '{email_subject}' was already sent...")
                find_email_res = await mcp.find_sent_email(email_subject)
                
                draft_id = None
                message_id = None
                thread_id = None
                
                if find_email_res and find_email_res.get("found"):
                    message_id = find_email_res.get("messageId")
                    logger.info(f"Email already sent (messageId: {message_id}). Skipping email creation.")
                else:
                    logger.info("Creating Gmail draft...")
                    draft_res = await mcp.create_draft(email_payload)
                    draft_id = draft_res.get("draftId") if draft_res else None
                    logger.info(f"Draft created successfully: {draft_id}")
                    
                    is_draft_only = args.draft_only if args.draft_only else config.delivery.draft_only
                    if is_draft_only:
                        logger.info("DRAFT ONLY mode is active. Skipping email send.")
                    else:
                        if draft_id:
                            logger.info(f"Sending email draft {draft_id}...")
                            send_res = await mcp.send_draft(draft_id)
                            if send_res:
                                message_id = send_res.get("messageId")
                                thread_id = send_res.get("threadId")
                            logger.info(f"Email sent successfully (messageId: {message_id}).")

                # Record Successful Run
                record = RunRecord(
                    product=product,
                    iso_week=iso_week,
                    run_at=datetime.now(),
                    docs_heading_id=heading_id,
                    gmail_draft_id=draft_id,
                    gmail_thread_id=thread_id,
                    status="success"
                )
                run_log.record_run(record)
                
                # Print Run Summary (5A.6)
                logger.info("\n" + "="*40)
                logger.info("RUN SUMMARY")
                logger.info("="*40)
                logger.info(f"Product:           {product}")
                logger.info(f"ISO Week:          {iso_week}")
                logger.info(f"Reviews Ingested:  {len(raw_reviews)}")
                logger.info(f"Clusters Found:    {len(clusters)}")
                logger.info(f"Themes Generated:  {len(report.themes)}")
                logger.info(f"Docs Updated:      {'Yes' if heading_id else 'No'}")
                logger.info(f"Email Draft:       {'Created' if draft_id else 'No'}")
                logger.info(f"Email Sent:        {'Yes' if message_id else 'No'}")
                logger.info("="*40)
                logger.info("Run completed and recorded successfully.")
                
            finally:
                await mcp.stop()
                logger.info("Disconnected from Remote MCP Server.")

        asyncio.run(run_mcp_delivery())
            
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
        raise

def main():
    parser = argparse.ArgumentParser(description="Groww Weekly Review Pulse Pipeline")
    parser.add_argument("--product", type=str, default="groww", help="Product name to run pipeline for")
    parser.add_argument("--week", type=str, default="auto", help="ISO week (e.g. 2026-W23) or 'auto'")
    parser.add_argument("--dry-run", action="store_true", help="Execute without calling MCP APIs")
    parser.add_argument("--draft-only", action="store_true", help="Create email draft but don't send")
    parser.add_argument("--force", action="store_true", help="Force run, skipping idempotency check")
    parser.add_argument("--export-raw", action="store_true", help="Export raw reviews to a JSON file")
    
    args = parser.parse_args()
    
    run_pipeline(args)

if __name__ == "__main__":
    main()
