import requests
from datetime import datetime, timedelta
import random

# Weather API parameters
API_KEY = "_"
LOCATION = input("Enter your location (e.g., Tripoli, LB): ").strip()
PANEL_EFFICIENCY = 0.8  # 80%
AC_VOLTAGE = 220  # Volts

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
    elif response.status_code == 404:
        print("Location not found. Please enter a valid location.")
        return None
    else:
        print("Failed to fetch weather data:", response.json().get("message", "Unknown error"))
        return None

def get_valid_location():
    while True:
        location = input("Enter your location (e.g., Tripoli, LB): ").strip()
        forecast = fetch_weather_forecast(location, API_KEY)
        if forecast is not None:
            return location
        else:
            print("Invalid location, please try again.")

def filter_tomorrow_forecast(forecast):
    tomorrow_date = (datetime.now() + timedelta(days=1)).date()
    return [entry for entry in forecast if datetime.fromisoformat(entry['timestamp']).date() == tomorrow_date]

def estimate_irradiance(cloud_cover):
    return max(1000 - (cloud_cover * 5), 0)

# User inputs
num_panels = int(input("Enter the number of solar panels: "))
panel_power = float(input("Enter the power output of each panel in watts (e.g., 400): "))
battery_capacity = float(input("Enter the total battery capacity in kWh: "))
battery_efficiency = float(input("Enter the battery efficiency as a decimal (e.g., 0.9 for 90%): "))
num_batteries = int(input("Enter the number of batteries: "))
inverter_efficiency = float(input("Enter the inverter efficiency as a decimal (e.g., 0.95 for 95%): "))

def calculate_max_ac_current_day(irradiance, num_panels, panel_power, inverter_efficiency, AC_VOLTAGE):
    total_dc_power = irradiance * num_panels * panel_power * PANEL_EFFICIENCY / 1000
    return max((total_dc_power * inverter_efficiency) / AC_VOLTAGE, 0)

def calculate_max_ac_current_night(battery_level, battery_efficiency, inverter_efficiency, AC_VOLTAGE, night_hours):
    usable_battery_energy = battery_level * battery_efficiency
    total_ac_energy = usable_battery_energy * inverter_efficiency
    return max((total_ac_energy * 1000) / (AC_VOLTAGE * night_hours), 0)

RECOMMENDATION_SETS = {
    "high_solar": [
        "Great solar conditions! You can increase energy consumption while still charging the battery.",
        "Optimal sunlight detected! Run high-energy appliances without worrying about battery drain."
    ],
    "moderate_solar": [
        "Moderate solar conditions. Balance energy consumption and battery charging.",
        "Decent sunlight available. Use appliances wisely while ensuring battery storage."
    ],
    "low_solar": [
        "Low solar conditions. Limit energy consumption to essential devices to preserve battery.",
        "Cloudy conditions detected. Reduce energy usage to avoid draining the battery quickly."
    ],
    "night": [
        "Nighttime is here. You can consume up to {max_ac_current:.2f} A of AC current per hour tonight.",
        "It's nighttime. Ensure power efficiency by limiting usage to critical appliances."
    ]
}

def generate_recommendations(forecast, num_panels, panel_power, battery_capacity, num_batteries, battery_efficiency, inverter_efficiency, AC_VOLTAGE, night_hours=7):
    recommendations = []
    total_battery_capacity = battery_capacity * num_batteries
    battery_level = None  # Will be set once during the night hours

    for entry in forecast:
        timestamp, cloud_cover, temperature = entry["timestamp"], entry["cloud_cover"], entry["temperature"]
        irradiance = estimate_irradiance(cloud_cover)
        hour = int(timestamp[11:13])

        if 20 <= hour <= 23 or hour <= 6:
            # Ask for battery level only once during the night
            if battery_level is None:
                battery_level = float(input("Enter the current battery level in kWh: "))
            max_ac_current_night = calculate_max_ac_current_night(
                battery_level, battery_efficiency, inverter_efficiency, AC_VOLTAGE, night_hours
            )
            recommendation_text = random.choice(RECOMMENDATION_SETS["night"]).format(max_ac_current=max_ac_current_night)
        else:
            max_ac_current_day = calculate_max_ac_current_day(irradiance, num_panels, panel_power, inverter_efficiency, AC_VOLTAGE)
            condition = "high_solar" if irradiance > 800 else "low_solar" if irradiance < 400 else "moderate_solar"
            recommendation_text = random.choice(RECOMMENDATION_SETS[condition])

        # Store recommendation details for each entry
        recommendations.append({
            "timestamp": timestamp,
            "temperature": temperature,
            "cloud_cover": cloud_cover,
            "irradiance": irradiance,
            "max_ac_current": max_ac_current_night if hour in range(20, 24) or hour in range(0, 7) else max_ac_current_day,
            "recommendation": recommendation_text
        })
    return recommendations

# Fetch weather data and generate recommendations
forecast = fetch_weather_forecast(LOCATION, API_KEY)
if forecast:
    today_forecast = filter_tomorrow_forecast(forecast)
    recommendations = generate_recommendations(
        today_forecast, num_panels, panel_power, battery_capacity, num_batteries, battery_efficiency, inverter_efficiency, AC_VOLTAGE
    )
    print("\nEnergy Consumption Recommendations for Today:")
    for rec in recommendations:
        print(f"{rec['timestamp']} - {rec['recommendation']} - Max AC current: {rec['max_ac_current']} A")
else:
    print("Unable to fetch weather forecast data.")
