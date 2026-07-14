import pandas as pd

# Using a public, unblocked raw GitHub mirror of the 2022 World Cup dataset
url = "https://raw.githubusercontent.com/jokecamp/FootballData/master/world-cups/2022-qatar/world_cup_2022_odds.csv"

try:
    print("Fetching full tournament dataset from mirror...")
    df = pd.read_csv(url)
    print(f"Successfully loaded data! Found {len(df)} total rows.\n")
except Exception as e:
    print(f"Failed to fetch data directly: {e}")
    exit()

# Filter out rows missing core teams or match results
df = df.dropna(subset=['FTR', 'Home', 'Away'])

def run_unabridged_backtest(df, stake=100):
    total_spent = 0
    total_net_return = 0
    wins = 0
    losses = 0
    ot_draw_losses = 0
    
    print(f"{'Match':<38} | {'Your Bet':<8} | {'90-Min Result':<13} | {'Net Return':<10}")
    print("-" * 78)
    
    for idx, row in df.iterrows():
        match_name = f"{row['Home']} vs {row['Away']}"
        
        # Use Bet365 historical closing odds columns
        try:
            b365_h = float(row['B365H'])
            b365_a = float(row['B365A'])
        except (ValueError, TypeError):
            # Skip rows if betting odds are corrupt or blank
            continue
            
        ftr = str(row['FTR']).strip() # 'H' = Home, 'A' = Away, 'D' = Draw
        
        # Strategy rule: Identify and wager on the favorite (lowest odds)
        if b365_h < b365_a:
            your_bet = 'Home'
            chosen_odds = b365_h
        else:
            your_bet = 'Away'
            chosen_odds = b365_a
            
        total_spent += stake
        
        # Strict 90-minute win check. Overtime/Draw outcomes ('D') register as a loss.
        is_win = (your_bet == 'Home' and ftr == 'H') or (your_bet == 'Away' and ftr == 'A')
        
        if is_win:
            net_return = (stake * chosen_odds) - stake
            total_net_return += net_return
            wins += 1
            result_str = "WON"
        else:
            net_return = -stake
            total_net_return += net_return
            losses += 1
            if ftr == 'D':
                ot_draw_losses += 1
                result_str = "LOST (OT/Draw)"
            else:
                result_str = "LOST"
                
        print(f"{match_name:<38} | {your_bet:<8} | {result_str:<13} | ${net_return:>8.2f}")

    print("-" * 78)
    print(f"Total Matches Wagered On: {wins + losses}")
    print(f"Successful 90-Min Bets:  {wins}")
    print(f"Failed Bets (Outright):  {losses - ot_draw_losses}")
    print(f"Failed Bets (OT/Draw):   {ot_draw_losses}")
    print(f"Total Wagers Placed:     ${total_spent:.2f}")
    print(f"Net Profit / Loss:       ${total_net_return:.2f}")

run_unabridged_backtest(df, stake=100)