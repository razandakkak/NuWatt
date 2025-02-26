# Solar Energy Recommendation System

This project provides energy consumption recommendations based on weather forecasts for both **homeowners** and **installers** managing multiple homes with solar energy systems.

## 📌 Features
- Fetches weather forecasts using the OpenWeather API.
- Estimates **solar irradiance** based on cloud cover.
- Calculates **maximum AC current** during the day and night.
- Provides **personalized energy consumption recommendations** for:
  - **Homeowners:** Helps optimize energy usage based on weather conditions.
  - **Installers:** Allows managing multiple homeowners and provides location-based recommendations.

## 🛠 Installation

### 1️⃣ Clone the Repository
```
git clone https://github.com/yourusername/solar-energy-recommendations.git
```
```
cd solar-energy-recommendations
```
# 🚀 Usage
🔹 Homeowner Version
- The user enters their location, number of solar panels, battery details, and efficiency parameters.
- The script fetches weather data and calculates solar irradiance.
- Generates daily energy recommendations to optimize usage.

🔹 Installer Version
1. The installer inputs details for multiple homeowners (location, panel & battery setup).
2. The script fetches and analyzes weather data for each homeowner.
3. Homeowners are sorted by location and personalized recommendations are generated.
4. The installer can view and manage energy suggestions for different locations.
