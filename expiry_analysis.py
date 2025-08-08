def expiry_bias_score(row):
    score = 0

    # OI + Price Based Bias Logic
    if row['changeinOpenInterest_CE'] > 0 and row['lastPrice_CE'] > row['previousClose_CE']:
        score += 1  # New CE longs → Bullish
    if row['changeinOpenInterest_PE'] > 0 and row['lastPrice_PE'] > row['previousClose_PE']:
        score -= 1  # New PE longs → Bearish
    if row['changeinOpenInterest_CE'] > 0 and row['lastPrice_CE'] < row['previousClose_CE']:
        score -= 1  # CE writing → Bearish
    if row['changeinOpenInterest_PE'] > 0 and row['lastPrice_PE'] < row['previousClose_PE']:
        score += 1  # PE writing → Bullish

    # Bid Volume Dominance
    if 'bidQty_CE' in row and 'bidQty_PE' in row:
        if row['bidQty_CE'] > row['bidQty_PE'] * 1.5:
            score += 1  # CE Bid dominance → Bullish
        if row['bidQty_PE'] > row['bidQty_CE'] * 1.5:
            score -= 1  # PE Bid dominance → Bearish

    # Volume Churn vs OI
    if row['totalTradedVolume_CE'] > 2 * row['openInterest_CE']:
        score -= 0.5  # CE churn → Possibly noise
    if row['totalTradedVolume_PE'] > 2 * row['openInterest_PE']:
        score += 0.5  # PE churn → Possibly noise

    # Bid-Ask Pressure
    if 'underlyingValue' in row:
        if abs(row['lastPrice_CE'] - row['underlyingValue']) < abs(row['lastPrice_PE'] - row['underlyingValue']):
            score += 0.5  # CE closer to spot → Bullish
        else:
            score -= 0.5  # PE closer to spot → Bearish

    return score

def expiry_entry_signal(df, support_levels, resistance_levels, instrument, score_threshold=1.5):
    entries = []
    for _, row in df.iterrows():
        strike = row['strikePrice']
        score = expiry_bias_score(row)

        # Entry at support/resistance + Bias Score Condition
        if score >= score_threshold and strike in support_levels:
            entries.append({
                'type': 'BUY CALL',
                'strike': strike,
                'score': score,
                'ltp': row['lastPrice_CE'],
                'reason': 'Bullish score + support zone',
                'instrument': instrument
            })

        if score <= -score_threshold and strike in resistance_levels:
            entries.append({
                'type': 'BUY PUT',
                'strike': strike,
                'score': score,
                'ltp': row['lastPrice_PE'],
                'reason': 'Bearish score + resistance zone',
                'instrument': instrument
            })

    return entries