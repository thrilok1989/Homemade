# Utility functions for NSE Options Analyzer

import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def get_env_variable(var_name, default_value=None):
    """Get environment variable with fallback"""
    return os.getenv(var_name, default_value)

def is_market_open():
    """Check if market is currently open"""
    now = datetime.now()
    current_day = now.weekday()  # 0 = Monday, 6 = Sunday
    current_time = now.time()
    
    # Market closed on weekends
    if current_day >= 5:
        return False
    
    # Market hours: 9:00 AM to 3:40 PM
    market_start = datetime.strptime("09:00", "%H:%M").time()
    market_end = datetime.strptime("15:40", "%H:%M").time()
    
    return market_start <= current_time <= market_end

def format_currency(amount, currency="₹"):
    """Format currency with proper comma separation"""
    return f"{currency}{amount:,.2f}"

def calculate_percentage_change(current, previous):
    """Calculate percentage change"""
    if previous == 0:
        return 0
    return ((current - previous) / previous) * 100

def validate_strike_price(strike, spot_price, max_deviation_percent=50):
    """Validate if strike price is reasonable"""
    max_deviation = spot_price * (max_deviation_percent / 100)
    return abs(strike - spot_price) <= max_deviation

def sanitize_filename(filename):
    """Remove invalid characters from filename"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def get_next_expiry_dates(current_date, num_expiries=3):
    """Get next expiry dates (typically Thursdays)"""
    # This is a simplified version - actual implementation would use NSE calendar
    expiries = []
    current = current_date
    
    # Find next Thursdays
    days_ahead = (3 - current.weekday()) % 7  # Thursday is 3
    if days_ahead == 0:  # Today is Thursday
        days_ahead = 7
    
    for i in range(num_expiries):
        next_expiry = current + datetime.timedelta(days=days_ahead + (i * 7))
        expiries.append(next_expiry.strftime("%d-%b-%Y"))
    
    return expiries

def health_check():
    """Perform basic health checks"""
    checks = {
        'market_open': is_market_open(),
        'env_loaded': bool(os.getenv('TELEGRAM_BOT_TOKEN')),
        'timestamp': datetime.now().isoformat()
    }
    return checks

# Constants
MARKET_HOLIDAYS_2024 = [
    '2024-01-26',  # Republic Day
    '2024-03-08',  # Holi
    '2024-03-29',  # Good Friday
    '2024-04-11',  # Eid ul Fitr
    '2024-04-17',  # Ram Navami
    '2024-05-01',  # Maharashtra Day
    '2024-06-17',  # Eid ul Adha
    '2024-08-15',  # Independence Day
    '2024-10-02',  # Gandhi Jayanti
    '2024-11-01',  # Diwali
    '2024-11-15',  # Guru Nanak Jayanti
    '2024-12-25',  # Christmas
]

def is_market_holiday(date_str):
    """Check if given date is a market holiday"""
    return date_str in MARKET_HOLIDAYS_2024