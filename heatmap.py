import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

# --- 1. Load the Map Image ---
image_path = 'tue_map.png' 
try:
    img = Image.open(image_path)
    # Convert to numpy array to ensure perfect Matplotlib compatibility
    img_array = np.array(img)
except FileNotFoundError:
    print(f"Error: Could not find {image_path}. Please check the file name and location.")
    exit()

# --- 2. Wind Calculation Parameters ---
v_0 = 5.0      # Base wind speed at 10m (m/s)
h_0 = 10.0     # Reference height (m)
alpha = 0.35   # Urban friction coefficient

# --- 3. Building Data ---
buildings = [
    'Luna', 'Vertigo', 'Castor', 'Pollux', 'Atlas', 
    'Auditorium', 'Matrix', 'MetaForum'
]

# Estimated heights in meters
heights = np.array([50, 50, 50, 50, 40, 15, 15, 20])

# --- 4. Auto-Scaling Coordinates ---
# Your measurements were taken on a smaller preview window (~850x650).
# We will dynamically scale them to fit your high-res (2339x1654) image perfectly!
measured_width = 850  
measured_height = 650 

scale_x = img.width / measured_width
scale_y = img.height / measured_height

# Your exact raw measurements
raw_x = [676, 502, 1013, 1218, 590, 441, 620, 695]
raw_y = [808, 1113, 569, 545, 918, 915, 1120, 954]

# Apply the scale factor so they match the real image file
x_pixels = np.array(raw_x) * scale_x
y_pixels = np.array(raw_y) * scale_y

# Calculate the estimated wind speed for each building's roof
wind_speeds = v_0 * (heights / h_0)**alpha

# --- 5. Plotting the Heatmap Over the Image ---
fig, ax = plt.subplots(figsize=(14, 10))

# Display the map image as the background
ax.imshow(img_array, extent=[0, img.width, img.height, 0])

# Scale the bubble size so they don't look tiny on a 4K image
bubble_size = heights * 30 * (scale_x ** 1.5)

# Plot the heatmap bubbles
scatter = ax.scatter(x_pixels, y_pixels, c=wind_speeds, cmap='jet', 
                     s=bubble_size, alpha=0.6, edgecolors='black', linewidth=2)

# Add the labels next to each bubble
for i, txt in enumerate(buildings):
    # Using 'offset points' makes the text distance consistent regardless of image resolution
    ax.annotate(f"{txt}\n({wind_speeds[i]:.1f} m/s)", 
                (x_pixels[i], y_pixels[i]), 
                xytext=(15, 15), textcoords='offset points',
                fontsize=11, fontweight='bold', color='black',
                bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=2))

# Add a color bar legend to the side
cbar = plt.colorbar(scatter, ax=ax, fraction=0.03, pad=0.04)
cbar.set_label('Estimated Roof Wind Speed (m/s)', fontsize=12, fontweight='bold')

# Final formatting
plt.title('TU/e Campus - Roof Wind Speed Heatmap', fontsize=16, fontweight='bold')
plt.axis('off') 
plt.tight_layout()

# Show the interactive plot window
plt.show()
