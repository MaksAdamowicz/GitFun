import pandas as pd
import openmeteo_requests
import requests_cache
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from retry_requests import retry
import numpy as np

def fetch_hybrid_data(lat, lon, start_date, end_date):
    """Fetches daily mean wind speed (m/s) and daily solar radiation sum (MJ/m²)."""
    cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": ["wind_speed_10m_mean", "shortwave_radiation_sum"], 
        "wind_speed_unit": "ms", 
        "timezone": "Europe/Amsterdam"
    }

    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    daily = response.Daily()

    wind_speeds = daily.Variables(0).ValuesAsNumpy()
    solar_radiation_mj = daily.Variables(1).ValuesAsNumpy()
    
    dates = pd.date_range(start=start_date, periods=len(wind_speeds), freq="D")

    df = pd.DataFrame({
        "date": dates,
        "wind_speed_10m_ms": wind_speeds,
        "solar_radiation_mj_m2": solar_radiation_mj
    })
    
    return df.dropna().reset_index(drop=True)


def simulate_hybrid_campus(df_weather, buildings_config):
    df = df_weather.copy()

    # --- System Specs (Optimized New Design) ---
    ROTOR_DIAMETER = 4.50
    ROTOR_HEIGHT = 4.80
    TURBINE_CAP_KW = 6.0          
    VELOCITY_AUGMENTATION = 1.65  
    AIR_DENSITY = 1.225
    TURBINE_EFFICIENCY = 0.40 
    HELLMANN_EXPONENT = 0.30      
    
    # --- Solar Specs (Integrated on Turbine Structures) ---
    SOLAR_PANEL_EFFICIENCY = 0.20  
    AVAILABLE_SOLAR_AREA_PER_TURBINE = 15.0  
    TRANSPOSITION_FACTOR = 1.15    
    
    swept_area = ROTOR_DIAMETER * ROTOR_HEIGHT 
    max_daily_wind_kwh = TURBINE_CAP_KW * 24

    # Convert Open-Meteo MJ/m² to kWh/m²
    df['solar_kwh_per_m2_flat'] = df['solar_radiation_mj_m2'] * 0.277778
    df['solar_kwh_per_m2_tilted'] = df['solar_kwh_per_m2_flat'] * TRANSPOSITION_FACTOR

    # --- Calculations per Building ---
    for name, props in buildings_config.items():
        height = props['height']
        qty = props['turbines']
        
        # 1. WIND GENERATION
        df[f'wind_speed_{name}'] = df['wind_speed_10m_ms'] * ((height / 10) ** HELLMANN_EXPONENT)
        df[f'augmented_wind_{name}'] = df[f'wind_speed_{name}'] * VELOCITY_AUGMENTATION
        
        power_watts = 0.5 * AIR_DENSITY * swept_area * (df[f'augmented_wind_{name}'] ** 3) * TURBINE_EFFICIENCY
        df[f'wind_kwh_{name}_single'] = ((power_watts * 24) / 1000).clip(upper=max_daily_wind_kwh)
        df[f'wind_kwh_{name}_total'] = df[f'wind_kwh_{name}_single'] * qty

        # 2. SOLAR GENERATION
        df[f'solar_kwh_{name}_single'] = df['solar_kwh_per_m2_tilted'] * AVAILABLE_SOLAR_AREA_PER_TURBINE * SOLAR_PANEL_EFFICIENCY
        df[f'solar_kwh_{name}_total'] = df[f'solar_kwh_{name}_single'] * qty

        # 3. COMBINED HYBRID OUTPUT (Single vs Total)
        df[f'hybrid_kwh_{name}_single'] = df[f'wind_kwh_{name}_single'] + df[f'solar_kwh_{name}_single']
        df[f'hybrid_kwh_{name}_total'] = df[f'wind_kwh_{name}_total'] + df[f'solar_kwh_{name}_total']

    return df


