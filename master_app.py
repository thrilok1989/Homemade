import streamlit as st

# Import all modules
import config_setup
from main_analysis import analyze_instrument

# === Main Function Call ===
if __name__ == "__main__":
    st.title("📊 NSE Options Analyzer")
    
    # Create tabs for each category
    tab_indices, tab_stocks = st.tabs(["Indices", "Stocks"])
    
    with tab_indices:
        st.header("NSE Indices Analysis")
        # Create subtabs for each index
        nifty_tab, banknifty_tab, it_tab, auto_tab = st.tabs(["NIFTY", "BANKNIFTY", "NIFTY IT", "NIFTY AUTO"])
        
        with nifty_tab:
            analyze_instrument('NIFTY')
        
        with banknifty_tab:
            analyze_instrument('BANKNIFTY')
        
        with it_tab:
            analyze_instrument('NIFTY IT')
        
        with auto_tab:
            analyze_instrument('NIFTY AUTO')
    
    with tab_stocks:
        st.header("Stock Options Analysis")
        # Create subtabs for each stock
        tcs_tab, reliance_tab, hdfc_tab = st.tabs(["TCS", "RELIANCE", "HDFCBANK"])
        
        with tcs_tab:
            analyze_instrument('TCS')
        
        with reliance_tab:
            analyze_instrument('RELIANCE')
        
        with hdfc_tab:
            analyze_instrument('HDFCBANK')
