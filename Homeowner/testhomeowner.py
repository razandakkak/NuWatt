import requests
import schedule
import time

url = "http://localhost:8000/get-recommendations/"
data = {
    "location": "Tripoli, LB",
    "num_panels": 6,
    "panel_power": 550,
    "battery_capacity": 10,
    "battery_efficiency": 0.6,
    "num_batteries": 4,
    "inverter_efficiency": 0.85,
    "initial_battery_level": 6  
}

def fetch_recommendation():
    response = requests.post(url, json=data)
    print(response.json())

# Schedule the request every hour
schedule.every(10).seconds.do(fetch_recommendation)

while True:
    schedule.run_pending()
    time.sleep(1)
