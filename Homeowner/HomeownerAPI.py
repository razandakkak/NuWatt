from fastapi import FastAPI
from pydantic import BaseModel
import requests
from datetime import datetime, timedelta
import random

app = FastAPI()

# Weather API parameters
API_KEY = "_"
PANEL_EFFICIENCY = 0.8  # 80%
AC_VOLTAGE = 220  # Volts
NIGHT_HOURS = 7  # Hours considered night time

# Request model
class UserInput(BaseModel):
    location: str
    num_panels: int
    panel_power: float
    battery_capacity: float
    battery_efficiency: float
    num_batteries: int
    inverter_efficiency: float
    initial_battery_level: float

def fetch_weather_forecast(location, api_key):
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={location}&units=metric&appid={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return [{
            "timestamp": item['dt_txt'],
            "temperature": item['main']['temp'],
            "cloud_cover": item['clouds']['all']
        } for item in data['list']]
    return None

def estimate_irradiance(cloud_cover):
    return max(1000 - (cloud_cover * 5), 0)

def calculate_max_ac_current_day(irradiance, num_panels, panel_power, inverter_efficiency):
    total_dc_power = irradiance * num_panels * panel_power * PANEL_EFFICIENCY / 1000
    return max((total_dc_power * inverter_efficiency) / AC_VOLTAGE, 0)

def calculate_max_ac_current_night(battery_level, battery_efficiency, inverter_efficiency):
    usable_battery_energy = battery_level * battery_efficiency
    total_ac_energy = usable_battery_energy * inverter_efficiency
    return max((total_ac_energy * 1000) / (AC_VOLTAGE * NIGHT_HOURS), 0)

RECOMMENDATION_SETS = {
    "high_solar": [
        "Great solar conditions! Increase energy consumption while charging the battery.",
        "Optimal sunlight detected! Run high-energy appliances freely."
    ],
    "moderate_solar": [
        "Moderate solar conditions. Balance energy use and battery charging.",
        "Decent sunlight available. Use appliances wisely."
    ],
    "low_solar": [
        "Low solar conditions. Limit energy consumption to preserve battery.",
        "Cloudy conditions detected. Reduce usage to avoid battery drain."
    ],
    "night": [
        "Nighttime detected. Limit usage to essential appliances.",
        "It's nighttime. Ensure power efficiency by limiting unnecessary usage."
    ]
}

@app.post("/get-recommendations/")
def get_recommendations(user_input: UserInput):
    forecast = fetch_weather_forecast(user_input.location, API_KEY)
    if not forecast:
        return {"error": "Could not fetch weather data"}
    
    next_hour = (datetime.now() + timedelta(hours=1)).hour  # ✅ Define next_hour

    next_available_forecast = min(forecast, key=lambda x: abs(datetime.fromisoformat(x['timestamp']).hour - next_hour))
    next_hour_forecast = [next_available_forecast]  # Ensure it's always a list

    if not next_hour_forecast:
        return {"error": "No forecast data available for the next hour"}

    recommendations = []
    for entry in next_hour_forecast:
        timestamp, cloud_cover = entry["timestamp"], entry["cloud_cover"]
        irradiance = estimate_irradiance(cloud_cover)
        hour = int(timestamp[11:13])
        
        if 20 <= hour <= 23 or hour <= 6:
            max_ac_current = calculate_max_ac_current_night(
                user_input.initial_battery_level, user_input.battery_efficiency, user_input.inverter_efficiency
            )
            recommendation = random.choice(RECOMMENDATION_SETS["night"])
        else:
            max_ac_current = calculate_max_ac_current_day(
                irradiance, user_input.num_panels, user_input.panel_power, user_input.inverter_efficiency
            )
            condition = "high_solar" if irradiance > 800 else "low_solar" if irradiance < 400 else "moderate_solar"
            recommendation = random.choice(RECOMMENDATION_SETS[condition])
        
        recommendations.append({
            "timestamp": timestamp,
            "irradiance": irradiance,
            "max_ac_current": max_ac_current,
            "recommendation": recommendation
        })

    return {"recommendations": recommendations}
