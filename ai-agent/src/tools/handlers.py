"""
Tool handlers for Battery Smart driver support LLM function calling.

Each handler processes a specific tool call and returns
formatted results for the LLM to respond with.

Tools:
1. get_swap_history - Swap history + invoice breakdown
2. find_nearest_station - Nearest stations + battery availability
3. get_subscription_info - Subscription status + renewal options
4. get_leave_info - Leave info + DSK location
5. escalate_to_support - Human agent escalation
"""
from typing import Any, Dict, Optional
from loguru import logger

from pipecat.services.llm_service import FunctionCallParams

from src.tools.mock_data import (
    get_swap_history,
    get_invoice_explanation,
    find_nearest_stations,
    get_station_availability,
    get_driver_subscription,
    get_leave_info,
    find_nearest_dsk,
    create_support_ticket,
    SUBSCRIPTION_PLANS,
    PRICING,
)

# Default driver ID for testing (in production, would come from call context)
DEFAULT_DRIVER_ID = "DRV001"
DEFAULT_LAT = 28.5677  # Delhi
DEFAULT_LNG = 77.2433


async def handle_get_swap_history(params: FunctionCallParams) -> str:
    """
    Handle swap history and invoice lookup.
    
    Returns recent swaps with optional invoice breakdown explaining:
    - Primary swap: ₹170
    - Secondary swap: ₹70
    - Service charge: ₹40/swap
    - Leave penalty recovery: ₹60/swap
    """
    args = params.arguments
    driver_id = args.get("driver_id", DEFAULT_DRIVER_ID)
    include_invoice = args.get("include_invoice", True)
    limit = min(args.get("limit", 5), 10)
    
    logger.info(f"Tool call: get_swap_history(driver_id={driver_id}, limit={limit})")
    
    # Get swap history
    swaps = get_swap_history(driver_id, limit)
    
    if not swaps:
        return "I don't see any swap history for your account. Have you completed any battery swaps recently?"
    
    # Voice-friendly response for recent swaps
    if len(swaps) == 1:
        swap = swaps[0]
        station_name = swap['station_name'].replace("Battery Smart ", "")
        response = f"Your last swap was at {station_name}. "
        response += f"You swapped a {swap.get('charge_out', 0)} percent battery for a {swap.get('charge_in', 0)} percent charged one. "
        response += f"It was a {swap.get('swap_type', 'primary')} swap costing {swap.get('amount', 0)} rupees. "
        
        if swap.get("service_charge"):
            response += f"There was also a service charge of {swap['service_charge']} rupees. "
        if swap.get("leave_penalty_recovery"):
            response += f"And {swap['leave_penalty_recovery']} rupees was recovered towards your leave penalty. "
        
        return response
    
    # Multiple swaps - summarize
    total_swaps = len(swaps)
    primary_count = len([s for s in swaps if s.get("swap_type") == "primary"])
    secondary_count = total_swaps - primary_count
    total_amount = sum(s.get("amount", 0) for s in swaps)
    
    response = f"You've done {total_swaps} swaps recently. "
    
    if primary_count > 0:
        response += f"{primary_count} were primary swaps at 170 rupees each. "
    if secondary_count > 0:
        response += f"{secondary_count} were secondary swaps at 70 rupees each. "
    
    # Last swap details
    last_swap = swaps[0]
    station_name = last_swap['station_name'].replace("Battery Smart ", "")
    response += f"Your most recent swap was at {station_name}. "
    
    # Invoice breakdown if requested
    if include_invoice:
        invoice = get_invoice_explanation(driver_id)
        if invoice:
            bd = invoice["breakdown"]
            response += f"Your total bill comes to {invoice['total_amount']} rupees. "
            
            if bd['service_charges']['total'] > 0:
                response += f"This includes {bd['service_charges']['total']} rupees in service charges. "
            
            if bd['leave_penalty']['total'] > 0:
                response += f"You also have a leave penalty of {bd['leave_penalty']['total']} rupees being recovered at 60 rupees per swap. "
    
    return response


