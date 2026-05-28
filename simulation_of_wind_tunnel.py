import math

def simulate_dynamic_hybrid_tunnel(length, inlet_diameter, throat_diameter, turbine_diameter, external_wind_speed, packing_factor=0.75):
    # --- Assumptions & Constants ---
    AIR_DENSITY = 1.225              
    SYSTEM_EFFICIENCY = 0.40         
    HOURS_IN_YEAR = 8760
    DIFFUSER_EFFICIENCY = 0.65       # Accounts for backpressure/air spilling around the tunnel

    PANEL_AREA = 1.6                 
    PANEL_POWER = 300                
    PEAK_SUN_HOURS_PER_YEAR = 1460   
    
    # --- Error Checking ---
    if turbine_diameter > throat_diameter:
        raise ValueError("Error: Turbine cannot be larger than the tunnel throat.")
    if inlet_diameter < throat_diameter:
        raise ValueError("Error: Inlet must be larger than or equal to the throat to create a Venturi effect.")

    # --- Solar Calculation (Based on Average Width) ---
    # Since the tunnel is now a funnel, we'll estimate the roof area using the average diameter
    avg_diameter = (inlet_diameter + throat_diameter) / 2
    gross_roof_area = length * avg_diameter 
    usable_roof_area = gross_roof_area * packing_factor
    num_panels = int(usable_roof_area // PANEL_AREA)
    annual_solar_kwh = (num_panels * PANEL_POWER * PEAK_SUN_HOURS_PER_YEAR) / 1000

    # --- Dynamic Augmentation Calculation ---
    # Calculate the theoretical speedup based on Area Ratio
    theoretical_augmentation = (inlet_diameter / throat_diameter) ** 2
    
    # Apply diffuser efficiency to account for real-world backpressure
    # Formula: 1 + ((Theoretical - 1) * Efficiency)
    actual_augmentation = 1 + ((theoretical_augmentation - 1) * DIFFUSER_EFFICIENCY)
    
    internal_wind_speed = external_wind_speed * actual_augmentation
    
    # --- Wind Power Calculation ---
    swept_area = math.pi * ((turbine_diameter / 2) ** 2)
    wind_power_watts = 0.5 * AIR_DENSITY * swept_area * (internal_wind_speed ** 3) * SYSTEM_EFFICIENCY
    annual_wind_kwh = (wind_power_watts * HOURS_IN_YEAR) / 1000

    # --- Total Generation ---
    total_energy_kwh = annual_solar_kwh + annual_wind_kwh

    # --- Output Results ---
    print(f"--- Dynamic Aerodynamic Simulation ---")
    print(f"External Wind Speed    : {external_wind_speed} m/s")
    print(f"Inlet Dia: {inlet_diameter}m -> Throat Dia: {throat_diameter}m")
    print(f"Calculated Augmentation: {actual_augmentation:.2f}x (Accounting for backpressure)")
    print(f"Internal Wind Speed    : {internal_wind_speed:.2f} m/s\n")
    
    print(f"Annual Solar Yield     : {annual_solar_kwh:,.2f} kWh")
    print(f"Annual Wind Yield      : {annual_wind_kwh:,.2f} kWh")
    print(f"TOTAL ANNUAL ENERGY    : {total_energy_kwh:,.2f} kWh")
    print(f"--------------------------------------")

# --- Run the Simulation ---
# Using a 7m inlet funneling down to a 5m throat
simulate_dynamic_hybrid_tunnel(length=8, inlet_diameter=8, throat_diameter=6.5, turbine_diameter=4.5, external_wind_speed=5.5)