import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
import statsmodels.api as sm

# 1. Load data and estimate the demand model
# Assuming the file is named 'yearlyBookingData.xls - Sheet1.csv'
# Use read_excel instead of read_csv
df = pd.read_excel('yearlyBookingData.xls', header=None)
df.columns = ['Date', 'Price', 'Demand']

# Fit OLS Regression: Demand = a + b*Price + epsilon
X = sm.add_constant(df['Price'])
y = df['Demand']
model = sm.OLS(y, X).fit()
intercept, slope = model.params
sigma = np.std(model.resid, ddof=2)

# 2. Optimization Parameters
prices = np.linspace(100, 250, 151) # Prices to consider
p_l = 75                            # Fixed student price
capacity = 250                      # Total rooms

def calculate_metrics(p_h):
    # Mean demand for business at this price
    mu_h = intercept + slope * p_h
    
    # Littlewood's Rule for Optimal Protection Level (Q*)
    # P(D > Q) = p_l / p_h  =>  Phi((Q-mu)/sigma) = 1 - (p_l/p_h)
    target_prob = 1 - (p_l / p_h)
    z_star = norm.ppf(target_prob)
    q_star = mu_h + z_star * sigma
    
    # Ensure Q stays within physical capacity
    q_star = max(0, min(capacity, q_star))
    b_star = capacity - q_star
    
    # Expected business sales: E[min(D_h, Q)]
    z = (q_star - mu_h) / sigma
    exp_sales_h = mu_h * norm.cdf(z) - sigma * norm.pdf(z) + q_star * (1 - norm.cdf(z))
    
    # Total Expected Revenue
    rev = (b_star * p_l) + (exp_sales_h * p_h)
    return rev, b_star, q_star

# 3. Iterate through prices
results = [calculate_metrics(p) for p in prices]
rev_list, b_list, q_list = zip(*results)

# Find Optimal Point
max_idx = np.argmax(rev_list)
opt_p = prices[max_idx]
opt_rev = rev_list[max_idx]

# Comparison value (at p=180)
rev_180, _, _ = calculate_metrics(180)

# 4. Plotting
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 12))

# Plot (i): Total Expected Daily Revenue
ax1.plot(prices, rev_list, color='red', linewidth=2, label='Total Expected Revenue')
ax1.axvline(opt_p, color='black', linestyle='--', alpha=0.6)
ax1.set_title('Expected Daily Revenue vs. Business Price', fontsize=14)
ax1.set_xlabel('Price Charged to Business Travellers (€)', fontsize=12)
ax1.set_ylabel('Total Expected Revenue (€)', fontsize=12)
ax1.grid(True, alpha=0.3)
ax1.annotate(f'Optimal Price: €{opt_p:.2f}\nMax Rev: €{opt_rev:,.2f}', 
             xy=(opt_p, opt_rev), xytext=(opt_p+15, opt_rev-1000),
             arrowprops=dict(facecolor='black', shrink=0.05))

# Plot (ii): Optimal Booking Limits and Protection Levels
ax2.plot(prices, q_list, label='Optimal Protection Level ($Q^*$)', color='green', linewidth=2)
ax2.plot(prices, b_list, label='Optimal Booking Limit ($b^*$)', color='blue', linewidth=2)
ax2.set_title('Optimal Decision Variables vs. Business Price', fontsize=14)
ax2.set_xlabel('Price Charged to Business Travellers (€)', fontsize=12)
ax2.set_ylabel('Number of Rooms', fontsize=12)
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('revenue_optimization.png')

# 5. Print Results
print(f"Optimal Price for Business: €{opt_p:.2f}")
print(f"Maximized Daily Revenue: €{opt_rev:.2f}")
print(f"Revenue at €180: €{rev_180:.2f}")
print(f"Daily Revenue Increase: €{opt_rev - rev_180:.2f}")
print(f"Annual Revenue Increase: €{(opt_rev - rev_180)*365:,.2f}")
print(f"Optimal Protection Level (Q*): {q_list[max_idx]:.2f}")
print(f"Optimal Booking Limit (b*): {b_list[max_idx]:.2f}")