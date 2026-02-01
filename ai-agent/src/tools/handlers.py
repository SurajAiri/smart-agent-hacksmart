"""
Tool handlers for LLM function calling.

Each handler processes a specific tool call and returns
formatted results for the LLM to respond with.
"""
from typing import Any, Dict, Optional
from loguru import logger

from pipecat.services.llm_service import FunctionCallParams

from src.tools.mock_data import (
    get_current_trip,
    get_trip_by_id,
    get_driver_info as get_driver_data,
    search_faqs,
    get_trip_history as get_history,
    create_support_ticket,
)


async def handle_get_trip_status(params: FunctionCallParams) -> str:
    """Handle get_trip_status tool call."""
    args = params.arguments
    trip_id = args.get("trip_id")
    
    logger.info(f"Tool call: get_trip_status(trip_id={trip_id})")
    
    if trip_id:
        trip = get_trip_by_id(trip_id)
    else:
        trip = get_current_trip()
    
    if not trip:
        return "No active trip found. You don't seem to have an ongoing ride at the moment."
    
    # Format response based on trip status
    if trip["status"] == "in_progress":
        driver = trip.get("driver", {})
        return (
            f"Your ride is currently in progress. "
            f"Driver {driver.get('name', 'N/A')} is taking you from {trip['pickup']['address']} "
            f"to {trip['dropoff']['address']}. "
            f"Estimated arrival: {trip.get('estimated_arrival', 'calculating...')}. "
            f"Distance: {trip.get('distance_km', 'N/A')} km. "
            f"Estimated fare: ₹{trip.get('fare_estimate', 'N/A')}. "
            f"Payment method: {trip.get('payment_method', 'N/A')}."
        )
    elif trip["status"] == "completed":
        return (
            f"Your trip from {trip['pickup']['address']} to {trip['dropoff']['address']} "
            f"has been completed. Final fare: ₹{trip.get('actual_fare', 'N/A')}. "
            f"Distance: {trip.get('distance_km', 'N/A')} km. "
            f"Payment: {trip.get('payment_method', 'N/A')}."
        )
    else:
        return f"Trip status: {trip['status']}. Details are being updated."


async def handle_get_driver_info(params: FunctionCallParams) -> str:
    """Handle get_driver_info tool call."""
    args = params.arguments
    driver_id = args.get("driver_id")
    
    logger.info(f"Tool call: get_driver_info(driver_id={driver_id})")
    
    # If no driver_id, get from current trip
    if not driver_id:
        trip = get_current_trip()
        if trip:
            driver_id = trip.get("driver_id")
    
    if not driver_id:
        return "No driver information available. You don't have an active ride at the moment."
    
    driver = get_driver_data(driver_id)
    
    if not driver:
        return f"Driver information not found for ID: {driver_id}"
    
    vehicle = driver.get("vehicle", {})
    return (
        f"Your driver is {driver['name']}. "
        f"Vehicle: {vehicle.get('color', '')} {vehicle.get('model', 'N/A')} ({vehicle.get('type', '')}). "
        f"Number plate: {vehicle.get('number', 'N/A')}. "
        f"Rating: {driver.get('rating', 'N/A')} stars with {driver.get('total_trips', 0)} trips completed. "
        f"Contact: {driver.get('phone', 'N/A')}."
    )


async def handle_lookup_faq(params: FunctionCallParams) -> str:
    """Handle lookup_faq tool call."""
    args = params.arguments
    query = args.get("query", "")
    
    logger.info(f"Tool call: lookup_faq(query={query})")
    
    if not query:
        return "Please specify what you'd like to know about."
    
    faqs = search_faqs(query)
    
    if not faqs:
        return (
            f"I couldn't find specific information about '{query}'. "
            "You can ask about pricing, cancellation policy, payment methods, "
            "safety features, refunds, lost items, or driver-related queries."
        )
    
    # Return the most relevant FAQ
    faq = faqs[0]
    return faq["answer"]


async def handle_get_trip_history(params: FunctionCallParams) -> str:
    """Handle get_trip_history tool call."""
    args = params.arguments
    limit = min(args.get("limit", 5), 10)
    
    logger.info(f"Tool call: get_trip_history(limit={limit})")
    
    trips = get_history(limit)
    
    if not trips:
        return "No trip history found."
    
    # Format trip history
    history_lines = []
    for i, trip in enumerate(trips, 1):
        driver = trip.get("driver", {})
        status = trip.get("status", "unknown")
        fare = trip.get("actual_fare") or trip.get("fare_estimate", "N/A")
        history_lines.append(
            f"{i}. {trip['pickup']['address']} to {trip['dropoff']['address']} - "
            f"₹{fare} ({status}) with {driver.get('name', 'N/A')}"
        )
    
    return f"Your recent trips:\n" + "\n".join(history_lines)


