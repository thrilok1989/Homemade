import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from pytz import timezone

from config_setup import INSTRUMENTS
from core_calculations import send_telegram_message, calculate_greeks, final_verdict, delta_volume_bias, weights
from support_resistance import determine_level, is_in_zone, get_support_resistance_zones
from expiry_analysis import expiry_bias_score, expiry_entry_signal
from display_ui import display_enhanced_trade_log, handle_export_data, plot_price_with_sr
from log_management import auto_update_call_log, display_call_log_book

def analyze_instrument(instrument):
    try:
        now = datetime.now(timezone("Asia/Kolkata"))
        current_day = now.weekday()
        current_time = now.time()
        market_start = datetime.strptime("09:00", "%H:%M").time()
        market_end = datetime.strptime("19:40", "%H:%M").time()

        if current_day >= 5 or not (market_start <= current_time <= market_end):
            st.warning("⏳ Market Closed (Mon-Fri 9:00-15:40)")
            return

        headers = {"User-Agent": "Mozilla/5.0"}
        session = requests.Session()
        session.headers.update(headers)
        session.get("https://www.nseindia.com", timeout=5)
        
        # Handle spaces in instrument names
        url_instrument = instrument.replace(' ', '%20')
        url = f"https://www.nseindia.com/api/option-chain-indices?symbol={url_instrument}" if instrument in INSTRUMENTS['indices'] else \
              f"https://www.nseindia.com/api/option-chain-equities?symbol={url_instrument}"
        
        response = session.get(url, timeout=10)
        data = response.json()

        records = data['records']['data']
        expiry = data['records']['expiryDates'][0]
        underlying = data['records']['underlyingValue']

        # === Open Interest Change Comparison ===
        total_ce_change = sum(item['CE']['changeinOpenInterest'] for item in records if 'CE' in item) / 100000
        total_pe_change = sum(item['PE']['changeinOpenInterest'] for item in records if 'PE' in item) / 100000
        
        st.markdown(f"## 📊 {instrument} Open Interest Change (Lakhs)")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📉 CALL ΔOI", 
                     f"{total_ce_change:+.1f}L",
                     delta_color="inverse")
            
        with col2:
            st.metric("📈 PUT ΔOI", 
                     f"{total_pe_change:+.1f}L",
                     delta_color="normal")
        
        # Dominance indicator
        if total_ce_change > total_pe_change:
            st.error(f"🚨 Call OI Dominance (Difference: {abs(total_ce_change - total_pe_change):.1f}L")
        elif total_pe_change > total_ce_change:
            st.success(f"🚀 Put OI Dominance (Difference: {abs(total_pe_change - total_ce_change):.1f}L")
        else:
            st.info("⚖️ OI Changes Balanced")

        today = datetime.now(timezone("Asia/Kolkata"))
        expiry_date = timezone("Asia/Kolkata").localize(datetime.strptime(expiry, "%d-%b-%Y"))
        
        # EXPIRY DAY LOGIC
        is_expiry_day = today.date() == expiry_date.date()
        
        if is_expiry_day:
            st.info(f"""
📅 **{instrument} EXPIRY DAY DETECTED**
- Using specialized expiry day analysis
- IV Collapse, OI Unwind, Volume Spike expected
- Modified signals will be generated
""")
            send_telegram_message(f"⚠️ {instrument} Expiry Day Detected. Using special expiry analysis.")
            
            # Store spot history for expiry day
            current_time_str = now.strftime("%H:%M:%S")
            new_row = pd.DataFrame([[current_time_str, underlying]], columns=["Time", "Spot"])
            st.session_state[f'{instrument}_price_data'] = pd.concat([st.session_state[f'{instrument}_price_data'], new_row], ignore_index=True)
            
            st.markdown(f"### 📍 {instrument} Spot Price: {underlying}")
            
            # Get previous close data
            if instrument in INSTRUMENTS['indices']:
                prev_close_url = f"https://www.nseindia.com/api/equity-stockIndices?index={url_instrument}%20INDEX"
            else:
                prev_close_url = f"https://www.nseindia.com/api/quote-equity?symbol={url_instrument}"
                
            prev_close_data = session.get(prev_close_url, timeout=10).json()
            prev_close = prev_close_data['data'][0]['previousClose'] if instrument in INSTRUMENTS['indices'] else \
                         prev_close_data['priceInfo']['previousClose']
            
            # Process records with expiry day logic
            calls, puts = [], []
            for item in records:
                if 'CE' in item and item['CE']['expiryDate'] == expiry:
                    ce = item['CE']
                    ce['previousClose_CE'] = prev_close
                    ce['underlyingValue'] = underlying
                    calls.append(ce)
                if 'PE' in item and item['PE']['expiryDate'] == expiry:
                    pe = item['PE']
                    pe['previousClose_PE'] = prev_close
                    pe['underlyingValue'] = underlying
                    puts.append(pe)
            
            df_ce = pd.DataFrame(calls)
            df_pe = pd.DataFrame(puts)
            df = pd.merge(df_ce, df_pe, on='strikePrice', suffixes=('_CE', '_PE')).sort_values('strikePrice')
            
            # Get support/resistance levels
            df['Level'] = df.apply(determine_level, axis=1)
            support_levels = df[df['Level'] == "Support"]['strikePrice'].unique()
            resistance_levels = df[df['Level'] == "Resistance"]['strikePrice'].unique()
            
            # Generate expiry day signals
            expiry_signals = expiry_entry_signal(df, support_levels, resistance_levels, instrument)
            
            # Display expiry day specific UI
            st.markdown(f"### 🎯 {instrument} Expiry Day Signals")
            if expiry_signals:
                for signal in expiry_signals:
                    st.success(f"""
                    {signal['type']} at {signal['strike']} 
                    (Score: {signal['score']:.1f}, LTP: ₹{signal['ltp']})
                    Reason: {signal['reason']}
                    """)
                    
                    # Add to trade log
                    st.session_state[f'{instrument}_trade_log'].append({
                        "Time": now.strftime("%H:%M:%S"),
                        "Strike": signal['strike'],
                        "Type": 'CE' if 'CALL' in signal['type'] else 'PE',
                        "LTP": signal['ltp'],
                        "Target": round(signal['ltp'] * 1.2, 2),
                        "SL": round(signal['ltp'] * 0.8, 2)
                    })
                    
                    # Send Telegram alert
                    send_telegram_message(
                        f"📅 {instrument} EXPIRY DAY SIGNAL\n"
                        f"Type: {signal['type']}\n"
                        f"Strike: {signal['strike']}\n"
                        f"Score: {signal['score']:.1f}\n"
                        f"LTP: ₹{signal['ltp']}\n"
                        f"Reason: {signal['reason']}\n"
                        f"Spot: {underlying}"
                    )
            else:
                st.warning(f"No strong {instrument} expiry day signals detected")
            
            # Show expiry day specific data
            with st.expander(f"📊 {instrument} Expiry Day Option Chain"):
                df['ExpiryBiasScore'] = df.apply(expiry_bias_score, axis=1)
                st.dataframe(df[['strikePrice', 'ExpiryBiasScore', 'lastPrice_CE', 'lastPrice_PE', 
                               'changeinOpenInterest_CE', 'changeinOpenInterest_PE',
                               'bidQty_CE', 'bidQty_PE']])
            
            return  # Exit early after expiry day processing
            
        # Non-expiry day processing
        T = max((expiry_date - today).days, 1) / 365
        r = 0.06

        calls, puts = [], []

        for item in records:
            if 'CE' in item and item['CE']['expiryDate'] == expiry:
                ce = item['CE']
                if ce['impliedVolatility'] > 0:
                    greeks = calculate_greeks('CE', underlying, ce['strikePrice'], T, r, ce['impliedVolatility'] / 100)
                    ce.update(dict(zip(['Delta', 'Gamma', 'Vega', 'Theta', 'Rho'], greeks)))
                calls.append(ce)

            if 'PE' in item and item['PE']['expiryDate'] == expiry:
                pe = item['PE']
                if pe['impliedVolatility'] > 0:
                    greeks = calculate_greeks('PE', underlying, pe['strikePrice'], T, r, pe['impliedVolatility'] / 100)
                    pe.update(dict(zip(['Delta', 'Gamma', 'Vega', 'Theta', 'Rho'], greeks)))
                puts.append(pe)

        df_ce = pd.DataFrame(calls)
        df_pe = pd.DataFrame(puts)
        df = pd.merge(df_ce, df_pe, on='strikePrice', suffixes=('_CE', '_PE')).sort_values('strikePrice')

        # Get instrument-specific parameters
        atm_range = INSTRUMENTS['indices'].get(instrument, {}).get('atm_range', 200) or \
                    INSTRUMENTS['stocks'].get(instrument, {}).get('atm_range', 200)
        
        atm_strike = min(df['strikePrice'], key=lambda x: abs(x - underlying))
        df = df[df['strikePrice'].between(atm_strike - atm_range, atm_strike + atm_range)]
        df['Zone'] = df['strikePrice'].apply(lambda x: 'ATM' if x == atm_strike else 'ITM' if x < underlying else 'OTM')
        df['Level'] = df.apply(determine_level, axis=1)

        bias_results, total_score = [], 0
        for _, row in df.iterrows():
            if abs(row['strikePrice'] - atm_strike) > (atm_range/2):  # Only consider strikes near ATM
                continue

            score = 0
            row_data = {
                "Strike": row['strikePrice'],
                "Zone": row['Zone'],
                "Level": row['Level'],
                "ChgOI_Bias": "Bullish" if row['changeinOpenInterest_CE'] < row['changeinOpenInterest_PE'] else "Bearish",
                "Volume_Bias": "Bullish" if row['totalTradedVolume_CE'] < row['totalTradedVolume_PE'] else "Bearish",
                "Gamma_Bias": "Bullish" if row['Gamma_CE'] < row['Gamma_PE'] else "Bearish",
                "AskQty_Bias": "Bullish" if row['askQty_PE'] > row['askQty_CE'] else "Bearish",
                "BidQty_Bias": "Bearish" if row['bidQty_PE'] > row['bidQty_CE'] else "Bullish",
                "IV_Bias": "Bullish" if row['impliedVolatility_CE'] > row['impliedVolatility_PE'] else "Bearish",
                "DVP_Bias": delta_volume_bias(
                    row['lastPrice_CE'] - row['lastPrice_PE'],
                    row['totalTradedVolume_CE'] - row['totalTradedVolume_PE'],
                    row['changeinOpenInterest_CE'] - row['changeinOpenInterest_PE']
                )
            }

            for k in row_data:
                if "_Bias" in k:
                    bias = row_data[k]
                    score += weights.get(k, 1) if bias == "Bullish" else -weights.get(k, 1)

            row_data["BiasScore"] = score
            row_data["Verdict"] = final_verdict(score)
            total_score += score
            bias_results.append(row_data)

        df_summary = pd.DataFrame(bias_results)
        atm_row = df_summary[df_summary["Zone"] == "ATM"].iloc[0] if not df_summary[df_summary["Zone"] == "ATM"].empty else None
        market_view = atm_row['Verdict'] if atm_row is not None else "Neutral"
        support_zone, resistance_zone = get_support_resistance_zones(df, underlying, instrument)
        
        # Store zones in session state
        st.session_state[f'{instrument}_support_zone'] = support_zone
        st.session_state[f'{instrument}_resistance_zone'] = resistance_zone

        current_time_str = now.strftime("%H:%M:%S")
        new_row = pd.DataFrame([[current_time_str, underlying]], columns=["Time", "Spot"])
        st.session_state[f'{instrument}_price_data'] = pd.concat([st.session_state[f'{instrument}_price_data'], new_row], ignore_index=True)

        support_str = f"{support_zone[1]} to {support_zone[0]}" if all(support_zone) else "N/A"
        resistance_str = f"{resistance_zone[0]} to {resistance_zone[1]}" if all(resistance_zone) else "N/A"

        atm_signal, suggested_trade = "No Signal", ""
        signal_sent = False

        for row in bias_results:
            if not is_in_zone(underlying, row['Strike'], row['Level'], instrument):
                continue

            if row['Level'] == "Support" and total_score >= 4 and "Bullish" in market_view:
                option_type = 'CE'
            elif row['Level'] == "Resistance" and total_score <= -4 and "Bearish" in market_view:
                option_type = 'PE'
            else:
                continue

            ltp = df.loc[df['strikePrice'] == row['Strike'], f'lastPrice_{option_type}'].values[0]
            iv = df.loc[df['strikePrice'] == row['Strike'], f'impliedVolatility_{option_type}'].values[0]
            target = round(ltp * (1 + iv / 100), 2)
            stop_loss = round(ltp * 0.8, 2)

            atm_signal = f"{'CALL' if option_type == 'CE' else 'PUT'} Entry (Bias Based at {row['Level']})"
            suggested_trade = f"Strike: {row['Strike']} {option_type} @ ₹{ltp} | 🎯 Target: ₹{target} | 🛑 SL: ₹{stop_loss}"

            send_telegram_message(
                f"📍 {instrument} Spot: {underlying}\n"
                f"🔹 {atm_signal}\n"
                f"{suggested_trade}\n"
                f"Bias Score (ATM ±2): {total_score} ({market_view})\n"
                f"Level: {row['Level']}\n"
                f"📉 Support Zone: {support_str}\n"
                f"📈 Resistance Zone: {resistance_str}\n"
                f"Biases:\n"
                f"Strike: {row['Strike']}\n"
                f"ChgOI: {row['ChgOI_Bias']}, Volume: {row['Volume_Bias']}, Gamma: {row['Gamma_Bias']},\n"
                f"AskQty: {row['AskQty_Bias']}, BidQty: {row['BidQty_Bias']}, IV: {row['IV_Bias']}, DVP: {row['DVP_Bias']}"
            )

            st.session_state[f'{instrument}_trade_log'].append({
                "Time": now.strftime("%H:%M:%S"),
                "Strike": row['Strike'],
                "Type": option_type,
                "LTP": ltp,
                "Target": target,
                "SL": stop_loss
            })

            signal_sent = True
            break

        # === Main Display ===
        st.markdown(f"### 📍 {instrument} Spot Price: {underlying}")
        st.success(f"🧠 {instrument} Market View: **{market_view}** Bias Score: {total_score}")
        st.markdown(f"### 🛡️ {instrument} Support Zone: `{support_str}`")
        st.markdown(f"### 🚧 {instrument} Resistance Zone: `{resistance_str}`")
        
        # Display price chart
        plot_price_with_sr(instrument)

        if suggested_trade:
            st.info(f"🔹 {atm_signal}\n{suggested_trade}")
        
        with st.expander(f"📊 {instrument} Option Chain Summary"):
            st.dataframe(df_summary)
        
        if st.session_state[f'{instrument}_trade_log']:
            st.markdown(f"### 📜 {instrument} Trade Log")
            st.dataframe(pd.DataFrame(st.session_state[f'{instrument}_trade_log']))

        # === Enhanced Functions Display ===
        st.markdown("---")
        st.markdown(f"## 📈 {instrument} Enhanced Features")
        
        # Enhanced Trade Log
        display_enhanced_trade_log(instrument)
        
        # Export functionality
        st.markdown("---")
        st.markdown(f"### 📥 {instrument} Data Export")
        handle_export_data(df_summary, underlying, instrument)
        
        # Call Log Book
        st.markdown("---")
        display_call_log_book(instrument)
        
        # Auto update call log with current price
        auto_update_call_log(underlying, instrument)

    except Exception as e:
        st.error(f"❌ {instrument} Error: {e}")
        send_telegram_message(f"❌ {instrument} Error: {str(e)}")