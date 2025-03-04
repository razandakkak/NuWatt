from fastapi import FastAPI
from pydantic import BaseModel
import requests
from datetime import datetime, timedelta
import random

app = FastAPI()

# Weather API parameters
API_KEY = "fb8fde2fa1c888193cc4ce0e6722e699"
AC_VOLTAGE = 220  # Volts
PANEL_EFFICIENCY = 0.8  # 80%
NIGHT_HOURS = 7  # Nighttime duration

# **Request Models**
class Homeowner(BaseModel):
    location: str
    num_panels: int
    panel_power: float
    battery_capacity: float
    battery_efficiency: float
    num_batteries: int
    inverter_efficiency: float
    initial_battery_level: float

class InstallerRequest(BaseModel):
    homeowners: list[Homeowner]  # List of homeowners sent by the installer

# **Fetch Weather Data**
def fetch_weather_forecast(location):
    url = f"https://api.openweathermap.org/data/2.5/forecast?q={location}&units=metric&appid={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return [
            {
                "timestamp": item['dt_txt'],
                "temperature": item['main']['temp'],
                "cloud_cover": item['clouds']['all']
            } for item in data['list']
        ]
    return None  # Return None if weather data fetch fails

# **Filter Tomorrow's Forecast**
def filter_tomorrow_forecast(forecast):
    tomorrow_date = (datetime.now() + timedelta(days=1)).date()
    return [entry for entry in forecast if datetime.fromisoformat(entry['timestamp']).date() == tomorrow_date]

# **Solar Calculations**
def estimate_irradiance(cloud_cover):
    return max(1000 - (cloud_cover * 5), 0)

def calculate_max_ac_current_day(irradiance, num_panels, panel_power, inverter_efficiency):
    total_dc_power = irradiance * num_panels * panel_power * PANEL_EFFICIENCY / 1000
    return max((total_dc_power * inverter_efficiency) / AC_VOLTAGE, 0)

def calculate_max_ac_current_night(battery_level, battery_efficiency, inverter_efficiency):
    usable_battery_energy = battery_level * battery_efficiency
    total_ac_energy = usable_battery_energy * inverter_efficiency
    return max((total_ac_energy * 1000) / (AC_VOLTAGE * NIGHT_HOURS), 0)

# **Installer Recommendations**
INSTALLER_RECOMMENDATIONS = {
    "high_solar": [
        "Advise the homeowner to utilize excess solar energy for heavy appliance usage.",
        "Encourage the homeowner to store surplus energy in batteries for later use."
    ],
    "moderate_solar": [
        "Suggest balancing energy consumption and battery storage for efficient use.",
        "Recommend checking the battery charge levels to ensure sufficient energy overnight."
    ],
    "low_solar": [
        "Advise reducing non-essential energy consumption due to low sunlight.",
        "Suggest scheduling appliance usage to avoid overloading the battery reserves."
    ],
    "night": [
        "Ensure the homeowner is aware of nighttime energy limitations and prioritizes essential usage.",
        "Advise monitoring battery discharge levels to prevent excessive drain overnight."
    ]
}

# **Generate Recommendations**
# Modify the function to return only one recommendation (closest upcoming forecast hour)
def generate_installer_recommendations(homeowner: Homeowner, forecast):
    if not forecast:
        return None  # Return None if no valid forecast exists
    
    # Pick the first available forecast hour
    entry = forecast[0]  
    timestamp, cloud_cover = entry["timestamp"], entry["cloud_cover"]
    irradiance = estimate_irradiance(cloud_cover)
    hour = int(timestamp[11:13])

    if 20 <= hour <= 23 or hour <= 6:  # Nighttime logic
        max_ac_current = calculate_max_ac_current_night(
            homeowner.initial_battery_level, homeowner.battery_efficiency, homeowner.inverter_efficiency
        )
        recommendation_text = random.choice(INSTALLER_RECOMMENDATIONS["night"])
    else:  # Daytime logic
        max_ac_current = calculate_max_ac_current_day(
            irradiance, homeowner.num_panels, homeowner.panel_power, homeowner.inverter_efficiency
        )
        condition = "high_solar" if irradiance > 800 else "low_solar" if irradiance < 400 else "moderate_solar"
        recommendation_text = random.choice(INSTALLER_RECOMMENDATIONS[condition])

    return {
        "timestamp": timestamp,
        "cloud_cover": cloud_cover,
        "irradiance": irradiance,
        "max_ac_current": max_ac_current,
        "recommendation": recommendation_text
    }

# **API Endpoint for Installer (Modified)**
@app.post("/get-installer-recommendations/")
def get_installer_recommendations(request: InstallerRequest):
    installer_recommendations = []

    for homeowner in request.homeowners:
        forecast = fetch_weather_forecast(homeowner.location)
        if not forecast:
            return {"error": f"Could not fetch weather data for {homeowner.location}"}
        
        filtered_forecast = filter_tomorrow_forecast(forecast)
        recommendation = generate_installer_recommendations(homeowner, filtered_forecast)

        if recommendation:
            installer_recommendations.append({
                "location": homeowner.location,
                "recommendation": recommendation
            })
    
    # Sort homeowners by location before returning
    installer_recommendations.sort(key=lambda x: x["location"])

    return {"installer_recommendations": installer_recommendations}
