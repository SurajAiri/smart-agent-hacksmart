"""
Tool definitions for Battery Smart driver support LLM function calling.

These tools follow the OpenAI function calling schema,
which is compatible with Groq and most LLM providers.

Tools available:
1. get_swap_history - Swap history lookup + invoice explanation
2. find_nearest_station - Nearest Battery Smart station + real-time availability
3. get_subscription_info - Subscription plan validity + renewals + pricing
4. get_leave_info - Leave information + nearest DSK for activation
5. escalate_to_support - Escalation to human support
"""
from typing import List, Dict, Any


# Tool definitions in OpenAI format
TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_swap_history",
            "description": "Get battery swap history and invoice breakdown for a driver. Use when user asks about their recent swaps, swap details, invoice explanation, billing breakdown, or wants to understand charges. This includes primary swap (₹170), secondary swap (₹70), service charges (₹40/swap), and leave penalty recovery (₹60/swap).",
            "parameters": {
                "type": "object",
                "properties": {
                    "driver_id": {
                        "type": "string",
                        "description": "Driver ID. If not provided, uses the current caller's ID."
                    },
                    "include_invoice": {
                        "type": "boolean",
                        "description": "Whether to include detailed invoice breakdown. Default true."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of recent swaps to retrieve (default: 5, max: 10)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_nearest_station",
            "description": "Find nearest Battery Smart stations with real-time battery availability. Use when user asks about nearby stations, where to swap battery, station locations, battery availability, or wait times. Can also find DSK (Driver Service Kendra) for subscription activation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "User's current latitude. If not provided, uses default location."
                    },
                    "longitude": {
                        "type": "number",
                        "description": "User's current longitude. If not provided, uses default location."
                    },
                    "dsk_only": {
                        "type": "boolean",
                        "description": "If true, only return DSK stations that can handle subscription activation and leave management."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of stations to return (default: 3, max: 5)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_subscription_info",
            "description": "Get driver's subscription plan details, validity, renewal options and pricing. Use when user asks about their plan, subscription status, renewal, plan expiry, available plans, or pricing for daily/weekly/monthly/unlimited plans.",
            "parameters": {
                "type": "object",
                "properties": {
                    "driver_id": {
                        "type": "string",
                        "description": "Driver ID. If not provided, uses the current caller's ID."
                    },
                    "show_all_plans": {
                        "type": "boolean",
                        "description": "If true, include all available subscription plans and their pricing."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_leave_info",
            "description": "Get driver's leave information including free leaves (4 days/month), used leaves, pending penalties (₹120 per excess leave), and penalty recovery status (₹60 recovered per swap). Also finds nearest DSK for leave activation if needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "driver_id": {
                        "type": "string",
                        "description": "Driver ID. If not provided, uses the current caller's ID."
                    },
                    "find_nearest_dsk": {
                        "type": "boolean",
                        "description": "If true, also return nearest DSK location for leave activation."
                    },
                    "latitude": {
                        "type": "number",
                        "description": "User's latitude for finding nearest DSK."
                    },
                    "longitude": {
                        "type": "number",
                        "description": "User's longitude for finding nearest DSK."
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
            "description": "Escalate an issue to human support agent. Use ONLY when: (1) user explicitly asks to speak to a human/agent, (2) there's a battery or vehicle emergency, (3) the issue cannot be resolved through other tools, (4) user is frustrated after multiple attempts, (5) complex payment disputes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "enum": ["battery_issue", "station_problem", "payment_dispute", "subscription_issue", "vehicle_breakdown", "safety_concern", "other_urgent"],
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
