import httpx
import logging
from typing import Any, Dict, Optional

from src.config import AppConfig

logger = logging.getLogger(__name__)

class MCPClient:
    """
    Temporary REST client to connect to the deployed Google-MCP-Server.
    Note: The remote server is currently a standard FastAPI REST service, not a true MCP Server.
    This client adapts GrowwReview's payloads to the simple text endpoints of that server.
    """
    def __init__(self, config: AppConfig):
        # Strip /sse since the actual server only has /append_to_doc and /create_email_draft
        self.url = config.mcp_server.url.replace("/sse", "")
        self.client: Optional[httpx.AsyncClient] = None

    async def start(self):
        """Connect to remote REST server."""
        self.client = httpx.AsyncClient(base_url=self.url, timeout=60.0)

    async def stop(self):
        """Graceful disconnect."""
        if self.client:
            await self.client.aclose()
            self.client = None

    async def append_doc_section(self, payload: Dict[str, Any]) -> Any:
        """
        Adapts the rich Google Docs batchUpdate payload into a plain text string
        for the remote server's simple /append_to_doc endpoint.
        """
        if not self.client:
            raise RuntimeError("MCPClient is not started. Call start() first.")

        # Extract plain text from the bodyRequests
        content = ""
        for req in payload.get("bodyRequests", []):
            if "insertText" in req:
                content += req["insertText"].get("text", "")

        body = {
            "doc_id": payload.get("docId"),
            "content": content
        }
        
        logger.info(f"Sending POST to {self.url}/append_to_doc")
        res = await self.client.post("/append_to_doc", json=body)
        
        if res.status_code != 200:
            logger.error(f"Failed to append doc: {res.text}")
            res.raise_for_status()
            
        return res.json().get("result", {})

    async def find_doc_section(self, payload: Dict[str, Any]) -> Any:
        # Not supported by google-mcp-server, returning False to trigger append
        return {"found": False}

    async def create_draft(self, payload: Dict[str, Any]) -> Any:
        """
        Sends plain text email body to the /create_email_draft endpoint.
        """
        if not self.client:
            raise RuntimeError("MCPClient is not started. Call start() first.")

        to_str = ", ".join(payload.get("to", []))
        body = {
            "to": to_str,
            "subject": payload.get("subject", ""),
            "body": payload.get("textBody", "")
        }
        
        logger.info(f"Sending POST to {self.url}/create_email_draft")
        res = await self.client.post("/create_email_draft", json=body)
        
        if res.status_code != 200:
            logger.error(f"Failed to create draft: {res.text}")
            res.raise_for_status()
            
        data = res.json().get("result", {})
        # Map Gmail's "id" to "draftId" so cli.py understands the response
        if "id" in data:
            data["draftId"] = data["id"]
            
        return data

    async def send_draft(self, draft_id: str) -> Any:
        # Not supported by google-mcp-server
        logger.warning("send_draft is not supported by the current server.")
        return {"messageId": "mock-sent-id"}

    async def find_sent_email(self, query: str) -> Any:
        # Not supported by google-mcp-server, returning False to trigger create
        return {"found": False}

