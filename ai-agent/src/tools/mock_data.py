"""
Mock data for Battery Smart driver support queries.

This simulates database responses for:
- Swap history and invoices
- Battery Smart stations
- Subscription plans
- Leave information
- Support escalation

PRICING STRUCTURE:
- Base swap: ₹170
- Secondary swap: ₹70 (varies by zone/city)
- Free leaves: 4 days/month
- Leave penalty: ₹120 (if absent beyond limit, recovered at ₹60/swap)
- Service charge: ₹40/swap for vehicle services
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import random

# ===== PRICING CONSTANTS =====
PRICING = {
    "base_swap": 170,
    "secondary_swap": 70,  # Can vary by zone
    "free_leaves_per_month": 4,
    "leave_penalty": 120,
    "leave_penalty_recovery_per_swap": 60,
    "service_charge_per_swap": 40,
}

# Zone-wise secondary swap pricing
ZONE_PRICING = {
    "delhi_ncr": {"secondary_swap": 70, "base_swap": 170},
    "mumbai": {"secondary_swap": 75, "base_swap": 175},
    "bangalore": {"secondary_swap": 65, "base_swap": 165},
    "hyderabad": {"secondary_swap": 60, "base_swap": 160},
    "pune": {"secondary_swap": 68, "base_swap": 168},
}

# ===== MOCK DRIVER DATA =====
MOCK_DRIVERS = {
    "DRV001": {
        "driver_id": "DRV001",
        "name": "Rajesh Kumar",
        "phone": "+91-9876543210",
        "vehicle": {
            "type": "E-Rickshaw",
            "model": "Piaggio Ape E-City",
            "number": "DL 1E AB 1234",
            "battery_id": "BAT-2024-001"
        },
        "zone": "delhi_ncr",
        "subscription": {
            "plan": "unlimited",
            "valid_till": (datetime.now() + timedelta(days=45)).strftime("%Y-%m-%d"),
            "swaps_used_today": 3,
            "swaps_this_month": 78
        },
        "leaves": {
            "used_this_month": 2,
            "free_remaining": 2,
            "pending_penalty": 0
        },
        "status": "active"
    },
    "DRV002": {
        "driver_id": "DRV002",
        "name": "Amit Singh",
        "phone": "+91-9876543211",
        "vehicle": {
            "type": "E-Rickshaw",
            "model": "Mahindra Treo",
            "number": "UP 14 EB 5678",
            "battery_id": "BAT-2024-002"
        },
        "zone": "delhi_ncr",
        "subscription": {
            "plan": "daily",
            "valid_till": datetime.now().strftime("%Y-%m-%d"),
            "swaps_used_today": 5,
            "swaps_this_month": 112
        },
        "leaves": {
            "used_this_month": 5,
            "free_remaining": 0,
            "pending_penalty": 120  # 1 extra leave taken
        },
        "status": "active"
    }
}

# ===== MOCK SWAP HISTORY =====
MOCK_SWAP_HISTORY = {
    "DRV001": [
        {
            "swap_id": "SWP-20240115-001",
            "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
            "station_id": "STN-DEL-042",
            "station_name": "Battery Smart Lajpat Nagar",
            "battery_out": "BAT-2024-001",
            "battery_in": "BAT-2024-156",
            "charge_out": 15,
            "charge_in": 98,
            "swap_type": "primary",
            "amount": 170,
            "payment_status": "paid"
        },
        {
            "swap_id": "SWP-20240115-002",
            "timestamp": (datetime.now() - timedelta(hours=5)).isoformat(),
            "station_id": "STN-DEL-018",
            "station_name": "Battery Smart Nehru Place",
            "battery_out": "BAT-2024-156",
            "battery_in": "BAT-2024-001",
            "charge_out": 22,
            "charge_in": 95,
            "swap_type": "secondary",
            "amount": 70,
            "payment_status": "paid"
        },
        {
            "swap_id": "SWP-20240114-001",
            "timestamp": (datetime.now() - timedelta(days=1, hours=3)).isoformat(),
            "station_id": "STN-DEL-042",
            "station_name": "Battery Smart Lajpat Nagar",
            "battery_out": "BAT-2024-089",
            "battery_in": "BAT-2024-001",
            "charge_out": 18,
            "charge_in": 97,
            "swap_type": "primary",
            "amount": 170,
            "payment_status": "paid"
        },
    ],
    "DRV002": [
        {
            "swap_id": "SWP-20240115-003",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
            "station_id": "STN-DEL-005",
            "station_name": "Battery Smart Karol Bagh",
            "battery_out": "BAT-2024-002",
            "battery_in": "BAT-2024-078",
            "charge_out": 12,
            "charge_in": 99,
            "swap_type": "primary",
            "amount": 170,
            "service_charge": 40,  # Vehicle service was done
            "leave_penalty_recovery": 60,  # Recovering penalty
            "total_amount": 270,
            "payment_status": "paid"
        },
    ]
}

# ===== MOCK INVOICE DATA =====
def generate_invoice(driver_id: str, date_str: str = None) -> Dict[str, Any]:
    """Generate invoice breakdown for a driver."""
    driver = MOCK_DRIVERS.get(driver_id)
    if not driver:
        return None
    
    zone = driver.get("zone", "delhi_ncr")
    pricing = ZONE_PRICING.get(zone, PRICING)
    
    # Mock invoice data
    swaps = MOCK_SWAP_HISTORY.get(driver_id, [])
    primary_swaps = len([s for s in swaps if s.get("swap_type") == "primary"])
    secondary_swaps = len([s for s in swaps if s.get("swap_type") == "secondary"])
    
    invoice = {
        "driver_id": driver_id,
        "driver_name": driver["name"],
        "period": date_str or datetime.now().strftime("%B %Y"),
        "zone": zone,
        "breakdown": {
            "primary_swaps": {
                "count": primary_swaps,
                "rate": pricing["base_swap"],
                "total": primary_swaps * pricing["base_swap"]
            },
            "secondary_swaps": {
                "count": secondary_swaps,
                "rate": pricing.get("secondary_swap", 70),
                "total": secondary_swaps * pricing.get("secondary_swap", 70)
            },
            "service_charges": {
                "count": 1,  # Mock: 1 service done
                "rate": PRICING["service_charge_per_swap"],
                "total": PRICING["service_charge_per_swap"]
            },
            "leave_penalty": {
                "excess_leaves": driver["leaves"]["used_this_month"] - PRICING["free_leaves_per_month"] if driver["leaves"]["used_this_month"] > PRICING["free_leaves_per_month"] else 0,
                "rate": PRICING["leave_penalty"],
                "total": driver["leaves"].get("pending_penalty", 0)
            }
        },
        "total_amount": (
            primary_swaps * pricing["base_swap"] +
            secondary_swaps * pricing.get("secondary_swap", 70) +
            PRICING["service_charge_per_swap"] +
            driver["leaves"].get("pending_penalty", 0)
        )
    }
    return invoice

# ===== MOCK STATIONS DATA =====
MOCK_STATIONS = {
    "STN-DEL-042": {
        "station_id": "STN-DEL-042",
        "name": "Battery Smart Lajpat Nagar",
        "address": "Shop 15, Central Market, Lajpat Nagar II, New Delhi",
        "coordinates": {"lat": 28.5677, "lng": 77.2433},
        "zone": "delhi_ncr",
        "timings": "6:00 AM - 10:00 PM",
        "batteries_available": 12,
        "total_capacity": 20,
        "services": ["swap", "vehicle_service", "dsk_activation"],
        "contact": "+91-11-4567890",
        "is_dsk": True
    },
    "STN-DEL-018": {
        "station_id": "STN-DEL-018",
        "name": "Battery Smart Nehru Place",
        "address": "Block A, Nehru Place, New Delhi",
        "coordinates": {"lat": 28.5494, "lng": 77.2516},
        "zone": "delhi_ncr",
        "timings": "7:00 AM - 9:00 PM",
        "batteries_available": 8,
        "total_capacity": 15,
        "services": ["swap"],
        "contact": "+91-11-4567891",
        "is_dsk": False
    },
    "STN-DEL-005": {
        "station_id": "STN-DEL-005",
        "name": "Battery Smart Karol Bagh",
        "address": "Ajmal Khan Road, Karol Bagh, New Delhi",
        "coordinates": {"lat": 28.6519, "lng": 77.1909},
        "zone": "delhi_ncr",
        "timings": "6:00 AM - 11:00 PM",
        "batteries_available": 15,
        "total_capacity": 25,
        "services": ["swap", "vehicle_service", "dsk_activation", "new_subscription"],
        "contact": "+91-11-4567892",
        "is_dsk": True
    },
    "STN-DEL-023": {
        "station_id": "STN-DEL-023",
        "name": "Battery Smart Connaught Place",
        "address": "Block M, Connaught Place, New Delhi",
        "coordinates": {"lat": 28.6315, "lng": 77.2167},
        "zone": "delhi_ncr",
        "timings": "24/7",
        "batteries_available": 22,
        "total_capacity": 30,
        "services": ["swap", "vehicle_service", "dsk_activation", "new_subscription"],
        "contact": "+91-11-4567893",
        "is_dsk": True
    }
}

# ===== SUBSCRIPTION PLANS =====
SUBSCRIPTION_PLANS = {
    "daily": {
        "name": "Daily Plan",
        "description": "Pay per day, unlimited swaps",
        "price": 199,
        "validity_days": 1,
        "features": ["Unlimited swaps", "All stations access", "No commitment"]
    },
    "weekly": {
        "name": "Weekly Plan",
        "description": "7 days unlimited swaps at discounted rate",
        "price": 999,
        "validity_days": 7,
        "features": ["Unlimited swaps", "All stations access", "15% savings vs daily"]
    },
    "monthly": {
        "name": "Monthly Plan",
        "description": "30 days unlimited swaps, best value",
        "price": 2999,
        "validity_days": 30,
        "features": ["Unlimited swaps", "All stations access", "Priority support", "25% savings"]
    },
    "unlimited": {
        "name": "Unlimited Plan",
        "description": "60 days mega saver plan",
        "price": 5499,
        "validity_days": 60,
        "features": ["Unlimited swaps", "All stations access", "Priority support", "Vehicle servicing discount", "35% savings"]
    }
}

# ===== ESCALATION REASONS =====
ESCALATION_REASONS = [
    "battery_issue",
    "station_problem",
    "payment_dispute",
    "subscription_issue",
    "vehicle_breakdown",
    "safety_concern",
    "other_urgent"
]


# ===== HELPER FUNCTIONS =====

def get_swap_history(driver_id: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Get recent swap history for a driver."""
    swaps = MOCK_SWAP_HISTORY.get(driver_id, [])
    return swaps[:limit]