async def handle_find_nearest_station(params: FunctionCallParams) -> str:
    """
    Handle finding nearest Battery Smart stations.
    
    Returns stations with real-time battery availability.
    Can filter for DSK stations only (for subscription/leave management).
    """
    args = params.arguments
    lat = args.get("latitude", DEFAULT_LAT)
    lng = args.get("longitude", DEFAULT_LNG)
    dsk_only = args.get("dsk_only", False)
    limit = min(args.get("limit", 3), 5)
    
    logger.info(f"Tool call: find_nearest_station(lat={lat}, lng={lng}, dsk_only={dsk_only})")
    
    stations = find_nearest_stations(lat, lng, limit, dsk_only)
    
    if not stations:
        if dsk_only:
            return "I couldn't find any Driver Service Kendra nearby. Please contact our support team for subscription activation or leave management."
        return "I couldn't find any Battery Smart stations nearby. Could you share your current location?"
    
    # Voice-friendly response
    if len(stations) == 1:
        station = stations[0]
        availability = get_station_availability(station["station_id"])
        
        response = f"The nearest station is {station['name']}, located at {station['address']}. "
        response += f"It's about {station['distance_km']} kilometers away. "
        response += f"The station is open from {station['timings']}. "
        
        if availability:
            response += f"Currently, {availability['batteries_available']} batteries are available. "
            if availability['estimated_wait'] != "No wait":
                response += f"Expected wait time is {availability['estimated_wait']}. "
        
        if station.get("is_dsk"):
            response += "This is a DSK station, so you can also do subscription activation and leave management here. "
        
        response += f"You can call them at {_format_phone_for_speech(station['contact'])}."
        return response
    
    # Multiple stations
    response = f"I found {len(stations)} stations near you. "
    
    # Describe the nearest one in detail
    nearest = stations[0]
    availability = get_station_availability(nearest["station_id"])
    
    response += f"The nearest one is {nearest['name']}, just {nearest['distance_km']} kilometers away at {nearest['address']}. "
    
    if availability:
        if availability['batteries_available'] > 10:
            response += "Good news, they have plenty of batteries available right now. "
        elif availability['batteries_available'] > 5:
            response += f"They have {availability['batteries_available']} batteries available. "
        else:
            response += f"They're running low with only {availability['batteries_available']} batteries, so you might want to hurry. "
    
    if nearest.get("is_dsk"):
        response += "This is also a DSK station. "
    
    # Briefly mention others
    if len(stations) > 1:
        other_names = [s['name'].replace("Battery Smart ", "") for s in stations[1:3]]
        response += f"Other nearby options include {' and '.join(other_names)}. "
    
    response += "Would you like more details about any of these stations?"
    
    return response


def _format_phone_for_speech(phone: str) -> str:
    """Format phone number to be spoken naturally."""
    # Remove special characters and format for speech
    digits = ''.join(filter(str.isdigit, phone))
    if len(digits) == 11 and digits.startswith('91'):
        digits = digits[2:]  # Remove country code
    if len(digits) == 10:
        # Format as: 98765 43210 (spoken as groups)
        return f"{digits[:5]} {digits[5:]}"
    return phone.replace('-', ' ').replace('+91', '')


async def handle_get_subscription_info(params: FunctionCallParams) -> str:
    """
    Handle subscription information lookup.
    
    Returns current plan, validity, and available renewal options.
    """
    args = params.arguments
    driver_id = args.get("driver_id", DEFAULT_DRIVER_ID)
    show_all_plans = args.get("show_all_plans", True)
    
    logger.info(f"Tool call: get_subscription_info(driver_id={driver_id})")
    
    sub_info = get_driver_subscription(driver_id)
    
    if not sub_info:
        return "I couldn't find your subscription information. Please visit a DSK to activate your subscription."
    
    # Voice-friendly response
    response = f"Okay {sub_info['driver_name']}, let me tell you about your subscription. "
    response += f"You're on the {sub_info['plan_name']}. "
    
    if sub_info['is_expired']:
        response += "I see that your subscription has expired. You'll need to renew it to continue swapping. "
    else:
        if sub_info['days_remaining'] <= 3:
            response += f"Heads up, your plan expires in just {sub_info['days_remaining']} days. You might want to renew soon. "
        else:
            response += f"Your plan is valid for {sub_info['days_remaining']} more days. "
    
    response += f"So far this month, you've done {sub_info['swaps_this_month']} swaps. "
    
    # Show renewal options if requested
    if show_all_plans:
        response += "For renewal, we have several plans. "
        response += "The Daily Plan costs 199 rupees. "
        response += "The Weekly Plan is 999 rupees for 7 days. "
        response += "The Monthly Plan is 2999 rupees for 30 days, which gives you 25 percent savings. "
        response += "And our best value is the Unlimited Plan at 5499 rupees for 60 days. "
        response += "You can renew at any DSK station."
    
    return response


