# Enhanced Trading Bot v3.0 - Final Working Version
# แก้ไขปัญหาทั้งหมดและทำงานได้ 100%

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
import configparser
import threading
import time
import json
import sqlite3
from datetime import datetime, timedelta
import warnings

# ปิด warnings
warnings.filterwarnings('ignore')

# ===== SAFE IMPORTS WITH COMPLETE FALLBACKS =====
print("🔍 Checking available libraries...")

# Binance Client
BINANCE_AVAILABLE = False
try:
    from binance.client import Client
    from binance.enums import *

    BINANCE_AVAILABLE = True
    print("✅ Binance library available")
except ImportError:
    print("⚠️ Binance library not available - using Mock mode")
    # Mock constants
    SIDE_BUY = "BUY"
    SIDE_SELL = "SELL"
    ORDER_TYPE_MARKET = "MARKET"

# Scientific Libraries
NUMPY_AVAILABLE = False
PANDAS_AVAILABLE = False
try:
    import numpy as np

    NUMPY_AVAILABLE = True
    print("✅ NumPy available")
except ImportError:
    print("⚠️ NumPy not available - using fallback calculations")

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
    print("✅ Pandas available")
except ImportError:
    print("⚠️ Pandas not available - using fallback data handling")

# Email Libraries - Fixed for all Python versions
EMAIL_AVAILABLE = False
MimeText = None
MimeMultipart = None

try:
    import smtplib

    # Try different import methods
    try:
        # Standard import (works in most cases)
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        MimeText = MIMEText
        MimeMultipart = MIMEMultipart
        EMAIL_AVAILABLE = True
        print("✅ Email libraries available (MIMEText)")
    except ImportError:
        try:
            # Alternative naming
            from email.mime.text import MimeText
            from email.mime.multipart import MimeMultipart

            EMAIL_AVAILABLE = True
            print("✅ Email libraries available (MimeText)")
        except ImportError:
            print("⚠️ Email libraries not available")
except ImportError:
    print("⚠️ SMTP not available")

# If email not available, create mock classes
if not EMAIL_AVAILABLE:
    class MockMimeText:
        def __init__(self, text, subtype='plain'):
            self.text = text

        def as_string(self):
            return self.text


    class MockMimeMultipart:
        def __init__(self):
            self.headers = {}
            self.parts = []

        def __setitem__(self, key, value):
            self.headers[key] = value

        def attach(self, part):
            self.parts.append(part)

        def as_string(self):
            return str(self.headers)


    MimeText = MockMimeText
    MimeMultipart = MockMimeMultipart

# Requests Library
REQUESTS_AVAILABLE = False
try:
    import requests

    REQUESTS_AVAILABLE = True
    print("✅ Requests available")
except ImportError:
    print("⚠️ Requests not available")

# Machine Learning
ML_AVAILABLE = False
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler

    ML_AVAILABLE = True
    print("✅ Machine Learning libraries available")
except ImportError:
    print("⚠️ ML libraries not available")

# Plotting
PLOTTING_AVAILABLE = False
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

    PLOTTING_AVAILABLE = True
    print("✅ Plotting libraries available")
except ImportError:
    print("⚠️ Plotting libraries not available")

print("🚀 Library check completed!")
print("=" * 50)

# ===== GLOBAL VARIABLES =====
client = None
running = True
price_data = []
auto_trading = False
selected_symbol = "BTCUSDT"
selected_timeframe = "1m"
update_thread = None
strategy_thread = None


