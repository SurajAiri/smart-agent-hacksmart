"""
Mock data for driver support queries.

This simulates database responses for:
- Trip information
- Driver details
- FAQs
- Support escalation
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

# Mock Driver Data
MOCK_DRIVERS = {
    "DRV001": {
        "driver_id": "DRV001",
        "name": "Rajesh Kumar",
        "phone": "+91-9876543210",
        "vehicle": {
            "type": "Sedan",
            "model": "Maruti Swift Dzire",
            "number": "MH 12 AB 1234",
            "color": "White"
        },
        "rating": 4.8,
        "total_trips": 1523,
        "status": "active"
    },
    "DRV002": {
        "driver_id": "DRV002", 
        "name": "Amit Singh",
        "phone": "+91-9876543211",
        "vehicle": {
            "type": "Hatchback",
            "model": "Hyundai i20",
            "number": "DL 01 CD 5678",
            "color": "Silver"
        },
        "rating": 4.6,
        "total_trips": 892,
        "status": "active"
    }
}

# Mock Trip Data
MOCK_TRIPS = {
    "TRIP001": {
        "trip_id": "TRIP001",
        "driver_id": "DRV001",
        "pickup": {
            "address": "Andheri West Metro Station, Mumbai",
            "lat": 19.1196,
            "lng": 72.8467
        },
        "dropoff": {
            "address": "Bandra Kurla Complex, Mumbai",
            "lat": 19.0653,
            "lng": 72.8694
        },
        "status": "in_progress",
        "estimated_arrival": (datetime.now() + timedelta(minutes=12)).isoformat(),
        "fare_estimate": 245.00,
        "distance_km": 8.5,
        "duration_mins": 25,
        "payment_method": "Cash",
        "booked_at": (datetime.now() - timedelta(minutes=10)).isoformat()
    },
    "TRIP002": {
        "trip_id": "TRIP002",
        "driver_id": "DRV002",
        "pickup": {
            "address": "Connaught Place, Delhi",
            "lat": 28.6315,
            "lng": 77.2167
        },
        "dropoff": {
            "address": "Indira Gandhi Airport, Delhi",
            "lat": 28.5562,
            "lng": 77.1000
        },
        "status": "completed",
        "actual_fare": 520.00,
        "distance_km": 15.2,
        "duration_mins": 45,
        "payment_method": "UPI",
        "completed_at": (datetime.now() - timedelta(hours=2)).isoformat()
    }
}

# Mock FAQ Data
MOCK_FAQS = {
    "pricing": {
        "question": "How is fare calculated?",
        "answer": "Fare is calculated based on distance traveled, time taken, and current demand. Base fare starts at ₹30, plus ₹12 per kilometer and ₹2 per minute. Peak hours may have surge pricing of 1.2x to 1.5x.",
        "category": "pricing"
    },
    "cancellation": {
        "question": "What is the cancellation policy?",
        "answer": "You can cancel a ride for free within 2 minutes of booking. After that, a cancellation fee of ₹50 applies. If the driver is already at pickup location, the fee is ₹100. Repeated cancellations may affect your account.",
        "category": "policy"
    },
    "payment": {
        "question": "What payment methods are accepted?",
        "answer": "We accept Cash, UPI (GPay, PhonePe, Paytm), Credit/Debit Cards, and our Wallet. For safety, we recommend digital payments. Wallet offers 5% cashback on rides.",
        "category": "payment"
    },
    "safety": {
        "question": "How do you ensure passenger safety?",
        "answer": "All drivers undergo background verification. We have SOS button for emergencies, live ride tracking shared with contacts, 24/7 support, and insurance coverage for all trips. OTP verification ensures you board the right vehicle.",
        "category": "safety"
    },
    "refund": {
        "question": "How do I get a refund?",
        "answer": "Refunds for cancelled rides are processed within 24-48 hours to your original payment method. For fare disputes, raise a complaint in app under Trip History > Report Issue. Our team reviews within 24 hours.",
        "category": "payment"
    },
    "lost_item": {
        "question": "I left something in the car. What should I do?",
        "answer": "Go to Trip History, select the trip, and tap 'Lost Item'. We'll connect you with the driver. If driver has found the item, you can arrange pickup. A convenience fee of ₹100 may apply for item return trips.",
        "category": "support"
    },
    "driver_earnings": {
        "question": "How do driver earnings work?",
        "answer": "Drivers earn 80% of the trip fare. Payments are settled weekly to registered bank accounts. Incentives include peak hour bonuses (₹50-200 per trip), daily targets (₹500 bonus for 10+ trips), and weekly leaderboard prizes.",
        "category": "driver"
    },
    "vehicle_requirements": {
        "question": "What are the vehicle requirements for drivers?",
        "answer": "Vehicle must be less than 8 years old, have valid registration and insurance, pass safety inspection, and have commercial permit. AC must be functional. We conduct periodic vehicle audits.",
        "category": "driver"
    }
}

# Support escalation reasons
ESCALATION_REASONS = [
    "accident_emergency",
    "harassment",
    "payment_fraud",
    "account_blocked",
    "legal_issue",
    "other_urgent"
]


def get_current_trip(driver_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get current active trip for a driver."""
    for trip_id, trip in MOCK_TRIPS.items():
        if trip["status"] == "in_progress":
            if driver_id is None or trip["driver_id"] == driver_id:
                # Add driver info
                driver = MOCK_DRIVERS.get(trip["driver_id"], {})
                return {**trip, "driver": driver}
    return None