async def handle_get_leave_info(params: FunctionCallParams) -> str:
    """
    Handle leave information lookup.
    
    Returns:
    - Free leaves (4 days/month)
    - Used leaves
    - Pending penalty (₹120 per excess leave)
    - Recovery status (₹60/swap)
    - Nearest DSK for activation
    """
    args = params.arguments
    driver_id = args.get("driver_id", DEFAULT_DRIVER_ID)
    find_dsk = args.get("find_nearest_dsk", True)
    lat = args.get("latitude", DEFAULT_LAT)
    lng = args.get("longitude", DEFAULT_LNG)
    
    logger.info(f"Tool call: get_leave_info(driver_id={driver_id})")
    
    leave_info = get_leave_info(driver_id)
    
    if not leave_info:
        return "I couldn't find your leave information. Please contact support or visit a DSK."
    
    # Voice-friendly response
    response = f"Here's your leave status, {leave_info['driver_name']}. "
    response += f"You get {leave_info['free_leaves_per_month']} free leave days every month. "
    response += f"This month, you've used {leave_info['leaves_used']} days. "
    
    if leave_info['leaves_remaining'] > 0:
        response += f"You still have {leave_info['leaves_remaining']} free days remaining. "
    else:
        response += "You've used up all your free leaves for this month. "
    
    # Penalty information
    if leave_info['pending_penalty'] > 0:
        response += f"I see you have a pending penalty of {leave_info['pending_penalty']} rupees for extra leaves. "
        response += f"Don't worry, we're recovering this at {leave_info['recovery_rate_per_swap']} rupees per swap. "
        response += f"You need about {leave_info['swaps_to_clear_penalty']} more swaps to clear it. "
    else:
        response += "Good news, you don't have any pending penalties! "
    
    # Leave policy reminder
    response += f"Just a reminder, if you take more than {PRICING['free_leaves_per_month']} leaves, there's a penalty of {PRICING['leave_penalty']} rupees per extra day. "
    
    # Find nearest DSK
    if find_dsk:
        dsk_info = find_nearest_dsk(lat, lng)
        if dsk_info["found"]:
            station_name = dsk_info['station']['name'].replace("Battery Smart ", "")
            response += f"If you need to apply for leave, the nearest DSK is at {station_name}, about {dsk_info['station']['distance_km']} kilometers away."
    
    return response


async def handle_escalate_to_support(params: FunctionCallParams) -> str:
    """Handle escalate_to_support tool call for Battery Smart."""
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
        
        # Map Battery Smart escalation reasons to triggers
        trigger_map = {
            "battery_issue": HandoffTrigger.SAFETY_EMERGENCY,
            "station_problem": HandoffTrigger.EXPLICIT_REQUEST,
            "payment_dispute": HandoffTrigger.FRAUD_DETECTION,
            "subscription_issue": HandoffTrigger.EXPLICIT_REQUEST,
            "vehicle_breakdown": HandoffTrigger.SAFETY_EMERGENCY,
            "safety_concern": HandoffTrigger.SAFETY_EMERGENCY,
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
        "I'm connecting you with a Battery Smart support agent right away. "
        "I've created a support ticket for you. "
        "A human agent will join this call shortly. Please stay on the line."
    )


# Tool handler registry for Battery Smart
TOOL_HANDLERS = {
    "get_swap_history": handle_get_swap_history,
    "find_nearest_station": handle_find_nearest_station,
    "get_subscription_info": handle_get_subscription_info,
    "get_leave_info": handle_get_leave_info,
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
    Register all Battery Smart tool handlers with the LLM service.
    
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
    
    logger.info(f"Registered {len(TOOL_HANDLERS)} Battery Smart tools with LLM service")
