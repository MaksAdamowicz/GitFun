import pandas as pd
import openmeteo_requests
import requests_cache
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from retry_requests import retry

def fetch_weather_data(lat, lon, start_date, end_date):
    """Fetches daily mean wind speed (m/s) and daily solar radiation sum (MJ/m²)."""
    # Setup the Open-Meteo API client with cache and retry on error
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

    # Fetch data
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    daily = response.Daily()

    # Extract variables
    wind_speeds = daily.Variables(0).ValuesAsNumpy()
    solar_radiation_mj = daily.Variables(1).ValuesAsNumpy()
    
    # Create datetime index
    dates = pd.date_range(start=start_date, periods=len(wind_speeds), freq="D")

    # Build DataFrame
    df = pd.DataFrame({
        "date": dates,
        "wind_speed": wind_speeds,
        "solar_radiation": solar_radiation_mj
    })
    
    return df.dropna().reset_index(drop=True)

def plot_weather_data(df):
    """Generates stacked line graphs for Wind Speed and Solar Radiation."""
    # Create a figure with 2 subplots that share the same X-axis
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    
    # --- Top Plot: Wind Speed ---
    ax1.plot(df['date'], df['wind_speed'], color='#4c72b0', linewidth=1.5, alpha=0.9)
    ax1.set_title('Daily Mean Wind Speed in Eindhoven (2023)', fontsize=14, pad=10)
    ax1.set_ylabel('Wind Speed (m/s)', fontsize=12)
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    # --- Bottom Plot: Solar Radiation ---
    ax2.plot(df['date'], df['solar_radiation'], color='#dd8452', linewidth=1.5, alpha=0.9)
    ax2.set_title('Daily Solar Radiation Sum in Eindhoven (2023)', fontsize=14, pad=10)
    ax2.set_ylabel('Solar Radiation (MJ/m²)', fontsize=12)
    ax2.grid(True, linestyle='--', alpha=0.5)
    
    # --- Formatting the X-Axis ---
    ax2.set_xlabel('Date', fontsize=12)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax2.xaxis.set_major_locator(mdates.MonthLocator())
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    
    # Save the graph
    filename = 'eindhoven_wind_solar_2023.png'
    plt.savefig(filename, dpi=300)
    print(f"Graph saved successfully as {filename}")

# ==========================================
# --- Execution Phase ---
# ==========================================
if __name__ == "__main__":
    print("Fetching weather data for Eindhoven...")
    
    # Eindhoven coordinates
    LAT = 51.4475
    LON = 5.4855
    # Full year 2023
    START = "2023-01-01"
    END = "2023-12-31"

    df_weather = fetch_weather_data(lat=LAT, lon=LON, start_date=START, end_date=END)

    print("Generating line graphs...")
    plot_weather_data(df_weather)