def get_invoice_explanation(driver_id: str) -> Dict[str, Any]:
    """Get detailed invoice breakdown with explanations."""
    return generate_invoice(driver_id)


def find_nearest_stations(lat: float, lng: float, limit: int = 5, dsk_only: bool = False) -> List[Dict[str, Any]]:
    """Find nearest Battery Smart stations."""
    stations = list(MOCK_STATIONS.values())
    
    if dsk_only:
        stations = [s for s in stations if s.get("is_dsk", False)]
    
    # Sort by mock distance (in real app, would calculate from coordinates)
    for station in stations:
        # Simple distance approximation
        station["distance_km"] = round(
            abs(station["coordinates"]["lat"] - lat) * 111 +
            abs(station["coordinates"]["lng"] - lng) * 85,
            1
        )
    
    stations.sort(key=lambda x: x["distance_km"])
    return stations[:limit]


def get_station_availability(station_id: str) -> Dict[str, Any]:
    """Get real-time battery availability at a station."""
    station = MOCK_STATIONS.get(station_id)
    if not station:
        return None
    
    return {
        "station_id": station_id,
        "name": station["name"],
        "batteries_available": station["batteries_available"],
        "total_capacity": station["total_capacity"],
        "availability_percent": round(station["batteries_available"] / station["total_capacity"] * 100),
        "status": "high" if station["batteries_available"] > 10 else "medium" if station["batteries_available"] > 5 else "low",
        "estimated_wait": "No wait" if station["batteries_available"] > 5 else f"{random.randint(5, 15)} minutes"
    }