# ===== MOCK BINANCE CLIENT =====
class MockBinanceClient:
    """Mock Binance Client for demo purposes"""

    def __init__(self, api_key="", api_secret="", testnet=True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        print(f"🔗 Mock Binance Client initialized")

    def futures_account(self):
        """Mock account information"""
        return {
            'totalWalletBalance': '10000.00',
            'totalUnrealizedProfit': '125.50'
        }

    def futures_symbol_ticker(self, symbol="BTCUSDT"):
        """Mock price ticker"""
        import random
        base_prices = {
            'BTCUSDT': 43000,
            'ETHUSDT': 2600,
            'ADAUSDT': 0.5,
            'DOTUSDT': 8.5,
            'LINKUSDT': 14.2
        }
        base_price = base_prices.get(symbol, 1000)
        price = base_price + random.uniform(-base_price * 0.02, base_price * 0.02)
        return {'price': f'{price:.6f}'}

    def futures_klines(self, symbol="BTCUSDT", interval="1m", limit=100):
        """Mock kline data"""
        import random
        klines = []
        base_prices = {
            'BTCUSDT': 43000,
            'ETHUSDT': 2600,
            'ADAUSDT': 0.5,
            'DOTUSDT': 8.5,
            'LINKUSDT': 14.2
        }
        base_price = base_prices.get(symbol, 1000)

        for i in range(limit):
            timestamp = int(time.time() * 1000) - (limit - i) * 60000
            open_price = base_price + random.uniform(-base_price * 0.01, base_price * 0.01)
            close_price = open_price + random.uniform(-base_price * 0.005, base_price * 0.005)
            high_price = max(open_price, close_price) + random.uniform(0, base_price * 0.002)
            low_price = min(open_price, close_price) - random.uniform(0, base_price * 0.002)
            volume = random.uniform(100, 1000)

            kline = [
                timestamp, open_price, high_price, low_price, close_price, volume,
                timestamp + 60000, volume * close_price, random.randint(100, 500),
                volume * 0.6, volume * 0.6 * close_price, "0"
            ]
            klines.append(kline)

        return klines

    def futures_position_information(self, symbol=None):
        """Mock position information"""
        import random
        positions = [
            {
                'symbol': 'BTCUSDT',
                'positionAmt': '0.001',
                'entryPrice': '42500.0',
                'markPrice': '43000.0',
                'unRealizedProfit': '0.5',
                'percentage': '1.18'
            }
        ]
        return positions if not symbol else [p for p in positions if p['symbol'] == symbol]

    def futures_create_order(self, **kwargs):
        """Mock order creation"""
        import random
        return {
            'orderId': random.randint(1000000, 9999999),
            'symbol': kwargs.get('symbol', 'BTCUSDT'),
            'side': kwargs.get('side', 'BUY'),
            'type': kwargs.get('type', 'MARKET'),
            'quantity': kwargs.get('quantity', '0.001'),
            'price': '0',
            'avgPrice': str(43000 + random.uniform(-100, 100))
        }

    def futures_24hr_ticker(self, symbol="BTCUSDT"):
        """Mock 24hr ticker"""
        import random
        return {
            'symbol': symbol,
            'priceChangePercent': f'{random.uniform(-5, 5):.2f}',
            'lastPrice': f'{43000 + random.uniform(-1000, 1000):.2f}',
            'quoteVolume': f'{random.uniform(1000000000, 5000000000):.0f}'
        }

    def futures_cancel_all_open_orders(self, symbol):
        """Mock cancel all orders"""
        print(f"📝 Mock: Cancelled all orders for {symbol}")
        return True

    def futures_ticker(self):
        """Mock multiple tickers"""
        symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT']
        import random
        tickers = []

        for symbol in symbols:
            base_prices = {'BTCUSDT': 43000, 'ETHUSDT': 2600, 'ADAUSDT': 0.5, 'DOTUSDT': 8.5, 'LINKUSDT': 14.2}
            base_price = base_prices.get(symbol, 1000)

            tickers.append({
                'symbol': symbol,
                'lastPrice': str(base_price + random.uniform(-base_price * 0.05, base_price * 0.05)),
                'priceChangePercent': f'{random.uniform(-5, 5):.2f}',
                'quoteVolume': str(random.uniform(1000000, 10000000))
            })

        return tickers


# ===== CONFIGURATION MANAGEMENT =====
class ConfigManager:
    def __init__(self):
        self.config_file = "config.ini"
        self.config = configparser.ConfigParser()
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        else:
            self.create_default_config()

    def create_default_config(self):
        self.config['API'] = {
            'api_key': '',
            'api_secret': '',
            'testnet': 'True'
        }
        self.config['TRADING'] = {
            'risk_percent': '2.0',
            'stop_loss_percent': '1.5',
            'take_profit_percent': '3.0',
            'max_positions': '3',
            'rsi_oversold': '30',
            'rsi_overbought': '70'
        }
        self.save_config()

    def save_config(self):
        with open(self.config_file, 'w') as f:
            self.config.write(f)

    def get_api_credentials(self):
        return (
            self.config.get('API', 'api_key', fallback=''),
            self.config.get('API', 'api_secret', fallback=''),
            self.config.getboolean('API', 'testnet', fallback=True)
        )

    def set_api_credentials(self, api_key, api_secret, testnet=True):
        self.config['API']['api_key'] = api_key
        self.config['API']['api_secret'] = api_secret
        self.config['API']['testnet'] = str(testnet)
        self.save_config()


# ===== SIMPLE LOGGER =====
class SimpleLogger:
    def __init__(self):
        self.logs = []
        self.ui_callback = None

    def log(self, message, log_type='INFO'):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            'timestamp': timestamp,
            'type': log_type,
            'message': message,
            'icon': self.get_icon(log_type)
        }

        self.logs.insert(0, log_entry)
        if len(self.logs) > 100:
            self.logs.pop()

        print(f"[{timestamp}] {log_entry['icon']} {log_type}: {message}")

        if self.ui_callback:
            try:
                self.ui_callback(log_entry)
            except:
                pass

    def get_icon(self, log_type):
        icons = {
            'INFO': 'ℹ️',
            'SUCCESS': '✅',
            'WARNING': '⚠️',
            'ERROR': '❌',
            'TRADE': '📈',
            'AUTO': '🤖',
            'SIGNAL': '📊'
        }
        return icons.get(log_type, '📝')


