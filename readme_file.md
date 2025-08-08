# 📊 NSE Options Analyzer

A comprehensive real-time options analysis tool for NSE (National Stock Exchange) indices and stocks with automated signal generation, support/resistance detection, and Telegram alerts.

## 🚀 Features

- **Real-time Options Data**: Live data from NSE API
- **Multi-instrument Support**: NIFTY, BANKNIFTY, NIFTY IT, NIFTY AUTO, TCS, RELIANCE, HDFCBANK
- **Greeks Calculation**: Delta, Gamma, Vega, Theta, Rho
- **Support/Resistance Detection**: Automated zone identification
- **Expiry Day Analysis**: Specialized logic for expiry day trading
- **Bias Analysis**: Multiple bias indicators with weighted scoring
- **Trade Logging**: Enhanced P&L tracking with win rate analysis
- **Data Export**: Excel export functionality
- **Telegram Alerts**: Real-time signal notifications
- **Interactive Charts**: Plotly-based price action with S&R zones

## 📁 Project Structure

```
NSE-Options-Analyzer/
├── config_setup.py          # Configuration & Setup
├── core_calculations.py     # Core calculation functions
├── support_resistance.py    # Support & Resistance analysis
├── expiry_analysis.py       # Expiry day analysis
├── display_ui.py           # Display & UI functions
├── log_management.py       # Log management functions
├── main_analysis.py        # Main analysis engine
├── master_app.py          # Master application file
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables example
├── .gitignore           # Git ignore file
└── README.md           # This file
```

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd NSE-Options-Analyzer
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Telegram (Optional)**
   - Copy `.env.example` to `.env`
   - Add your Telegram Bot Token and Chat ID
   - Or modify `config_setup.py` directly

## 🚀 Usage

**Run the application:**
```bash
streamlit run master_app.py
```

**Access the app:**
- Open browser to `http://localhost:8501`
- Navigate through Indices/Stocks tabs
- Select specific instruments for analysis

## 📊 Analysis Features

### Bias Analysis
- **ChgOI Bias**: Change in Open Interest analysis
- **Volume Bias**: Trading volume patterns
- **Gamma Bias**: Gamma exposure analysis
- **Ask/Bid Qty Bias**: Order book analysis
- **IV Bias**: Implied Volatility comparison
- **DVP Bias**: Delta-Volume-Price relationship

### Signal Generation
- **Regular Days**: Bias-based entry signals
- **Expiry Days**: Specialized expiry day analysis
- **Support/Resistance**: Zone-based entries
- **Auto-targeting**: IV-based target calculation

### Data Export
- Excel reports with option chain data
- Trade log export with P&L tracking
- CSV download for call log books

## ⚙️ Configuration

### Instrument Settings
Modify `INSTRUMENTS` dictionary in `config_setup.py`:
```python
INSTRUMENTS = {
    'indices': {
        'NIFTY': {'lot_size': 75, 'zone_size': 20, 'atm_range': 200}
    },
    'stocks': {
        'TCS': {'lot_size': 150, 'zone_size': 30, 'atm_range': 150}
    }
}
```

### Telegram Configuration
1. Create bot via @BotFather
2. Get Chat ID from @userinfobot
3. Update `config_setup.py` or use environment variables

## 📈 Trading Logic

### Entry Conditions
- **Bullish**: Support zone + Positive bias score (≥4)
- **Bearish**: Resistance zone + Negative bias score (≤-4)
- **Expiry Day**: Specialized scoring with OI unwind analysis

### Risk Management
- **Stop Loss**: 20% of entry price
- **Target**: IV-adjusted target calculation
- **Position Sizing**: Based on lot sizes

## 🕒 Market Hours
- **Active**: Monday-Friday, 9:00 AM - 3:40 PM IST
- **Auto-refresh**: Every 2 minutes
- **Expiry Detection**: Automatic expiry day identification

## 🔧 Troubleshooting

### Common Issues
1. **Import Errors**: Ensure all files are in same directory
2. **NSE API Errors**: Check internet connection and NSE website status
3. **Telegram Failures**: Verify bot token and chat ID
4. **Data Loading**: Wait for market hours or check instrument names

### Performance Tips
- Close unused tabs to reduce API calls
- Use specific instrument tabs instead of all at once
- Clear browser cache if charts don't load

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## ⚠️ Disclaimer

This tool is for educational and analysis purposes only. It is not financial advice. Trading in options involves substantial risk and may not be suitable for all investors. Always consult with a qualified financial advisor before making investment decisions.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support, email support@example.com or create an issue in the GitHub repository.

---

**Happy Trading! 📈**