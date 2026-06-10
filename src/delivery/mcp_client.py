import json
from typing import Any, Dict, Optional
from contextlib import AsyncExitStack

from mcp.client.sse import sse_client
from mcp.client.session import ClientSession

from src.config import AppConfig

class MCPClient:
    """
    Connects to remote MCP server via SSE, sends JSON-RPC requests, and parses responses.
    """
    def __init__(self, config: AppConfig):
        self.url = config.mcp_server.url
        self._exit_stack: Optional[AsyncExitStack] = None
        self._session: Optional[ClientSession] = None
        self._streams = None

    async def start(self):
        """Connect to remote MCP server via SSE."""
        self._exit_stack = AsyncExitStack()
        
        self._streams = await self._exit_stack.enter_async_context(sse_client(self.url))
        self._session = await self._exit_stack.enter_async_context(ClientSession(*self._streams))
        await self._session.initialize()

    async def stop(self):
        """Graceful disconnect."""
        if self._exit_stack:
            await self._exit_stack.aclose()
            self._session = None
            self._streams = None
            self._exit_stack = None

    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """Call an MCP tool with timeout and error handling."""
        if not self._session:
            raise RuntimeError("MCPClient is not started. Call start() first.")
            
        result = await self._session.call_tool(tool_name, arguments=params)
        
        if result.isError:
            raise Exception(f"Tool {tool_name} error: {result.content}")
            
        if not result.content:
            return None
            
        text_content = next((item.text for item in result.content if item.type == "text"), None)
        if text_content:
            try:
                return json.loads(text_content)
            except json.JSONDecodeError:
                return text_content
                
        return result.content

    async def append_doc_section(self, payload: Dict[str, Any]) -> Any:
        return await self.call_tool("docs.appendSection", payload)

    async def find_doc_section(self, payload: Dict[str, Any]) -> Any:
        return await self.call_tool("docs.findSection", payload)

    async def create_draft(self, payload: Dict[str, Any]) -> Any:
        return await self.call_tool("gmail.createDraft", payload)

    async def send_draft(self, draft_id: str) -> Any:
        return await self.call_tool("gmail.send", {"draftId": draft_id})

    async def find_sent_email(self, query: str) -> Any:
        return await self.call_tool("gmail.findMessage", {"query": query})
