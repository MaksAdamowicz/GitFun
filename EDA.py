import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

# 1. Fixed Parameters from previous questions
capacity = 250
p_L = 75
sigma = 9.73
intercept = 416.79
slope = -1.6685

# Range of prices to test
prices = np.arange(100, 251, 1)

# Arrays to store tracking variables
y_opt_vals, b_opt_vals, er_vals = [], [], []

for p_H in prices:
    # Expected demand at this specific price
    mu = intercept + slope * p_H
    
    # Calculate Protection Level (y*) using Littlewood's Rule
    # 1 - CDF(z*) = p_L / p_H
    z_star = norm.ppf(1 - p_L / p_H)
    y_star = mu + z_star * sigma
    
    # Restrict y* to physical capacity boundaries [0, 250]
    y_star = max(0, min(capacity, y_star))
    b_star = capacity - y_star
    
    # Calculate Expected Sales for business guests using normal loss function
    z_c = (y_star - mu) / sigma
    expected_lost_sales = norm.pdf(z_c) - z_c * (1 - norm.cdf(z_c))
    exp_sales_H = mu - sigma * expected_lost_sales
    
    # Calculate Total Expected Revenue at this price
    er = (p_L * b_star) + (p_H * exp_sales_H)
    
    y_opt_vals.append(y_star)
    b_opt_vals.append(b_star)
    er_vals.append(er)

# Convert to plotting arrays
y_opt_vals = np.array(y_opt_vals)
b_opt_vals = np.array(b_opt_vals)
er_vals = np.array(er_vals)

# --- Plot 1: Expected Revenue vs. Price ---
plt.figure(figsize=(10, 6))
plt.plot(prices, er_vals, label='Total Expected Revenue', color='green', linewidth=2.5)
optimal_idx = np.argmax(er_vals)
plt.axvline(x=prices[optimal_idx], color='red', linestyle='--', label=f'Optimal Price: €{prices[optimal_idx]}')
plt.title('Total Expected Daily Revenue vs. Business Price (p_H)')
plt.xlabel('Business Price (€)')
plt.ylabel('Expected Daily Revenue (€)')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.7)
plt.savefig('revenue_vs_price.png')

# --- Plot 2: Booking Limits and Protection Levels vs. Price ---
plt.figure(figsize=(10, 6))
plt.plot(prices, y_opt_vals, label='Protection Level for Business (y*)', color='orange', linewidth=2.5)
plt.plot(prices, b_opt_vals, label='Booking Limit for Students (b*)', color='blue', linewidth=2.5)
plt.axvline(x=prices[optimal_idx], color='red', linestyle='--', label=f'Optimal Price: €{prices[optimal_idx]}')
plt.title('Optimal Booking Limit and Protection Level vs. Business Price')
plt.xlabel('Business Price (€)')
plt.ylabel('Number of Rooms')
plt.legend()
plt.grid(True, linestyle='--', alpha=0.7)
plt.savefig('limits_vs_price.png')

# Print out specific results
er_180 = er_vals[np.where(prices == 180)[0][0]]
print(f"Optimal Price: €{prices[optimal_idx]}")
print(f"Max Revenue: €{er_vals[optimal_idx]:.2f}")
print(f"Revenue at €180: €{er_180:.2f}")
print(f"Revenue Increase: €{er_vals[optimal_idx] - er_180:.2f}")