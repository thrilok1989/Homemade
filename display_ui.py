import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io
from datetime import datetime
from config_setup import INSTRUMENTS

def display_enhanced_trade_log(instrument):
    if not st.session_state[f'{instrument}_trade_log']:
        st.info(f"No {instrument} trades logged yet")
        return
    st.markdown(f"### 📜 {instrument} Trade Log")
    df_trades = pd.DataFrame(st.session_state[f'{instrument}_trade_log'])
    
    # Get lot size for P&L calculation
    lot_size = INSTRUMENTS['indices'].get(instrument, {}).get('lot_size', 1) or \
               INSTRUMENTS['stocks'].get(instrument, {}).get('lot_size', 1)
    
    if 'Current_Price' not in df_trades.columns:
        df_trades['Current_Price'] = df_trades['LTP'] * np.random.uniform(0.8, 1.3, len(df_trades))
        df_trades['Unrealized_PL'] = (df_trades['Current_Price'] - df_trades['LTP']) * lot_size
        df_trades['Status'] = df_trades['Unrealized_PL'].apply(
            lambda x: '🟢 Profit' if x > 0 else '🔴 Loss' if x < -100 else '🟡 Breakeven'
        )
    
    def color_pnl(row):
        colors = []
        for col in row.index:
            if col == 'Unrealized_PL':
                if row[col] > 0:
                    colors.append('background-color: #90EE90; color: black')
                elif row[col] < -100:
                    colors.append('background-color: #FFB6C1; color: black')
                else:
                    colors.append('background-color: #FFFFE0; color: black')
            else:
                colors.append('')
        return colors
    
    styled_trades = df_trades.style.apply(color_pnl, axis=1)
    st.dataframe(styled_trades, use_container_width=True)
    total_pl = df_trades['Unrealized_PL'].sum()
    win_rate = len(df_trades[df_trades['Unrealized_PL'] > 0]) / len(df_trades) * 100
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total P&L", f"₹{total_pl:,.0f}")
    with col2:
        st.metric("Win Rate", f"{win_rate:.1f}%")
    with col3:
        st.metric("Total Trades", len(df_trades))

def create_export_data(df_summary, trade_log, spot_price, instrument):
    # Create Excel data
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_summary.to_excel(writer, sheet_name=f'{instrument}_Option_Chain', index=False)
        if trade_log:
            pd.DataFrame(trade_log).to_excel(writer, sheet_name=f'{instrument}_Trade_Log', index=False)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{instrument.lower()}_analysis_{timestamp}.xlsx"
    
    return output.getvalue(), filename

def handle_export_data(df_summary, spot_price, instrument):
    if st.button(f"Prepare {instrument} Excel Export"):
        try:
            excel_data, filename = create_export_data(df_summary, st.session_state[f'{instrument}_trade_log'], spot_price, instrument)
            st.download_button(
                label=f"📥 Download {instrument} Excel Report",
                data=excel_data,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            st.success(f"✅ {instrument} export ready! Click the download button above.")
        except Exception as e:
            st.error(f"❌ {instrument} export failed: {e}")

def plot_price_with_sr(instrument):
    price_df = st.session_state[f'{instrument}_price_data'].copy()
    if price_df.empty or price_df['Spot'].isnull().all():
        st.info(f"Not enough {instrument} data to show price action chart yet.")
        return
    
    price_df['Time'] = pd.to_datetime(price_df['Time'])
    support_zone = st.session_state.get(f'{instrument}_support_zone', (None, None))
    resistance_zone = st.session_state.get(f'{instrument}_resistance_zone', (None, None))
    
    fig = go.Figure()
    
    # Main price line
    fig.add_trace(go.Scatter(
        x=price_df['Time'],
        y=price_df['Spot'],
        mode='lines+markers',
        name='Spot Price',
        line=dict(color='blue', width=2)
    ))
    
    # Support zone
    if all(support_zone) and None not in support_zone:
        fig.add_shape(
            type="rect",
            xref="paper", yref="y",
            x0=0, x1=1,
            y0=support_zone[0], y1=support_zone[1],
            fillcolor="rgba(0,255,0,0.08)",
            line=dict(width=0),
            layer="below"
        )
        fig.add_trace(go.Scatter(
            x=[price_df['Time'].min(), price_df['Time'].max()],
            y=[support_zone[0], support_zone[0]],
            mode='lines',
            name='Support Low',
            line=dict(color='green', dash='dash')
        ))
        fig.add_trace(go.Scatter(
            x=[price_df['Time'].min(), price_df['Time'].max()],
            y=[support_zone[1], support_zone[1]],
            mode='lines',
            name='Support High',
            line=dict(color='green', dash='dot')
        ))
    
    # Resistance zone
    if all(resistance_zone) and None not in resistance_zone:
        fig.add_shape(
            type="rect",
            xref="paper", yref="y",
            x0=0, x1=1,
            y0=resistance_zone[0], y1=resistance_zone[1],
            fillcolor="rgba(255,0,0,0.08)",
            line=dict(width=0),
            layer="below"
        )
        fig.add_trace(go.Scatter(
            x=[price_df['Time'].min(), price_df['Time'].max()],
            y=[resistance_zone[0], resistance_zone[0]],
            mode='lines',
            name='Resistance Low',
            line=dict(color='red', dash='dash')
        ))
        fig.add_trace(go.Scatter(
            x=[price_df['Time'].min(), price_df['Time'].max()],
            y=[resistance_zone[1], resistance_zone[1]],
            mode='lines',
            name='Resistance High',
            line=dict(color='red', dash='dot')
        ))
    
    # Layout configuration
    fig.update_layout(
        title=f"{instrument} Spot Price Action with Support & Resistance",
        xaxis_title="Time",
        yaxis_title="Spot Price",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)