import json
import random
import socket
import time
from datetime import datetime, timedelta, timezone
from uuid import uuid4

HOST = "127.0.0.1"
PORT = 5050
FORMAT = "utf-8"

FACILITY_TYPES = [
    "Acute Care Hospital",
    "Ambulatory Surgery Center",
    "Specialty Hospital",
    "Long-Term Care",
    "Outpatient Clinic",
]

DEPARTMENTS = [
    "Med-Surg",
    "Operating Room",
    "Emergency Department",
    "ICU",
    "Pharmacy",
    "Laboratory",
    "Sterile Processing",
    "Oncology",
    "Labor & Delivery",
]

ITEM_CATEGORIES = {
    "Surgical Supplies": ["Sutures & Staples", "Drapes & Gowns", "Needles & Syringes"],
    "Medications": ["IV Medications", "Oral Medications", "Controlled Substances"],
    "PPE": ["Masks", "Gloves", "Face Shields", "Gowns"],
    "Lab Consumables": ["Reagents", "Collection Tubes", "Test Kits"],
    "IV & Fluids": ["Saline Bags", "IV Sets", "Infusion Supplies"],
    "Wound Care": ["Bandages", "Dressings", "Gauze"],
    "Implants & Prosthetics": ["Orthopedic Implants", "Cardiac Implants"],
}

CRITICALITY_LEVELS = ["Critical", "High", "Medium", "Low"]
UNITS = ["Each", "Box", "Case", "Vial", "Bag", "Roll", "Kit", "Pair"]
DEMAND_TRENDS = ["Stable", "Increasing", "Decreasing"]


def rand_id(prefix: str, max_value: int, width: int = 4) -> str:
    return f"{prefix}{random.randint(1, max_value):0{width}d}"


def yes_no(probability_yes: float) -> str:
    return "Yes" if random.random() < probability_yes else "No"


def generate_event() -> dict:
    item_category = random.choice(list(ITEM_CATEGORIES.keys()))
    item_subcategory = random.choice(ITEM_CATEGORIES[item_category])
    criticality_level = random.choice(CRITICALITY_LEVELS)

    avg_90d = round(random.uniform(0.5, 500), 2)
    avg_30d = round(avg_90d * random.uniform(0.65, 1.45), 2)

    contracted_lead_time = random.randint(1, 45)
    actual_lead_time = round(contracted_lead_time * random.uniform(0.8, 2.0), 2)
    lead_variability = round(random.uniform(0, 20), 2)

    criticality_multiplier = {
        "Critical": 2.0,
        "High": 1.5,
        "Medium": 1.1,
        "Low": 0.8,
    }[criticality_level]

    safety_stock = int(
        avg_90d
        * (contracted_lead_time + 7)
        * criticality_multiplier
    )

    days_supply = round(random.uniform(0.5, 120), 2)
    current_stock = int(avg_30d * days_supply)

    stock_pct = round(
        (current_stock / safety_stock) * 100 if safety_stock else 0,
        2,
    )

    vendor_reliability = round(random.uniform(1.0, 5.0), 2)
    demand_trend = random.choices(
        DEMAND_TRENDS,
        weights=[60, 25, 15],
        k=1,
    )[0]

    recent_spike = yes_no(0.15)
    active_po = yes_no(0.53)
    sole_source = yes_no(0.12)
    substitution = yes_no(0.42)
    surge = yes_no(0.055)

    risk_score = 0

    if current_stock < safety_stock:
        risk_score += 35
    if days_supply < 3:
        risk_score += 25
    elif days_supply < 10:
        risk_score += 15
    if criticality_level in ["Critical", "High"]:
        risk_score += 15
    if demand_trend == "Increasing":
        risk_score += 10
    if recent_spike == "Yes":
        risk_score += 10
    if vendor_reliability <= 2.5:
        risk_score += 10
    if lead_variability > 10:
        risk_score += 8
    if sole_source == "Yes":
        risk_score += 8
    if substitution == "No":
        risk_score += 5
    if surge == "Yes":
        risk_score += 10

    stockout_event = 1 if risk_score >= 45 else 0

    snapshot_date = datetime.now(timezone.utc) - timedelta(days=random.randint(0, 365))

    return {
        "event_type": "MEDICAL_INVENTORY_STREAM",
        "record_id": f"SC{random.randint(1, 89088):08d}",
        "snapshot_date": snapshot_date.strftime("%Y-%m-%d"),
        "facility_id": rand_id("FAC", 200, 4),
        "facility_type": random.choice(FACILITY_TYPES),
        "department": random.choice(DEPARTMENTS),
        "item_id": rand_id("ITEM", 450, 4),
        "item_category": item_category,
        "item_subcategory": item_subcategory,
        "criticality_level": criticality_level,
        "unit_of_measure": random.choice(UNITS),
        "shelf_life_days": random.randint(30, 3650),
        "avg_daily_usage_last_30d": avg_30d,
        "avg_daily_usage_last_90d": avg_90d,
        "usage_cv_last_90d": round(random.uniform(0.02, 0.90), 2),
        "demand_trend": demand_trend,
        "seasonal_demand_factor": round(random.uniform(0.65, 1.60), 2),
        "recent_usage_spike": recent_spike,
        "current_stock_on_hand": current_stock,
        "safety_stock_level": safety_stock,
        "days_of_supply_on_hand": days_supply,
        "stock_as_pct_of_safety_level": stock_pct,
        "reorder_point_days": round(random.uniform(1.0, 60.0), 2),
        "days_until_next_scheduled_order": random.randint(1, 28),
        "primary_vendor_id": rand_id("VEND", 85, 3),
        "vendor_reliability_score": vendor_reliability,
        "contracted_lead_time_days": contracted_lead_time,
        "actual_avg_lead_time_last_6m": actual_lead_time,
        "lead_time_variability_days": lead_variability,
        "active_po_in_transit": active_po,
        "backorder_frequency_last_12m": random.randint(0, 10),
        "sole_source_item": sole_source,
        "substitution_available": substitution,
        "facility_census_pct": round(random.uniform(20.0, 100.0), 2),
        "pandemic_or_surge_flag": surge,
        "days_since_last_stockout": random.randint(1, 730),
        "stockout_event": stockout_event,
        "risk_score": risk_score,
        "stream_event_id": str(uuid4()),
        "stream_timestamp": datetime.now(timezone.utc).isoformat(),
    }


def start_server() -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)

    print(f"[LISTENING] Medical Inventory Stream Server running on {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        print(f"[CONNECTED] Client connected from {addr}")

        try:
            while True:
                payload = generate_event()
                message = json.dumps(payload) + "\n"
                conn.sendall(message.encode(FORMAT))

                print(
                    "[SENT]",
                    payload["record_id"],
                    payload["item_id"],
                    "risk:",
                    payload["risk_score"],
                    "stockout:",
                    payload["stockout_event"],
                )

                time.sleep(5)

        except (BrokenPipeError, ConnectionResetError):
            print("[DISCONNECTED] Client disconnected")

        except KeyboardInterrupt:
            print("[STOPPED] Server stopped")
            break

        except Exception as exc:
            print("[ERROR]", exc)

        finally:
            conn.close()


if __name__ == "__main__":
    start_server()