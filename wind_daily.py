import pandas as pd
import openmeteo_requests
import requests_cache
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from retry_requests import retry
import numpy as np

def fetch_wind_data(lat, lon, start_date, end_date):
    """Fetches daily mean wind speed (m/s) at 10m height."""
    cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": ["wind_speed_10m_mean"],
        "wind_speed_unit": "ms", 
        "timezone": "Europe/Amsterdam"
    }

    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    daily = response.Daily()

    wind_speeds = daily.Variables(0).ValuesAsNumpy()
    dates = pd.date_range(start=start_date, periods=len(wind_speeds), freq="D")

    df = pd.DataFrame({
        "date": dates,
        "wind_speed_10m_ms": wind_speeds
    })
    
    return df.dropna().reset_index(drop=True)


def simulate_turbines_on_campus(df_weather, buildings_config):
    df = df_weather.copy()

    # --- System Specs Provided ---
    ROTOR_DIAMETER = 4.50
    ROTOR_HEIGHT = 4.80
    TURBINE_CAP_KW = 6.0
    VELOCITY_AUGMENTATION = 1.55 
    AIR_DENSITY = 1.225
    TURBINE_EFFICIENCY = 0.40 
    HELLMANN_EXPONENT = 0.30  # Urban/campus terrain roughness
    
    swept_area = ROTOR_DIAMETER * ROTOR_HEIGHT 
    max_daily_kwh_per_turbine = TURBINE_CAP_KW * 24

    # --- Calculations per Building ---
    for name, props in buildings_config.items():
        height = props['height']
        qty = props['turbines']
        
        # 1. Scale wind speed from 10m to building height
        df[f'wind_speed_{name}'] = df['wind_speed_10m_ms'] * ((height / 10) ** HELLMANN_EXPONENT)

        # 2. Augment the external wind speed
        df[f'internal_wind_speed_{name}'] = df[f'wind_speed_{name}'] * VELOCITY_AUGMENTATION
        
        # 3. Calculate Power (Watts) for ONE turbine
        df[f'power_{name}_watts'] = 0.5 * AIR_DENSITY * swept_area * (df[f'internal_wind_speed_{name}'] ** 3) * TURBINE_EFFICIENCY
        
        # 4. Convert to Daily kWh per turbine and apply physical cap
        df[f'daily_kwh_{name}_single'] = (df[f'power_{name}_watts'] * 24) / 1000
        df[f'daily_kwh_{name}_single'] = df[f'daily_kwh_{name}_single'].clip(upper=max_daily_kwh_per_turbine)
        
        # 5. Multiply by number of turbines on this specific roof
        df[f'daily_kwh_{name}_total'] = df[f'daily_kwh_{name}_single'] * qty

    return df


def save_daily_windspeeds_csv(df_results, buildings_config, filename="daily_windspeeds.csv"):
    """Save raw, roof-height, and augmented daily wind speeds to a CSV file."""
    windspeed_columns = ["date", "wind_speed_10m_ms"]

    for name in buildings_config.keys():
        windspeed_columns.extend([
            f"wind_speed_{name}",
            f"internal_wind_speed_{name}",
        ])

    df_results[windspeed_columns].to_csv(filename, index=False)
    return filename


# ==========================================
# --- Execution Phase ---
# ==========================================

# Define our campus setup
campus_buildings = {
    'Atlas': {'height': 53.0, 'turbines': 4, 'color': '#1f77b4'},   # Blue
    'Vertigo': {'height': 58.0, 'turbines': 3, 'color': '#2ca02c'}, # Green
    'Helix': {'height': 55.0, 'turbines': 3, 'color': '#d62728'},   # Red
    'Flux': {'height': 40.0, 'turbines': 3, 'color': '#9467bd'}     # Purple
}

print("Fetching weather data for Eindhoven (TU/e Campus)...")
df_weather = fetch_wind_data(lat=51.4475, lon=5.4855, start_date="2023-01-01", end_date="2023-12-31")

print("Simulating wind turbine generation across campus...")
df_results = simulate_turbines_on_campus(df_weather, campus_buildings)

print("Saving daily wind speeds...")
windspeeds_filename = save_daily_windspeeds_csv(df_results, campus_buildings)
print(f"Saved {windspeeds_filename}")

# --- Summarize Totals ---
print("\n--- Simulation Results (Annual Summary) ---")
grand_total = 0
for name in campus_buildings.keys():
    annual_total = df_results[f'daily_kwh_{name}_total'].sum()
    grand_total += annual_total
    print(f"Total Generation on {name} ({campus_buildings[name]['turbines']} turbines) : {annual_total:,.2f} kWh")
print("-" * 43)
print(f"GRAND TOTAL CAMPUS GENERATION: {grand_total:,.2f} kWh\n")


# ==========================================
# --- Visualization Phase ---
# ==========================================
print("Generating graphs...")
plt.style.use('default')

# 1. Separate Daily Line Graphs for EACH building
for name, props in campus_buildings.items():
    plt.figure(figsize=(12, 5))
    plt.plot(df_results['date'], df_results[f'daily_kwh_{name}_total'], 
             label=f'{name} ({props["turbines"]} turbines)', color=props['color'], alpha=0.8, linewidth=1.5)
    
    plt.title(f'Daily Wind Energy Generation: {name} Roof (2023)', fontsize=14, pad=15)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Energy Generated (kWh/day)', fontsize=12)
    plt.legend(loc='upper right')
    plt.grid(True, linestyle='--', alpha=0.5)

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.xticks(rotation=45)
    plt.tight_layout()

    filename = f'daily_generation_{name.lower()}.png'
    plt.savefig(filename, dpi=300)
    plt.close() # Close the figure to free up memory
    print(f"Saved {filename}")

# 2. Combined Monthly Grouped Bar Graph
df_monthly = df_results.set_index('date').resample('ME').sum()
month_labels = df_monthly.index.strftime('%b')

x = np.arange(len(month_labels))  
width = 0.2 # Thinner bars to fit 4 per month
offsets = [-1.5, -0.5, 0.5, 1.5] # Offsets to group bars around the center tick

plt.figure(figsize=(14, 6))

for idx, (name, props) in enumerate(campus_buildings.items()):
    plt.bar(x + (offsets[idx] * width), df_monthly[f'daily_kwh_{name}_total'], 
            width, label=f'{name} ({props["turbines"]} turbines)', color=props['color'], alpha=0.8)

plt.title('Monthly Wind Energy Generation by Building (Combined)', fontsize=14, pad=15)
plt.xlabel('Month', fontsize=12)
plt.ylabel('Total Energy Generated (kWh)', fontsize=12)
plt.xticks(x, month_labels)
plt.legend(loc='upper right')
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()

plt.savefig('monthly_generation_combined.png', dpi=300)
print("Saved monthly_generation_combined.png")
print("All visualizations complete!")