def save_hybrid_data_csv(df_results, buildings_config, filename="daily_hybrid_generation.csv"):
    cols = ["date", "wind_speed_10m_ms", "solar_radiation_mj_m2"]
    for name in buildings_config.keys():
        cols.extend([
            f"hybrid_kwh_{name}_single",
            f"hybrid_kwh_{name}_total"
        ])
    df_results[cols].to_csv(filename, index=False)
    return filename


# ==========================================
# --- Execution Phase ---
# ==========================================
campus_buildings = {
    'Atlas': {'height': 53.0, 'turbines': 4, 'color': '#1f77b4'},   
    'Vertigo': {'height': 58.0, 'turbines': 3, 'color': '#2ca02c'}, 
    'Helix': {'height': 55.0, 'turbines': 3, 'color': '#d62728'},   
    'Flux': {'height': 40.0, 'turbines': 3, 'color': '#9467bd'}     
}

print("Fetching historical weather & radiation data for TU/e Campus...")
df_weather = fetch_hybrid_data(lat=51.4475, lon=5.4855, start_date="2023-01-01", end_date="2023-12-31")

print("Running Hybrid Energy Generation Simulation...")
df_results = simulate_hybrid_campus(df_weather, campus_buildings)

# Calculate total aggregate campus capacities
df_results['campus_wind_total'] = sum(df_results[f'wind_kwh_{name}_total'] for name in campus_buildings)
df_results['campus_solar_total'] = sum(df_results[f'solar_kwh_{name}_total'] for name in campus_buildings)
df_results['campus_hybrid_total'] = df_results['campus_wind_total'] + df_results['campus_solar_total']

# Save results
csv_file = save_hybrid_data_csv(df_results, campus_buildings)
print(f"Saved database metrics to {csv_file}")

# --- Annual Breakdown Performance ---
print("\n--- Annual Generation Profile (PER SINGLE TURBINE SYSTEM) ---")
for name in campus_buildings.keys():
    single_wind = df_results[f'wind_kwh_{name}_single'].sum()
    single_solar = df_results[f'solar_kwh_{name}_single'].sum()
    single_hybrid = df_results[f'hybrid_kwh_{name}_single'].sum()
    print(f"🏢 1x Turbine on {name:7} (H={campus_buildings[name]['height']}m) | Wind: {single_wind:9,.1f} kWh | Solar: {single_solar:9,.1f} kWh | Total: {single_hybrid:9,.1f} kWh")


# -------------------------------------------------------------------------
# --- NEW: Seasonal Interchangability Analysis (Total Campus Overview) ---
# -------------------------------------------------------------------------
print("\n--- Seasonal Interchangeability Breakdown (TOTAL CAMPUS ENERGY) ---")

# Define seasonal periods using months
df_seasonal = df_results.copy()
df_seasonal['month'] = df_seasonal['date'].dt.month

# Summer: June (6), July (7), August (8)
df_summer = df_seasonal[df_seasonal['month'].isin([6, 7, 8])]
summer_wind = df_summer['campus_wind_total'].sum()
summer_solar = df_summer['campus_solar_total'].sum()
summer_total = df_summer['campus_hybrid_total'].sum()

# Winter: December (12), January (1), February (2)
df_winter = df_seasonal[df_seasonal['month'].isin([12, 1, 2])]
winter_wind = df_winter['campus_wind_total'].sum()
winter_solar = df_winter['campus_solar_total'].sum()
winter_total = df_winter['campus_hybrid_total'].sum()

# Print text table matrix
print(f"{'Season':<10} | {'Total Wind Energy':<20} | {'Total Solar Energy':<20} | {'Combined Total Output':<22} | {'Solar Share':<12}")
print("-" * 93)
print(f"{'SUMMER':<10} | {summer_wind:17,.1f} kWh | {summer_solar:17,.1f} kWh | {summer_total:19,.1f} kWh | {(summer_solar/summer_total)*100:6.1f}%")
print(f"{'WINTER':<10} | {winter_wind:17,.1f} kWh | {winter_solar:17,.1f} kWh | {winter_total:19,.1f} kWh | {(winter_solar/winter_total)*100:6.1f}%")
print("-" * 93)
print(f"💡 Key Insight: Solar provides {(summer_solar/summer_total)*100:.1f}% of your energy in summer, but drops to just {(winter_solar/winter_total)*100:.1f}% in winter!")


