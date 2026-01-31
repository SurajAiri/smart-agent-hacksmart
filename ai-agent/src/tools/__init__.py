"""
Tools module for LLM function calling.

Provides intent detection and tool execution for driver queries.
"""
from src.tools.definitions import TOOLS, get_tools_list
from src.tools.handlers import register_tools, handle_tool_call

__all__ = [
    "TOOLS",
    "get_tools_list",
    "register_tools",
    "handle_tool_call",
]