def get_driver_subscription(driver_id: str) -> Dict[str, Any]:
    """Get driver's current subscription details."""
    driver = MOCK_DRIVERS.get(driver_id)
    if not driver:
        return None
    
    sub = driver.get("subscription", {})
    plan_details = SUBSCRIPTION_PLANS.get(sub.get("plan", "daily"), {})
    
    valid_till = datetime.strptime(sub["valid_till"], "%Y-%m-%d")
    days_remaining = (valid_till - datetime.now()).days
    
    return {
        "driver_id": driver_id,
        "driver_name": driver["name"],
        "current_plan": sub.get("plan"),
        "plan_name": plan_details.get("name"),
        "valid_till": sub["valid_till"],
        "days_remaining": max(0, days_remaining),
        "is_expired": days_remaining < 0,
        "swaps_today": sub.get("swaps_used_today", 0),
        "swaps_this_month": sub.get("swaps_this_month", 0),
        "renewal_options": list(SUBSCRIPTION_PLANS.keys()),
        "zone": driver.get("zone", "delhi_ncr")
    }


def get_leave_info(driver_id: str) -> Dict[str, Any]:
    """Get driver's leave information."""
    driver = MOCK_DRIVERS.get(driver_id)
    if not driver:
        return None
    
    leaves = driver.get("leaves", {})
    
    return {
        "driver_id": driver_id,
        "driver_name": driver["name"],
        "free_leaves_per_month": PRICING["free_leaves_per_month"],
        "leaves_used": leaves.get("used_this_month", 0),
        "leaves_remaining": leaves.get("free_remaining", PRICING["free_leaves_per_month"]),
        "pending_penalty": leaves.get("pending_penalty", 0),
        "penalty_rate": PRICING["leave_penalty"],
        "recovery_rate_per_swap": PRICING["leave_penalty_recovery_per_swap"],
        "swaps_to_clear_penalty": (
            leaves.get("pending_penalty", 0) // PRICING["leave_penalty_recovery_per_swap"]
            if leaves.get("pending_penalty", 0) > 0 else 0
        )
    }


def find_nearest_dsk(lat: float, lng: float) -> Dict[str, Any]:
    """Find nearest DSK (Driver Service Kendra) for subscription activation."""
    dsk_stations = find_nearest_stations(lat, lng, limit=3, dsk_only=True)
    
    if dsk_stations:
        nearest = dsk_stations[0]
        return {
            "found": True,
            "station": nearest,
            "message": f"Nearest DSK is {nearest['name']}, {nearest['distance_km']} km away. Visit for subscription activation or leave management."
        }
    
    return {
        "found": False,
        "message": "No DSK found nearby. Please contact support for assistance."
    }


def create_support_ticket(reason: str, description: str) -> Dict[str, Any]:
    """Create a support escalation ticket."""
    ticket_id = f"BST{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    high_priority_reasons = ["battery_issue", "safety_concern", "vehicle_breakdown"]
    
    return {
        "ticket_id": ticket_id,
        "reason": reason,
        "description": description,
        "status": "open",
        "priority": "high" if reason in high_priority_reasons else "normal",
        "created_at": datetime.now().isoformat(),
        "estimated_response": "A support agent will contact you within 10 minutes" if reason in high_priority_reasons else "Our team will respond within 1 hour"
    }