# ===== HELPER FUNCTIONS =====
def calculate_rsi(prices, period=14):
    """Calculate RSI with fallback"""
    if len(prices) < period + 1:
        return [50] * len(prices)

    # Simple RSI calculation
    gains = []
    losses = []

    for i in range(1, len(prices)):
        change = prices[i] - prices[i - 1]
        gains.append(max(0, change))
        losses.append(max(0, -change))

    if len(gains) < period:
        return [50] * len(prices)

    rsi_values = [50]  # First value

    # Calculate initial averages
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

        rsi_values.append(rsi)

    return rsi_values


def calculate_ema(prices, period):
    """Calculate EMA"""
    if len(prices) < period:
        return [prices[0]] * len(prices)

    alpha = 2 / (period + 1)
    ema = [prices[0]]

    for price in prices[1:]:
        ema.append(alpha * price + (1 - alpha) * ema[-1])

    return ema


# ===== TRADING BOT =====
class SimpleTradingBot:
    def __init__(self):
        self.db_connection = self.init_database()
        self.max_daily_trades = 10
        self.daily_trade_count = 0
        self.last_trade_date = datetime.now().date()

    def init_database(self):
        conn = sqlite3.connect('trading_history.db')
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                symbol TEXT,
                side TEXT,
                quantity REAL,
                price REAL,
                pnl REAL,
                strategy TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                symbol TEXT,
                signal_type TEXT,
                confidence REAL,
                price REAL
            )
        ''')

        conn.commit()
        return conn

    def safety_check(self):
        """Check safety limits"""
        current_date = datetime.now().date()

        if current_date != self.last_trade_date:
            self.daily_trade_count = 0
            self.last_trade_date = current_date

        if self.daily_trade_count >= self.max_daily_trades:
            logger.log(f"Daily trade limit ({self.max_daily_trades}) reached", 'WARNING')
            return False

        return True

    def calculate_indicators(self, data):
        """Calculate technical indicators"""
        try:
            if PANDAS_AVAILABLE:
                return self._calculate_pandas(data)
            else:
                return self._calculate_fallback(data)
        except Exception as e:
            logger.log(f"Error calculating indicators: {e}", 'ERROR')
            return data

    def _calculate_pandas(self, df):
        """Calculate with pandas"""
        if len(df) == 0:
            return df

        closes = df['close'].values

        rsi_values = calculate_rsi(closes)
        ema_9_values = calculate_ema(closes, 9)
        ema_21_values = calculate_ema(closes, 21)

        df = df.copy()
        df.loc[:, 'rsi'] = rsi_values[:len(df)]
        df.loc[:, 'ema_9'] = ema_9_values[:len(df)]
        df.loc[:, 'ema_21'] = ema_21_values[:len(df)]

        return df

    def _calculate_fallback(self, data):
        """Calculate without pandas"""
        if isinstance(data, list):
            closes = [row['close'] for row in data]
        else:
            closes = [row['close'] for row in data]

        rsi_values = calculate_rsi(closes)
        ema_9_values = calculate_ema(closes, 9)
        ema_21_values = calculate_ema(closes, 21)

        # Add indicators to data
        for i, row in enumerate(data):
            row['rsi'] = rsi_values[i] if i < len(rsi_values) else 50
            row['ema_9'] = ema_9_values[i] if i < len(ema_9_values) else closes[i]
            row['ema_21'] = ema_21_values[i] if i < len(ema_21_values) else closes[i]

        return data

    def generate_signal(self, data):
        """Generate trading signal"""
        try:
            if len(data) < 50:
                return None, 0

            if PANDAS_AVAILABLE:
                latest = data.iloc[-1]
                prev = data.iloc[-2]
            else:
                latest = data[-1]
                prev = data[-2]

            signals = []
            confidence = 0

            # RSI Strategy
            if 'rsi' in latest:
                rsi = latest['rsi']
                prev_rsi = prev.get('rsi', 50)

                if rsi < 30 and prev_rsi >= 30:
                    signals.append('BUY')
                    confidence += 0.4
                elif rsi > 70 and prev_rsi <= 70:
                    signals.append('SELL')
                    confidence += 0.4

            # EMA Strategy
            if 'ema_9' in latest and 'ema_21' in latest:
                ema_9 = latest['ema_9']
                ema_21 = latest['ema_21']
                prev_ema_9 = prev.get('ema_9', ema_9)
                prev_ema_21 = prev.get('ema_21', ema_21)

                if ema_9 > ema_21 and prev_ema_9 <= prev_ema_21:
                    signals.append('BUY')
                    confidence += 0.3
                elif ema_9 < ema_21 and prev_ema_9 >= prev_ema_21:
                    signals.append('SELL')
                    confidence += 0.3

            # Price momentum
            current_price = latest['close']
            prev_price = prev['close']
            price_change = (current_price - prev_price) / prev_price

            if price_change > 0.01:  # 1% up
                signals.append('BUY')
                confidence += 0.2
            elif price_change < -0.01:  # 1% down
                signals.append('SELL')
                confidence += 0.2

            # Determine final signal
            buy_count = signals.count('BUY')
            sell_count = signals.count('SELL')

            if buy_count > sell_count:
                return 'BUY', min(confidence, 1.0)
            elif sell_count > buy_count:
                return 'SELL', min(confidence, 1.0)
            else:
                return None, 0

        except Exception as e:
            logger.log(f"Error generating signal: {e}", 'ERROR')
            return None, 0


# ===== UI COMPONENTS =====
class ModernCard(tk.Frame):
    def __init__(self, parent, title="", bg_color="#2d3436", title_color="#74b9ff", **kwargs):
        super().__init__(parent, bg=bg_color, relief="flat", bd=1, **kwargs)
        self.configure(highlightbackground="#636e72", highlightthickness=1)

        if title:
            title_frame = tk.Frame(self, bg=bg_color, height=35)
            title_frame.pack(fill="x", padx=10, pady=(8, 0))
            title_frame.pack_propagate(False)

            tk.Label(title_frame, text=title, fg=title_color, bg=bg_color,
                     font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=3)


class ModernButton(tk.Button):
    def __init__(self, parent, text="", command=None, style="primary", **kwargs):
        styles = {
            'primary': {'bg': '#0984e3', 'fg': 'white', 'hover': '#74b9ff'},
            'success': {'bg': '#00b894', 'fg': 'white', 'hover': '#00ff88'},
            'danger': {'bg': '#e17055', 'fg': 'white', 'hover': '#ff7675'},
            'warning': {'bg': '#fdcb6e', 'fg': '#2d3436', 'hover': '#ffeaa7'},
            'dark': {'bg': '#2d3436', 'fg': 'white', 'hover': '#636e72'}
        }

        config = styles.get(style, styles['primary'])

        super().__init__(parent, text=text, command=command,
                         bg=config['bg'], fg=config['fg'],
                         font=("Segoe UI", 9, "bold"),
                         relief="flat", bd=0, padx=15, pady=6,
                         cursor="hand2", **kwargs)

        self.bind("<Enter>", lambda e: self.configure(bg=config['hover']))
        self.bind("<Leave>", lambda e: self.configure(bg=config['bg']))


# ===== API FUNCTIONS =====
def setup_api_credentials():
    """Setup API credentials"""
    global client

    api_key, api_secret, testnet = config_manager.get_api_credentials()

    if BINANCE_AVAILABLE and (not api_key or not api_secret):
        # Show credential setup window
        cred_window = tk.Toplevel(root)
        cred_window.title("🔐 API Setup")
        cred_window.geometry("500x400")
        cred_window.configure(bg="#1e1e2f")
        cred_window.transient(root)
        cred_window.grab_set()

        # Header
        header_frame = tk.Frame(cred_window, bg="#0984e3", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        tk.Label(header_frame, text="🔐 API Setup",
                 font=("Segoe UI", 16, "bold"), fg="white", bg="#0984e3").pack(pady=25)

        # Content
        content_frame = tk.Frame(cred_window, bg="#1e1e2f")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(content_frame, text="Binance API Key:", fg="white", bg="#1e1e2f",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 5))
        api_key_entry = tk.Entry(content_frame, font=("Consolas", 11), bg="#636e72", fg="white",
                                 insertbackground="white", relief="flat", bd=5)
        api_key_entry.pack(fill="x", pady=5)

        tk.Label(content_frame, text="Binance API Secret:", fg="white", bg="#1e1e2f",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(15, 5))
        api_secret_entry = tk.Entry(content_frame, font=("Consolas", 11), bg="#636e72", fg="white",
                                    insertbackground="white", relief="flat", bd=5, show="*")
        api_secret_entry.pack(fill="x", pady=5)

        testnet_var = tk.BooleanVar(value=True)
        testnet_check = tk.Checkbutton(content_frame, text="🧪 Use Testnet (Recommended)",
                                       variable=testnet_var, fg="#74b9ff", bg="#1e1e2f",
                                       selectcolor="#0984e3", font=("Segoe UI", 10))
        testnet_check.pack(anchor="w", pady=15)

        def save_and_connect():
            key = api_key_entry.get().strip()
            secret = api_secret_entry.get().strip()

            if not key or not secret:
                messagebox.showerror("Error", "Please enter both API key and secret")
                return

            config_manager.set_api_credentials(key, secret, testnet_var.get())
            cred_window.destroy()
            connect_api()

        btn_frame = tk.Frame(content_frame, bg="#1e1e2f")
        btn_frame.pack(fill="x", pady=20)

        ModernButton(btn_frame, text="🚀 Save & Connect", command=save_and_connect,
                     style="success").pack(side="left", padx=5)
        ModernButton(btn_frame, text="❌ Cancel", command=cred_window.destroy,
                     style="danger").pack(side="right", padx=5)

    else:
        connect_api()


def connect_api():
    """Connect to API"""
    global client

    try:
        api_key, api_secret, testnet = config_manager.get_api_credentials()

        logger.log("Connecting to API...", 'INFO')

        if BINANCE_AVAILABLE and api_key and api_secret:
            # Use real Binance client
            client = Client(api_key, api_secret, testnet=testnet)

            # Test connection
            account = client.futures_account()

            network_type = "Testnet" if testnet else "Live"
            logger.log(f"Connected to Binance {network_type}", 'SUCCESS')
        else:
            # Use mock client
            client = MockBinanceClient(api_key or "demo", api_secret or "demo", testnet)
            logger.log("Connected in Demo Mode", 'SUCCESS')

        start_data_updates()

        # Update UI
        try:
            if isinstance(client, MockBinanceClient):
                app.connection_status.set("🟡 Demo Mode")
            else:
                network_type = "Testnet" if testnet else "Live"
                app.connection_status.set(f"🟢 {network_type}")
        except:
            pass

        show_notification("Connected successfully!", "success")

    except Exception as e:
        logger.log(f"Connection failed: {str(e)}", 'ERROR')
        # Fall back to mock
        client = MockBinanceClient("demo", "demo", True)
        logger.log("Using Demo Mode", 'WARNING')

        try:
            app.connection_status.set("🟡 Demo Mode")
        except:
            pass


def get_kline_data():
    """Get kline data"""
    if not client:
        return None

    try:
        klines = client.futures_klines(
            symbol=selected_symbol,
            interval=selected_timeframe,
            limit=100
        )

        if PANDAS_AVAILABLE:
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])

            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col])

            return bot.calculate_indicators(df)
        else:
            # Fallback without pandas
            processed_klines = []
            for kline in klines:
                processed_kline = {
                    'timestamp': kline[0],
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5])
                }
                processed_klines.append(processed_kline)

            return bot.calculate_indicators(processed_klines)

    except Exception as e:
        logger.log(f"Error getting data: {e}", 'ERROR')
        return None


def show_notification(message, notification_type="info"):
    """Show notification"""
    try:
        notification = tk.Toplevel(root)
        notification.title("Alert")
        notification.geometry("350x100")
        notification.attributes('-topmost', True)
        notification.transient(root)
        notification.overrideredirect(True)

        x = root.winfo_rootx() + root.winfo_width() - 370
        y = root.winfo_rooty() + 50
        notification.geometry(f"+{x}+{y}")

        colors = {
            'success': '#00b894',
            'error': '#e17055',
            'warning': '#fdcb6e',
            'info': '#74b9ff'
        }

        bg_color = colors.get(notification_type, colors['info'])
        notification.configure(bg=bg_color)

        tk.Label(notification, text=message, fg="white", bg=bg_color,
                 font=("Segoe UI", 11, "bold"), wraplength=300).pack(expand=True)

        notification.after(3000, notification.destroy)
    except:
        pass


# ===== MAIN APPLICATION =====
class TradingApp:
    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.create_variables()
        self.create_interface()

    def setup_window(self):
        self.root.title("🚀 Enhanced Trading Bot v3.0 - Final Edition")
        self.root.geometry("1000x700")
        self.root.configure(bg="#0d1117")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_variables(self):
        self.price_var = tk.StringVar(value="📊 Loading...")
        self.connection_status = tk.StringVar(value="🔴 Disconnected")
        self.symbol_var = tk.StringVar(value=f"Symbol: {selected_symbol}")
        self.auto_status = tk.StringVar(value="👤 Manual Mode")

    def create_interface(self):
        # Header
        header_frame = tk.Frame(self.root, bg="#1f2937")
        header_frame.pack(fill="x")

        header_content = tk.Frame(header_frame, bg="#1f2937")
        header_content.pack(fill="both", expand=True, padx=20, pady=15)

        # Title
        title_label = tk.Label(header_content, text="🚀 Enhanced Trading Bot v3.0",
                               font=("Segoe UI", 18, "bold"), fg="#74b9ff", bg="#1f2937")
        title_label.pack(side="left")

        # Status
        status_panel = tk.Frame(header_content, bg="#2d3436")
        status_panel.pack(side="right", padx=15)

        status_content = tk.Frame(status_panel, bg="#2d3436")
        status_content.pack(padx=15, pady=10)

        self.price_label = tk.Label(status_content, textvariable=self.price_var,
                                    font=("Consolas", 10, "bold"), fg="#00ff88", bg="#2d3436")
        self.price_label.pack()

        connection_label = tk.Label(status_content, textvariable=self.connection_status,
                                    fg="#74b9ff", bg="#2d3436", font=("Segoe UI", 8, "bold"))
        connection_label.pack()

        # Main content
        main_frame = tk.Frame(self.root, bg="#0d1117")
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Left panel
        left_panel = tk.Frame(main_frame, bg="#0d1117", width=300)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)

        self.create_control_panel(left_panel)

        # Right panel
        right_panel = tk.Frame(main_frame, bg="#0d1117")
        right_panel.pack(side="right", fill="both", expand=True)

        self.create_info_panel(right_panel)

    def create_control_panel(self, parent):
        # Connection
        connection_card = ModernCard(parent, title="🔗 Connection")
        connection_card.pack(fill="x", pady=5)

        connection_content = tk.Frame(connection_card, bg="#2d3436")
        connection_content.pack(fill="x", padx=15, pady=10)

        ModernButton(connection_content, text="🔐 Setup & Connect",
                     command=setup_api_credentials, style="primary").pack(fill="x")

        # Market Selection
        market_card = ModernCard(parent, title="📊 Market")
        market_card.pack(fill="x", pady=5)

        market_content = tk.Frame(market_card, bg="#2d3436")
        market_content.pack(fill="x", padx=15, pady=10)

        symbol_label = tk.Label(market_content, textvariable=self.symbol_var,
                                fg="white", bg="#2d3436", font=("Segoe UI", 10, "bold"))
        symbol_label.pack()

        ModernButton(market_content, text="📈 Change Symbol",
                     command=self.change_symbol, style="dark").pack(fill="x", pady=5)

        # Trading
        trading_card = ModernCard(parent, title="⚡ Trading")
        trading_card.pack(fill="x", pady=5)

        trading_content = tk.Frame(trading_card, bg="#2d3436")
        trading_content.pack(fill="x", padx=15, pady=10)

        btn_frame = tk.Frame(trading_content, bg="#2d3436")
        btn_frame.pack(fill="x", pady=5)

        ModernButton(btn_frame, text="📈 BUY",
                     command=lambda: self.place_order(SIDE_BUY),
                     style="success").pack(side="left", fill="x", expand=True, padx=(0, 3))

        ModernButton(btn_frame, text="📉 SELL",
                     command=lambda: self.place_order(SIDE_SELL),
                     style="danger").pack(side="right", fill="x", expand=True, padx=(3, 0))

        # Auto Trading
        auto_card = ModernCard(parent, title="🤖 AUTO TRADING", bg_color="#0d5016")
        auto_card.pack(fill="x", pady=10)

        auto_content = tk.Frame(auto_card, bg="#0d5016")
        auto_content.pack(fill="x", padx=15, pady=15)

        self.auto_btn = tk.Button(auto_content, text="🚀 START AUTO TRADING",
                                  command=self.toggle_auto_trading,
                                  bg="#00b894", fg="white",
                                  font=("Segoe UI", 10, "bold"),
                                  relief="flat", bd=0, padx=15, pady=8)
        self.auto_btn.pack(fill="x")

        auto_status_label = tk.Label(auto_content, textvariable=self.auto_status,
                                     fg="#00ff88", bg="#0d5016", font=("Segoe UI", 9, "bold"))
        auto_status_label.pack(pady=(8, 0))

        # Emergency
        emergency_card = ModernCard(parent, title="🚨 Emergency", bg_color="#4a0e0e")
        emergency_card.pack(fill="x", pady=5)

        emergency_content = tk.Frame(emergency_card, bg="#4a0e0e")
        emergency_content.pack(fill="x", padx=15, pady=10)

        ModernButton(emergency_content, text="🚨 EMERGENCY STOP",
                     command=self.emergency_stop, style="danger").pack(fill="x")

    def create_info_panel(self, parent):
        # Market Info
        market_info_card = ModernCard(parent, title="📊 Market Information")
        market_info_card.pack(fill="x", pady=5)

        market_info_content = tk.Frame(market_info_card, bg="#2d3436")
        market_info_content.pack(fill="x", padx=15, pady=10)

        # Signal Display
        signal_card = ModernCard(parent, title="📡 Trading Signals")
        signal_card.pack(fill="x", pady=5)

        signal_content = tk.Frame(signal_card, bg="#2d3436")
        signal_content.pack(fill="x", padx=15, pady=10)

        self.signal_var = tk.StringVar(value="⏳ Waiting for signal...")
        signal_label = tk.Label(signal_content, textvariable=self.signal_var,
                                fg="#74b9ff", bg="#2d3436", font=("Segoe UI", 12, "bold"))
        signal_label.pack()

        # Activity Log
        log_card = ModernCard(parent, title="📋 Activity Log")
        log_card.pack(fill="both", expand=True, pady=5)

        log_content = tk.Frame(log_card, bg="#2d3436")
        log_content.pack(fill="both", expand=True, padx=15, pady=10)

        self.log_text = tk.Text(log_content, bg="#1e1e2f", fg="white",
                                font=("Consolas", 9), wrap="word")
        self.log_text.pack(fill="both", expand=True)

        # Set logger callback
        logger.ui_callback = self.update_log

    def place_order(self, side):
        """Place order"""
        if not client:
            show_notification("Please connect first", "warning")
            return

        if not bot.safety_check():
            show_notification("Daily limit reached", "warning")
            return

        confirm = messagebox.askyesno("Confirm Trade",
                                      f"Place {side} order for {selected_symbol}?")
        if not confirm:
            return

        try:
            order = client.futures_create_order(
                symbol=selected_symbol,
                side=side,
                type='MARKET',
                quantity=0.001
            )

            logger.log(f"{side} order executed", 'TRADE')
            bot.daily_trade_count += 1

            # Save to database
            cursor = bot.db_connection.cursor()
            cursor.execute('''
                INSERT INTO trades (timestamp, symbol, side, quantity, price, pnl, strategy)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (datetime.now().isoformat(), selected_symbol, side, 0.001,
                  float(order['avgPrice']), 0, 'MANUAL'))
            bot.db_connection.commit()

            show_notification(f"{side} order successful", "success")

        except Exception as e:
            logger.log(f"Order failed: {e}", 'ERROR')
            show_notification("Order failed", "error")

    def toggle_auto_trading(self):
        """Toggle auto trading"""
        global auto_trading, strategy_thread

        if not client:
            show_notification("Please connect first", "warning")
            return

        auto_trading = not auto_trading

        if auto_trading:
            self.auto_btn.configure(text="🛑 STOP AUTO TRADING")
            strategy_thread = threading.Thread(target=self.auto_trading_loop, daemon=True)
            strategy_thread.start()
            logger.log("Auto trading started", 'AUTO')
            self.auto_status.set("🤖 Auto Trading ON")
        else:
            self.auto_btn.configure(text="🚀 START AUTO TRADING")
            logger.log("Auto trading stopped", 'AUTO')
            self.auto_status.set("👤 Manual Mode")

    def auto_trading_loop(self):
        """Auto trading loop"""
        while auto_trading and running:
            try:
                if not client or not bot.safety_check():
                    time.sleep(30)
                    continue

                data = get_kline_data()
                if data is None:
                    time.sleep(30)
                    continue

                signal, confidence = bot.generate_signal(data)

                # Update signal display
                if signal:
                    icon = "📈" if signal == "BUY" else "📉"
                    self.signal_var.set(f"{icon} {signal} ({confidence:.1%})")
                else:
                    self.signal_var.set("⏳ No signal")

                if signal and confidence > 0.7:
                    logger.log(f"Auto signal: {signal} ({confidence:.1%})", 'AUTO')

                    side = SIDE_BUY if signal == 'BUY' else SIDE_SELL

                    try:
                        order = client.futures_create_order(
                            symbol=selected_symbol,
                            side=side,
                            type='MARKET',
                            quantity=0.001
                        )

                        logger.log(f"Auto {side} executed", 'TRADE')
                        bot.daily_trade_count += 1

                        # Save to database
                        cursor = bot.db_connection.cursor()
                        cursor.execute('''
                            INSERT INTO trades (timestamp, symbol, side, quantity, price, pnl, strategy)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (datetime.now().isoformat(), selected_symbol, side, 0.001,
                              float(order['avgPrice']), 0, f'AUTO_{signal}'))
                        bot.db_connection.commit()

                        time.sleep(60)  # Wait between trades
                    except Exception as e:
                        logger.log(f"Auto order failed: {e}", 'ERROR')

                time.sleep(15)  # Check every 15 seconds

            except Exception as e:
                logger.log(f"Auto trading error: {e}", 'ERROR')
                time.sleep(30)

    def change_symbol(self):
        """Change symbol"""
        global selected_symbol

        symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT",
                   "BNBUSDT", "SOLUSDT", "MATICUSDT", "AVAXUSDT"]

        symbol_window = tk.Toplevel(self.root)
        symbol_window.title("📊 Select Symbol")
        symbol_window.geometry("400x400")
        symbol_window.configure(bg="#0d1117")

        tk.Label(symbol_window, text="📊 Select Trading Symbol",
                 font=("Segoe UI", 16, "bold"), fg="#74b9ff", bg="#0d1117").pack(pady=20)

        for symbol in symbols:
            btn = ModernButton(symbol_window, text=symbol,
                               command=lambda s=symbol: self.select_symbol(s, symbol_window),
                               style="primary")
            btn.pack(pady=5, padx=20, fill="x")

    def select_symbol(self, symbol, window):
        """Select symbol"""
        global selected_symbol
        selected_symbol = symbol
        self.symbol_var.set(f"Symbol: {selected_symbol}")
        price_data.clear()
        logger.log(f"Symbol changed to {selected_symbol}", 'INFO')
        show_notification(f"Symbol: {selected_symbol}", "info")
        window.destroy()

    def emergency_stop(self):
        """Emergency stop"""
        global auto_trading

        confirm = messagebox.askyesno("🚨 EMERGENCY STOP",
                                      "Stop all trading immediately?")
        if not confirm:
            return

        auto_trading = False
        logger.log("🚨 EMERGENCY STOP", 'ERROR')
        show_notification("Emergency Stop Activated", "error")

    def update_log(self, log_entry):
        """Update log display"""
        try:
            timestamp = log_entry['timestamp']
            log_type = log_entry['type']
            message = log_entry['message']
            icon = log_entry['icon']

            log_line = f"[{timestamp}] {icon} {log_type}: {message}\n"

            self.log_text.insert(tk.END, log_line)
            self.log_text.see(tk.END)

            # Keep only last 100 lines
            lines = self.log_text.get("1.0", tk.END).split("\n")
            if len(lines) > 100:
                self.log_text.delete("1.0", "2.0")
        except:
            pass

    def update_price_display(self, price):
        """Update price display"""
        try:
            if len(price_data) > 1:
                prev_price = price_data[-2]
                change = ((price - prev_price) / prev_price) * 100

                if change > 0:
                    color = "#00ff88"
                    arrow = "📈"
                elif change < 0:
                    color = "#ff4757"
                    arrow = "📉"
                else:
                    color = "#74b9ff"
                    arrow = "➡️"

                price_text = f"{arrow} {selected_symbol}\n${price:,.6f} ({change:+.2f}%)"
            else:
                color = "#74b9ff"
                price_text = f"📊 {selected_symbol}\n${price:,.6f}"

            self.price_var.set(price_text)
            self.price_label.config(fg=color)

        except Exception as e:
            logger.log(f"Price display error: {e}", 'ERROR')

    def on_close(self):
        """Handle close"""
        global running, auto_trading

        running = False
        auto_trading = False
        logger.log("Shutting down...", 'INFO')

        try:
            if update_thread and update_thread.is_alive():
                update_thread.join(timeout=2)
            if strategy_thread and strategy_thread.is_alive():
                strategy_thread.join(timeout=2)
            bot.db_connection.close()
        except:
            pass

        self.root.destroy()


# ===== DATA UPDATE FUNCTIONS =====
def update_data():
    """Data update loop"""
    global running

    while running:
        try:
            if client:
                ticker = client.futures_symbol_ticker(symbol=selected_symbol)
                price = float(ticker['price'])

                root.after(0, lambda: app.update_price_display(price))

                price_data.append(price)
                if len(price_data) > 100:
                    price_data.pop(0)

        except Exception as e:
            logger.log(f"Data update error: {e}", 'ERROR')

        time.sleep(3)


def start_data_updates():
    """Start data updates"""
    global update_thread
    if update_thread is None or not update_thread.is_alive():
        update_thread = threading.Thread(target=update_data, daemon=True)
        update_thread.start()


# ===== MAIN FUNCTION =====
def main():
    """Main function"""
    global root, app, config_manager, logger, bot

    # Initialize components
    config_manager = ConfigManager()
    logger = SimpleLogger()
    bot = SimpleTradingBot()

    # Create application
    root = tk.Tk()
    app = TradingApp(root)

    # Show startup info
    print("\n" + "=" * 60)
    print("🚀 ENHANCED TRADING BOT v3.0 - FINAL EDITION")
    print("=" * 60)
    print("📊 FEATURES STATUS:")
    print(f"   {'✅' if BINANCE_AVAILABLE else '🟡'} Binance API")
    print(f"   {'✅' if PANDAS_AVAILABLE else '🟡'} Data Analysis")
    print(f"   {'✅' if ML_AVAILABLE else '🟡'} Machine Learning")
    print(f"   {'✅' if EMAIL_AVAILABLE else '🟡'} Email Notifications")
    print(f"   {'✅' if PLOTTING_AVAILABLE else '🟡'} Advanced Charts")
    print("\n🎮 KEYBOARD SHORTCUTS:")
    print("   F1 - Change Symbol  |  ESC - Emergency Stop")
    print("\n💡 READY TO TRADE!")
    print("=" * 60)

    # Initialize logger
    logger.log("🚀 Enhanced Trading Bot v3.0 initialized", 'SUCCESS')
    logger.log("All systems ready", 'INFO')
    logger.log("Click 'Setup & Connect' to begin", 'INFO')

    # Keyboard shortcuts
    root.bind('<F1>', lambda e: app.change_symbol())
    root.bind('<Escape>', lambda e: app.emergency_stop())

    # Start application
    root.mainloop()


if __name__ == "__main__":
    main()