async def handle_escalate_to_support(params: FunctionCallParams) -> str:
    """Handle escalate_to_support tool call."""
    args = params.arguments
    reason = args.get("reason", "other_urgent")
    description = args.get("description", "User requested support")
    
    logger.info(f"Tool call: escalate_to_support(reason={reason}, description={description})")
    
    # Create support ticket (existing functionality)
    ticket = create_support_ticket(reason, description)
    
    # Also trigger handoff system if reason is high priority
    try:
        from src.core.conversation_tracker import get_conversation_tracker
        from src.core.escalation_engine import get_escalation_engine
        from src.core.handoff_manager import get_handoff_manager
        from src.core.models import HandoffTrigger, IntentCategory
        
        # Map escalation reason to trigger
        trigger_map = {
            "accident_emergency": HandoffTrigger.SAFETY_EMERGENCY,
            "harassment": HandoffTrigger.HARASSMENT_REPORT,
            "payment_fraud": HandoffTrigger.FRAUD_DETECTION,
            "account_blocked": HandoffTrigger.EXPLICIT_REQUEST,
            "legal_issue": HandoffTrigger.EXPLICIT_REQUEST,
            "other_urgent": HandoffTrigger.EXPLICIT_REQUEST,
        }
        
        trigger = trigger_map.get(reason, HandoffTrigger.EXPLICIT_REQUEST)
        
        # Record this as an escalation request intent
        tracker = get_conversation_tracker()
        # Find the call_id from active conversations (tool calls happen in context)
        for call_id in tracker.get_active_conversations():
            state = tracker.get_conversation(call_id)
            if state and not state.escalation_triggered:
                # Add escalation request to high risk intents
                state.high_risk_intents_detected.append(IntentCategory.ESCALATION_REQUEST)
                
                # Trigger handoff
                engine = get_escalation_engine()
                priority = engine.get_priority(state, trigger)
                
                handoff_manager = get_handoff_manager()
                await handoff_manager.trigger_handoff(
                    state=state,
                    trigger=trigger,
                    priority=priority,
                )
                logger.info(f"Handoff triggered via escalate_to_support for call {call_id}")
                break
    except Exception as e:
        logger.error(f"Error triggering handoff from tool: {e}")
    
    return (
        f"I'm connecting you with a support agent right away. Ticket ID: {ticket['ticket_id']}. "
        f"Priority: {ticket['priority']}. "
        "A human agent will join this call shortly. Please stay on the line."
    )


# Tool handler registry
TOOL_HANDLERS = {
    "get_trip_status": handle_get_trip_status,
    "get_driver_info": handle_get_driver_info,
    "lookup_faq": handle_lookup_faq,
    "get_trip_history": handle_get_trip_history,
    "escalate_to_support": handle_escalate_to_support,
}


async def handle_tool_call(params: FunctionCallParams) -> Optional[str]:
    """
    Route tool call to appropriate handler.
    
    Args:
        params: FunctionCallParams from Pipecat
        
    Returns:
        Tool result as string, or None if tool not found
    """
    function_name = params.function_name
    handler = TOOL_HANDLERS.get(function_name)
    
    if handler:
        try:
            result = await handler(params)
            logger.debug(f"Tool {function_name} result: {result[:100]}...")
            return result
        except Exception as e:
            logger.error(f"Tool {function_name} error: {e}")
            return f"Sorry, there was an error processing your request. Please try again."
    else:
        logger.warning(f"Unknown tool: {function_name}")
        return None


def register_tools(llm_service: Any) -> None:
    """
    Register all tool handlers with the LLM service.
    
    Args:
        llm_service: Pipecat LLM service instance (e.g., GroqLLMService)
    """
    async def tool_handler(params: FunctionCallParams):
        """Universal tool handler that routes to specific handlers."""
        result = await handle_tool_call(params)
        if result:
            # Use the result_callback to return result to LLM
            await params.result_callback(result)
    
    # Register each tool with the LLM service
    for tool_name in TOOL_HANDLERS.keys():
        llm_service.register_function(tool_name, tool_handler)
        logger.info(f"Registered tool: {tool_name}")
    
    logger.info(f"Registered {len(TOOL_HANDLERS)} tools with LLM service")