def get_trip_by_id(trip_id: str) -> Optional[Dict[str, Any]]:
    """Get trip details by ID."""
    trip = MOCK_TRIPS.get(trip_id)
    if trip:
        driver = MOCK_DRIVERS.get(trip["driver_id"], {})
        return {**trip, "driver": driver}
    return None


def get_driver_info(driver_id: str) -> Optional[Dict[str, Any]]:
    """Get driver information."""
    return MOCK_DRIVERS.get(driver_id)


def search_faqs(query: str) -> List[Dict[str, Any]]:
    """Search FAQs by keyword matching."""
    query_lower = query.lower()
    results = []
    
    # Keyword mapping for common queries
    keyword_map = {
        "price": ["pricing"],
        "cost": ["pricing"],
        "fare": ["pricing"],
        "charge": ["pricing"],
        "cancel": ["cancellation"],
        "payment": ["payment"],
        "pay": ["payment"],
        "upi": ["payment"],
        "cash": ["payment"],
        "safe": ["safety"],
        "emergency": ["safety"],
        "sos": ["safety"],
        "refund": ["refund"],
        "money back": ["refund"],
        "lost": ["lost_item"],
        "forgot": ["lost_item"],
        "left": ["lost_item"],
        "earning": ["driver_earnings"],
        "income": ["driver_earnings"],
        "salary": ["driver_earnings"],
        "vehicle": ["vehicle_requirements"],
        "car": ["vehicle_requirements"],
        "requirement": ["vehicle_requirements"]
    }
    
    matched_keys = set()
    for keyword, faq_keys in keyword_map.items():
        if keyword in query_lower:
            matched_keys.update(faq_keys)
    
    # If no keyword match, do basic text search
    if not matched_keys:
        for key, faq in MOCK_FAQS.items():
            if query_lower in faq["question"].lower() or query_lower in faq["answer"].lower():
                matched_keys.add(key)
    
    for key in matched_keys:
        if key in MOCK_FAQS:
            results.append(MOCK_FAQS[key])
    
    return results


def get_trip_history(limit: int = 5) -> List[Dict[str, Any]]:
    """Get recent trip history."""
    trips = []
    for trip_id, trip in MOCK_TRIPS.items():
        driver = MOCK_DRIVERS.get(trip["driver_id"], {})
        trips.append({**trip, "driver": driver})
    return trips[:limit]


def create_support_ticket(reason: str, description: str) -> Dict[str, Any]:
    """Create a support escalation ticket."""
    ticket_id = f"TKT{datetime.now().strftime('%Y%m%d%H%M%S')}"
    return {
        "ticket_id": ticket_id,
        "reason": reason,
        "description": description,
        "status": "open",
        "priority": "high" if reason in ["accident_emergency", "harassment"] else "normal",
        "created_at": datetime.now().isoformat(),
        "estimated_response": "A support agent will contact you within 15 minutes" if reason in ["accident_emergency", "harassment"] else "Our team will respond within 2 hours"
    }
