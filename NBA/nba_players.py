import pandas as pd
from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog
import matplotlib.pyplot as plt

# --- STEP 1: Get the Player ID ---
# The API requires a numerical ID (e.g., LeBron is 2544)
curry_dict = players.find_players_by_full_name('Stephen Curry')
curry_id = curry_dict[0]['id']

lebron_dict = players.find_players_by_full_name('LeBron James')
lebron_id = lebron_dict[0]['id']

# --- STEP 2: Fetch the Game Log ---
# We request the game log for a specific season (e.g., '2023-24' or '2024-25')
curry_gamelog = playergamelog.PlayerGameLog(player_id=curry_id, season='2024-25')
lebron_gamelog = playergamelog.PlayerGameLog(player_id=lebron_id, season='2024-25')

# Convert the API response to a pandas DataFrame
df_curry = curry_gamelog.get_data_frames()[0]
df_lebron = lebron_gamelog.get_data_frames()[0]

# Display the first 5 rows to check the data
print(df_curry[['GAME_DATE', 'MATCHUP', 'PTS', 'AST', 'REB']].head())
print(df_lebron[['GAME_DATE', 'MATCHUP', 'PTS', 'AST', 'REB']].head())


# --- STEP 3: Data Analysis ---
# Convert GAME_DATE to datetime objects for proper plotting
df_curry['GAME_DATE'] = pd.to_datetime(df_curry['GAME_DATE'])
df_lebron['GAME_DATE'] = pd.to_datetime(df_lebron['GAME_DATE'])

# Calculate simple aggregates
avg_points_curry = df_curry['PTS'].mean()
max_points_curry = df_curry['PTS'].max()

avg_points_lebron = df_lebron['PTS'].mean()
max_points_lebron = df_lebron['PTS'].max()
# --- STEP 4: Visualization ---
plt.figure(figsize=(12, 6))

# Plot Points per Game over time
plt.plot(df_curry['GAME_DATE'], df_curry['PTS'], marker='o', linestyle='-', color='purple', label='Stephen Curry')
plt.plot(df_lebron['GAME_DATE'], df_lebron['PTS'], marker='o', linestyle='-', color='orange', label='LeBron James')

# Add a horizontal line for his average
plt.axhline(avg_points_curry, color='gray', linestyle='--', label=f'Season Avg ({avg_points_curry:.1f})')

plt.title(f'Stephen Curry Scoring Trend (2024-25)', fontsize=16)
plt.xlabel('Date')
plt.ylabel('Points')
plt.legend()
plt.grid(True, alpha=0.3)

plt.show()