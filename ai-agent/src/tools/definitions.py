"""
Tool definitions for LLM function calling.

These tools follow the OpenAI function calling schema,
which is compatible with Groq and most LLM providers.
"""
from typing import List, Dict, Any


# Tool definitions in OpenAI format
TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_trip_status",
            "description": "Get the current trip status, ETA, fare, and route information. Use this when the user asks about their current ride, trip status, estimated arrival time, or fare.",
            "parameters": {
                "type": "object",
                "properties": {
                    "trip_id": {
                        "type": "string",
                        "description": "Optional trip ID. If not provided, returns the current active trip."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_driver_info",
            "description": "Get information about the driver including name, vehicle details, rating, and contact. Use when user asks about driver details, car info, or wants to identify their ride.",
            "parameters": {
                "type": "object",
                "properties": {
                    "driver_id": {
                        "type": "string",
                        "description": "Optional driver ID. If not provided, returns info for current trip's driver."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_faq",
            "description": "Search frequently asked questions about pricing, cancellation, payment methods, safety features, refunds, lost items, driver earnings, or vehicle requirements. Use for general policy or how-to questions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The user's question or topic to search for (e.g., 'cancellation policy', 'payment methods', 'safety features')"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_trip_history",
            "description": "Get the user's recent trip history. Use when user asks about past rides, previous trips, or ride history.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of recent trips to retrieve (default: 5, max: 10)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_support",
            "description": "Escalate an issue to human support. Use ONLY when: (1) user explicitly asks to speak to a human, (2) there's an emergency or safety concern, (3) the issue cannot be resolved through other tools, (4) user is very frustrated after multiple attempts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "enum": ["accident_emergency", "harassment", "payment_fraud", "account_blocked", "legal_issue", "other_urgent"],
                        "description": "Category of the escalation"
                    },
                    "description": {
                        "type": "string",
                        "description": "Brief description of the issue for the support agent"
                    }
                },
                "required": ["reason", "description"]
            }
        }
    }
]


def get_tools_list() -> List[Dict[str, Any]]:
    """Return the list of available tools in OpenAI format."""
    return TOOLS


def get_tool_names() -> List[str]:
    """Get list of all tool function names."""
    return [tool["function"]["name"] for tool in TOOLS]
