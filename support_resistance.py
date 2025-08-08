from config_setup import INSTRUMENTS

def determine_level(row):
    ce_oi = row['openInterest_CE']
    pe_oi = row['openInterest_PE']
    ce_chg = row['changeinOpenInterest_CE']
    pe_chg = row['changeinOpenInterest_PE']

    # Strong Support condition
    if pe_oi > 1.12 * ce_oi:
        return "Support"
    # Strong Resistance condition
    elif ce_oi > 1.12 * pe_oi:
        return "Resistance"
    # Neutral if none dominant
    else:
        return "Neutral"

def is_in_zone(spot, strike, level, instrument):
    zone_size = INSTRUMENTS['indices'].get(instrument, {}).get('zone_size', 20) or \
                INSTRUMENTS['stocks'].get(instrument, {}).get('zone_size', 20)
    
    if level == "Support":
        return strike - zone_size <= spot <= strike + zone_size
    elif level == "Resistance":
        return strike - zone_size <= spot <= strike + zone_size
    return False

def get_support_resistance_zones(df, spot, instrument):
    support_strikes = df[df['Level'] == "Support"]['strikePrice'].tolist()
    resistance_strikes = df[df['Level'] == "Resistance"]['strikePrice'].tolist()

    nearest_supports = sorted([s for s in support_strikes if s <= spot], reverse=True)[:2]
    nearest_resistances = sorted([r for r in resistance_strikes if r >= spot])[:2]

    support_zone = (min(nearest_supports), max(nearest_supports)) if len(nearest_supports) >= 2 else (nearest_supports[0], nearest_supports[0]) if nearest_supports else (None, None)
    resistance_zone = (min(nearest_resistances), max(nearest_resistances)) if len(nearest_resistances) >= 2 else (nearest_resistances[0], nearest_resistances[0]) if nearest_resistances else (None, None)

    return support_zone, resistance_zone