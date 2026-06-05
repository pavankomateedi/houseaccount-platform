"""Generate sample pricing data for development and testing."""

import csv
import random
import datetime
from pathlib import Path

CATEGORIES = [
    "Appliance Repair", "Auto", "Chimney", "Cleaning", "Electrical",
    "Exterior", "Flooring", "General Contractor", "Handyman", "HVAC",
    "Landscaping", "Moving", "Painting", "Pest Control", "Plumbing",
    "Pool", "Remodeling", "Roofing"
]

PRODUCTION_CATEGORIES = [
    "Electrical", "Exterior", "Handyman", "HVAC", "Cleaning",
    "Landscaping", "Pest Control", "Plumbing"
]

SUBTYPES = {
    "Plumbing": ["Water Heater Replacement", "Leak Repair", "Drain Cleaning", "Fixture Installation"],
    "Electrical": ["Panel Upgrade", "Outlet Installation", "Lighting", "Wiring"],
    "HVAC": ["AC Repair", "Furnace Maintenance", "Ductwork", "Thermostat"],
    "Painting": ["Interior", "Exterior", "Cabinet"],
    "Cleaning": ["Window Washing", "Carpet Cleaning", "General Cleaning"],
    "Pest Control": ["Bed Bugs", "Termites", "Rodents", "General"],
}

DESCRIPTIONS = {
    "Plumbing": [
        "Replace kitchen sink shutoff valve (you supply valve)",
        "Fix leaking bathroom faucet",
        "Install new water heater",
        "Clear clogged drain",
    ],
    "Electrical": [
        "Install new outlets in kitchen",
        "Repair faulty electrical panel",
        "Install ceiling fan",
        "Replace light switches",
    ],
    "HVAC": [
        "AC unit repair and maintenance",
        "Furnace service before winter",
        "Install new thermostat",
        "Clean ductwork",
    ],
    "Painting": [
        "Paint interior bedroom walls",
        "Exterior house painting",
        "Cabinet refinishing",
        "Trim painting",
    ],
    "Cleaning": [
        "Exterior window wash, 2-story, 20 windows",
        "Carpet cleaning entire house",
        "Deep clean kitchen and bathrooms",
        "Window washing service",
    ],
    "Pest Control": [
        "Bed bug heat treatment, 2BR apartment",
        "Termite inspection and treatment",
        "Rodent control and sealing",
        "General pest control service",
    ],
}

PRICE_RANGES = {
    "Plumbing": (100, 1500),
    "Electrical": (150, 2000),
    "HVAC": (200, 3000),
    "Painting": (300, 2500),
    "Cleaning": (100, 1000),
    "Pest Control": (300, 2000),
    "Handyman": (75, 500),
    "Landscaping": (200, 1500),
    "Exterior": (500, 3000),
    "General Contractor": (1000, 10000),
}

DEADLINES = [
    "As soon as possible",
    "Within 1-2 weeks",
    "Within 1 month",
    "I'm flexible"
]

def generate_sample_csv(num_rows=1432, num_labeled=411):
    """Generate sample pricing data CSV."""
    rows = []
    headers = [
        "job_id", "service_category", "service_subtype", "zip_code",
        "booking_month", "job_description", "estimate_lo", "estimate_hi",
        "original_estimate", "final_price", "deadline"
    ]

    zip_codes = [f"{random.randint(10000, 99999)}" for _ in range(1033)]

    for i in range(num_rows):
        category = random.choice(CATEGORIES)

        # Generate base price range
        if category in PRICE_RANGES:
            base_lo, base_hi = PRICE_RANGES[category]
        else:
            base_lo, base_hi = 200, 2000

        # Add some variance
        lo = base_lo + random.randint(-base_lo//4, base_lo//4)
        hi = base_hi + random.randint(-base_hi//4, base_hi//4)
        midpoint = (lo + hi) // 2

        # Generate final price for first num_labeled rows
        if i < num_labeled:
            # 70% of labeled rows have final prices
            if random.random() < 0.7:
                final_price = midpoint + random.randint(-int(midpoint*0.2), int(midpoint*0.2))
                final_price = max(lo, min(hi, final_price))  # Keep within range
            else:
                final_price = None
        else:
            final_price = None

        job_id = f"job_{i:06d}"
        subtype = random.choice(SUBTYPES.get(category, [category]))
        description = random.choice(DESCRIPTIONS.get(category, [category]))
        zip_code = random.choice(zip_codes)
        booking_month = f"2026-{random.randint(1, 4):02d}"
        deadline = random.choice(DEADLINES)

        rows.append({
            "job_id": job_id,
            "service_category": category,
            "service_subtype": subtype,
            "zip_code": zip_code,
            "booking_month": booking_month,
            "job_description": description,
            "estimate_lo": lo,
            "estimate_hi": hi,
            "original_estimate": midpoint,
            "final_price": final_price if final_price else "",
            "deadline": deadline,
        })

    # Write CSV
    output_path = Path(__file__).parent / "houseaccount_pricing_sample.csv"
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {num_rows} rows with {num_labeled} labeled")
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    generate_sample_csv()
