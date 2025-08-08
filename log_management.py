import streamlit as st
import pandas as pd
from datetime import datetime
from pytz import timezone

def auto_update_call_log(current_price, instrument):
    for call in st.session_state[f'{instrument}_call_log_book']:
        if call["Status"] != "Active":
            continue
        if call["Type"] == "CE":
            if current_price >= max(call["Targets"].values()):
                call["Status"] = "Hit Target"
                call["Hit_Target"] = True
                call["Exit_Time"] = datetime.now(timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")
                call["Exit_Price"] = current_price
            elif current_price <= call["Stoploss"]:
                call["Status"] = "Hit Stoploss"
                call["Hit_Stoploss"] = True
                call["Exit_Time"] = datetime.now(timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")
                call["Exit_Price"] = current_price
        elif call["Type"] == "PE":
            if current_price <= min(call["Targets"].values()):
                call["Status"] = "Hit Target"
                call["Hit_Target"] = True
                call["Exit_Time"] = datetime.now(timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")
                call["Exit_Price"] = current_price
            elif current_price >= call["Stoploss"]:
                call["Status"] = "Hit Stoploss"
                call["Hit_Stoploss"] = True
                call["Exit_Time"] = datetime.now(timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")
                call["Exit_Price"] = current_price

def display_call_log_book(instrument):
    st.markdown(f"### 📚 {instrument} Call Log Book")
    if not st.session_state[f'{instrument}_call_log_book']:
        st.info(f"No {instrument} calls have been made yet.")
        return
    
    df_log = pd.DataFrame(st.session_state[f'{instrument}_call_log_book'])
    st.dataframe(df_log, use_container_width=True)
    
    if st.button(f"Download {instrument} Call Log Book as CSV"):
        st.download_button(
            label="Download CSV",
            data=df_log.to_csv(index=False).encode(),
            file_name=f"{instrument.lower()}_call_log_book.csv",
            mime="text/csv"
        )