# ==========================================
# --- Visualization Phase ---
# ==========================================
print("\nGenerating tracking plots...")
plt.style.use('default')

# 1. Separate Daily Line Graphs for ONE turbine on EACH building
for name, props in campus_buildings.items():
    plt.figure(figsize=(12, 5))
    
    plt.plot(df_results['date'], df_results[f'hybrid_kwh_{name}_single'], 
             label=f'Single Turbine System on {name}', color=props['color'], alpha=0.9, linewidth=1.5)
    
    plt.title(f'Daily Energy Generation for ONE Turbine System: {name} Roof ({props["height"]}m)', fontsize=14, pad=15)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Energy Generated (kWh/day)', fontsize=12)
    plt.legend(loc='upper right')
    plt.grid(True, linestyle='--', alpha=0.5)

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.xticks(rotation=45)
    plt.tight_layout()

    filename = f'single_turbine_daily_{name.lower()}.png'
    plt.savefig(filename, dpi=300)
    plt.close()
    print(f"Saved {filename}")

# 2. Combined Monthly Grouped Bar Graph (Side-by-Side SINGLE Turbine Comparison)
df_monthly = df_results.set_index('date').resample('ME').sum()
month_labels = df_monthly.index.strftime('%b')

x = np.arange(len(month_labels))  
width = 0.2                      
offsets = [-1.5, -0.5, 0.5, 1.5] 

plt.figure(figsize=(14, 6))

for idx, (name, props) in enumerate(campus_buildings.items()):
    plt.bar(x + (offsets[idx] * width), df_monthly[f'hybrid_kwh_{name}_single'], 
            width, label=f'{name} (Single Unit @ {props["height"]}m)', color=props['color'], alpha=0.85)

plt.title('Monthly Energy Generation per SINGLE Turbine System (Side-by-Side Height Efficiency Comparison)', fontsize=14, pad=15)
plt.xlabel('Month', fontsize=12)
plt.ylabel('Energy Generated per Turbine (kWh)', fontsize=12)
plt.xticks(x, month_labels)
plt.legend(loc='upper right')
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()

plt.savefig('monthly_generation_single_turbine_comparison.png', dpi=300)
plt.close()
print("Saved monthly_generation_single_turbine_comparison.png")

# 3. Stacked Bar Chart for Total Campus Monthly Generation (Wind vs. Solar)
df_monthly_total = df_results.set_index('date').resample('ME').sum()

plt.figure(figsize=(12, 6))
x_stack = np.arange(len(month_labels))

plt.bar(x_stack, df_monthly_total['campus_wind_total'], 
        label='Total Wind Energy', color='#4c72b0', alpha=0.9, edgecolor='black', linewidth=0.5)
plt.bar(x_stack, df_monthly_total['campus_solar_total'], bottom=df_monthly_total['campus_wind_total'], 
        label='Total Solar Energy', color='#dd8452', alpha=0.9, edgecolor='black', linewidth=0.5)

plt.title('Total Campus Energy Generation: Wind vs. Solar (All Buildings Combined)', fontsize=14, pad=15)
plt.xlabel('Month', fontsize=12)
plt.ylabel('Total Energy Generated (kWh)', fontsize=12)
plt.xticks(x_stack, month_labels)
plt.legend(loc='upper right')
plt.grid(axis='y', linestyle='--', alpha=0.5)
plt.tight_layout()

plt.savefig('campus_monthly_stacked_wind_solar.png', dpi=300)
plt.close()
print("Saved campus_monthly_stacked_wind_solar.png")

print("All visualizations complete!")