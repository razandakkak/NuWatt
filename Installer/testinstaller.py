import requests
import time

while True:
    url = "http://localhost:8000/get-installer-recommendations/"

    data = {
        "homeowners": [
            {
                "location": "Tripoli, LB",
                "num_panels": 8,
                "panel_power": 600,
                "battery_capacity": 12,
                "battery_efficiency": 0.8,
                "num_batteries": 2,
                "inverter_efficiency": 0.9,
                "initial_battery_level": 10  
            },
            {
                "location": "Beirut, LB",
                "num_panels": 6,
                "panel_power": 550,
                "battery_capacity": 10,
                "battery_efficiency": 0.75,
                "num_batteries": 3,
                "inverter_efficiency": 0.85,
                "initial_battery_level": 6  
            }
        ]
    }

    response = requests.post(url, json=data)
    recommendations = response.json().get("installer_recommendations", [])

    for rec in recommendations:
        location = rec["location"]
        timestamp = rec["recommendation"]["timestamp"]
        recommendation = rec["recommendation"]["recommendation"]

        print(f"🏠 {location} ({timestamp}):\n   ➤ {recommendation}\n")

    # Wait for 1 hour before running again
    time.sleep(36)
