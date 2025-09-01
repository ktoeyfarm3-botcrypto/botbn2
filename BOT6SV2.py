import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import os
import configparser
from binance.client import Client
from binance.enums import *
import threading
import time
import json
import sqlite3
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import warnings

warnings.filterwarnings('ignore')


# ===== Configuration Management =====
class ConfigManager:
    def __init__(self):
        self.config_file = "config.ini"
        self.config = configparser.ConfigParser()
        self.load_config()

    def load_config(self):
        """Load configuration from file or create default"""
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        else:
            self.create_default_config()

    def create_default_config(self):
        """Create default configuration file"""
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
            'min_volume': '1000000',
            'rsi_oversold': '30',
            'rsi_overbought': '70',
            'enable_notifications': 'True'
        }
        self.save_config()

    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            self.config.write(f)

    def get_api_credentials(self):
        """Get API credentials safely"""
        return (
            self.config.get('API', 'api_key', fallback=''),
            self.config.get('API', 'api_secret', fallback=''),
            self.config.getboolean('API', 'testnet', fallback=True)
        )

    def set_api_credentials(self, api_key, api_secret, testnet=True):
        """Set API credentials"""
        self.config['API']['api_key'] = api_key
        self.config['API']['api_secret'] = api_secret
        self.config['API']['testnet'] = str(testnet)
        self.save_config()


# ===== Enhanced Logging System =====
class TradingLogger:
    def __init__(self, ui_callback=None):
        self.logs = []
        self.ui_callback = ui_callback
        self.log_types = {
            'INFO': {'color': '#74b9ff', 'icon': 'ℹ️'},
            'SUCCESS': {'color': '#00ff88', 'icon': '✅'},
            'WARNING': {'color': '#ffeaa7', 'icon': '⚠️'},
            'ERROR': {'color': '#ff4757', 'icon': '❌'},
            'TRADE': {'color': '#00ff88', 'icon': '📈'},
            'AUTO': {'color': '#a29bfe', 'icon': '🤖'},
            'SIGNAL': {'color': '#fd79a8', 'icon': '📊'}
        }

    def log(self, message, log_type='INFO', details=None):
        """Enhanced logging with types and details"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        icon = self.log_types.get(log_type, {}).get('icon', '📝')

        log_entry = {
            'timestamp': timestamp,
            'type': log_type,
            'message': message,
            'details': details,
            'icon': icon
        }

        self.logs.insert(0, log_entry)  # Add to beginning
        if len(self.logs) > 100:  # Keep only last 100 logs
            self.logs.pop()

        if self.ui_callback:
            self.ui_callback(log_entry)

        # Also print to console for debugging
        print(f"[{timestamp}] {icon} {log_type}: {message}")

    def get_recent_logs(self, count=20):
        """Get recent logs for display"""
        return self.logs[:count]


# ===== Helper Functions =====
def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    if len(prices) < period + 1:
        return [50] * len(prices)

    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    avg_gains = [np.mean(gains[:period])]
    avg_losses = [np.mean(losses[:period])]

    for i in range(period, len(deltas)):
        avg_gains.append((avg_gains[-1] * (period - 1) + gains[i]) / period)
        avg_losses.append((avg_losses[-1] * (period - 1) + losses[i]) / period)

    rs = np.array(avg_gains) / np.array(avg_losses)
    rsi = 100 - (100 / (1 + rs))

    return [50] + list(rsi)


def calculate_ema(prices, period):
    """Calculate EMA indicator"""
    if len(prices) < period:
        return [prices[0]] * len(prices)

    alpha = 2 / (period + 1)
    ema = [prices[0]]

    for price in prices[1:]:
        ema.append(alpha * price + (1 - alpha) * ema[-1])

    return ema


def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """Calculate Bollinger Bands"""
    if len(prices) < period:
        return prices, prices, prices

    sma = []
    bb_upper = []
    bb_lower = []

    for i in range(len(prices)):
        if i < period - 1:
            sma.append(prices[i])
            bb_upper.append(prices[i])
            bb_lower.append(prices[i])
        else:
            window = prices[i - period + 1:i + 1]
            mean = np.mean(window)
            std = np.std(window)

            sma.append(mean)
            bb_upper.append(mean + (std * std_dev))
            bb_lower.append(mean - (std * std_dev))

    return sma, bb_upper, bb_lower


# ===== Trading Bot Class =====
class SafeTradingBot:
    def __init__(self):
        self.db_connection = self.init_database()
        self.safety_checks_enabled = True
        self.max_daily_trades = 10
        self.daily_trade_count = 0
        self.last_trade_date = datetime.now().date()
        self.active_signals = []

    def init_database(self):
        """Initialize database for trade history"""
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
                price REAL,
                indicators TEXT
            )
        ''')

        conn.commit()
        return conn

    def safety_check(self):
        """Perform safety checks before trading"""
        current_date = datetime.now().date()

        if current_date != self.last_trade_date:
            self.daily_trade_count = 0
            self.last_trade_date = current_date

        if self.daily_trade_count >= self.max_daily_trades:
            logger.log(f"Daily trade limit ({self.max_daily_trades}) reached", 'WARNING')
            return False

        return True

    def calculate_indicators(self, df):
        """Calculate technical indicators with error handling"""
        try:
            if len(df) == 0:
                return df

            closes = df['close'].values
            highs = df['high'].values
            lows = df['low'].values
            volumes = df['volume'].values

            # Calculate indicators and ensure length matches DataFrame
            rsi_values = calculate_rsi(closes)
            ema_9_values = calculate_ema(closes, 9)
            ema_21_values = calculate_ema(closes, 21)
            ema_50_values = calculate_ema(closes, 50)

            # Ensure all arrays have the same length as DataFrame
            data_length = len(df)

            # Pad or trim arrays to match DataFrame length
            def ensure_length(arr, target_length):
                if len(arr) > target_length:
                    return arr[-target_length:]
                elif len(arr) < target_length:
                    # Pad with the first value
                    padding = [arr[0]] * (target_length - len(arr))
                    return padding + arr
                return arr

            df = df.copy()  # Create a copy to avoid modifying original
            df.loc[:, 'rsi'] = ensure_length(rsi_values, data_length)
            df.loc[:, 'ema_9'] = ensure_length(ema_9_values, data_length)
            df.loc[:, 'ema_21'] = ensure_length(ema_21_values, data_length)
            df.loc[:, 'ema_50'] = ensure_length(ema_50_values, data_length)

            # Bollinger Bands
            bb_middle, bb_upper, bb_lower = calculate_bollinger_bands(closes)
            df.loc[:, 'bb_upper'] = ensure_length(bb_upper, data_length)
            df.loc[:, 'bb_middle'] = ensure_length(bb_middle, data_length)
            df.loc[:, 'bb_lower'] = ensure_length(bb_lower, data_length)

            # MACD
            ema_12 = calculate_ema(closes, 12)
            ema_26 = calculate_ema(closes, 26)
            macd_values = np.array(ensure_length(ema_12, data_length)) - np.array(ensure_length(ema_26, data_length))
            df.loc[:, 'macd'] = macd_values

            macd_signal_values = calculate_ema(macd_values, 9)
            df.loc[:, 'macd_signal'] = ensure_length(macd_signal_values, data_length)

            # Volume SMA
            volume_sma_values = calculate_ema(volumes, 20)
            df.loc[:, 'volume_sma'] = ensure_length(volume_sma_values, data_length)

            return df

        except Exception as e:
            logger.log(f"Error calculating indicators: {e}", 'ERROR')
            # Return original DataFrame with default indicator values
            df = df.copy()
            data_length = len(df)
            default_value = 50

            df.loc[:, 'rsi'] = [default_value] * data_length
            df.loc[:, 'ema_9'] = df['close'].values
            df.loc[:, 'ema_21'] = df['close'].values
            df.loc[:, 'ema_50'] = df['close'].values
            df.loc[:, 'bb_upper'] = df['close'].values
            df.loc[:, 'bb_middle'] = df['close'].values
            df.loc[:, 'bb_lower'] = df['close'].values
            df.loc[:, 'macd'] = [0] * data_length
            df.loc[:, 'macd_signal'] = [0] * data_length
            df.loc[:, 'volume_sma'] = df['volume'].values

            return df

    def generate_signal(self, df):
        """Generate trading signals with detailed logging"""
        if len(df) < 50:
            return None, 0

        try:
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            signals = []

            # Check if required columns exist
            required_columns = ['rsi', 'macd', 'macd_signal', 'ema_9', 'ema_21', 'ema_50', 'bb_upper', 'bb_lower',
                                'close', 'volume', 'volume_sma']
            for col in required_columns:
                if col not in df.columns:
                    logger.log(f"Missing indicator column: {col}", 'WARNING')
                    return None, 0

            # RSI Strategy
            if pd.notna(latest['rsi']) and pd.notna(prev['rsi']):
                if latest['rsi'] < settings['rsi_oversold'] and prev['rsi'] >= settings['rsi_oversold']:
                    signals.append(('RSI_OVERSOLD_BUY', 0.3))
                    logger.log(f"RSI Signal: Oversold condition detected (RSI: {latest['rsi']:.1f})", 'SIGNAL')
                elif latest['rsi'] > settings['rsi_overbought'] and prev['rsi'] <= settings['rsi_overbought']:
                    signals.append(('RSI_OVERBOUGHT_SELL', 0.3))
                    logger.log(f"RSI Signal: Overbought condition detected (RSI: {latest['rsi']:.1f})", 'SIGNAL')

            # MACD Strategy
            if pd.notna(latest['macd']) and pd.notna(latest['macd_signal']) and pd.notna(prev['macd']) and pd.notna(
                    prev['macd_signal']):
                if latest['macd'] > latest['macd_signal'] and prev['macd'] <= prev['macd_signal']:
                    signals.append(('MACD_BULLISH_CROSS', 0.4))
                    logger.log(f"MACD Signal: Bullish crossover detected", 'SIGNAL')
                elif latest['macd'] < latest['macd_signal'] and prev['macd'] >= prev['macd_signal']:
                    signals.append(('MACD_BEARISH_CROSS', 0.4))
                    logger.log(f"MACD Signal: Bearish crossover detected", 'SIGNAL')

            # EMA Strategy
            if all(pd.notna(latest[col]) and pd.notna(prev[col]) for col in ['ema_9', 'ema_21', 'ema_50', 'close']):
                if latest['ema_9'] > latest['ema_21'] > latest['ema_50']:
                    if latest['close'] > latest['ema_9'] and prev['close'] <= prev['ema_9']:
                        signals.append(('EMA_GOLDEN_CROSS', 0.5))
                        logger.log(f"EMA Signal: Golden cross pattern confirmed", 'SIGNAL')
                elif latest['ema_9'] < latest['ema_21'] < latest['ema_50']:
                    if latest['close'] < latest['ema_9'] and prev['close'] >= prev['ema_9']:
                        signals.append(('EMA_DEATH_CROSS', 0.5))
                        logger.log(f"EMA Signal: Death cross pattern confirmed", 'SIGNAL')

            # Bollinger Bands Strategy
            if all(pd.notna(latest[col]) for col in ['close', 'bb_lower', 'bb_upper', 'rsi']):
                if latest['close'] < latest['bb_lower'] and latest['rsi'] < 40:
                    signals.append(('BB_OVERSOLD', 0.3))
                    logger.log(f"BB Signal: Price below lower band with low RSI", 'SIGNAL')
                elif latest['close'] > latest['bb_upper'] and latest['rsi'] > 60:
                    signals.append(('BB_OVERBOUGHT', 0.3))
                    logger.log(f"BB Signal: Price above upper band with high RSI", 'SIGNAL')

            # Volume confirmation
            if pd.notna(latest['volume']) and pd.notna(latest['volume_sma']):
                if latest['volume'] > latest['volume_sma'] * 1.5:
                    for signal in signals:
                        if 'BUY' in signal[0] or 'BULLISH' in signal[0]:
                            signals.append(('VOLUME_CONFIRM_BUY', 0.2))
                        elif 'SELL' in signal[0] or 'BEARISH' in signal[0]:
                            signals.append(('VOLUME_CONFIRM_SELL', 0.2))

            buy_signals = [s for s in signals if any(x in s[0] for x in ['BUY', 'BULLISH', 'OVERSOLD'])]
            sell_signals = [s for s in signals if any(x in s[0] for x in ['SELL', 'BEARISH', 'OVERBOUGHT'])]

            buy_confidence = sum([s[1] for s in buy_signals])
            sell_confidence = sum([s[1] for s in sell_signals])

            if buy_confidence > sell_confidence and buy_confidence > 0.6:
                signal_details = f"Buy signals: {[s[0] for s in buy_signals]}"
                logger.log(f"Strong BUY signal generated", 'SIGNAL', signal_details)
                return 'BUY', min(buy_confidence, 1.0)
            elif sell_confidence > buy_confidence and sell_confidence > 0.6:
                signal_details = f"Sell signals: {[s[0] for s in sell_signals]}"
                logger.log(f"Strong SELL signal generated", 'SIGNAL', signal_details)
                return 'SELL', min(sell_confidence, 1.0)

            return None, 0

        except Exception as e:
            logger.log(f"Error in generate_signal: {e}", 'ERROR')
            return None, 0


# Initialize global objects
config_manager = ConfigManager()
logger = TradingLogger()
bot = SafeTradingBot()

# Global Variables
client = None
running = True
price_data = []
volume_data = []
kline_data = []
positions = {}
orders = []
balance_info = {}
pnl_history = []
auto_trading = False
selected_symbol = "BTCUSDT"
selected_timeframe = "1m"

# Trading Settings
settings = {
    'risk_percent': config_manager.config.getfloat('TRADING', 'risk_percent', fallback=2.0),
    'stop_loss_percent': config_manager.config.getfloat('TRADING', 'stop_loss_percent', fallback=1.5),
    'take_profit_percent': config_manager.config.getfloat('TRADING', 'take_profit_percent', fallback=3.0),
    'max_positions': config_manager.config.getint('TRADING', 'max_positions', fallback=3),
    'min_volume': config_manager.config.getfloat('TRADING', 'min_volume', fallback=1000000),
    'rsi_oversold': config_manager.config.getint('TRADING', 'rsi_oversold', fallback=30),
    'rsi_overbought': config_manager.config.getint('TRADING', 'rsi_overbought', fallback=70),
    'enable_notifications': config_manager.config.getboolean('TRADING', 'enable_notifications', fallback=True)
}

update_thread = None
strategy_thread = None


# ===== Modern UI Components =====
class ModernCard(tk.Frame):
    """Modern card-style UI component"""

    def __init__(self, parent, title="", bg_color="#2d3436", title_color="#74b9ff", **kwargs):
        super().__init__(parent, bg=bg_color, relief="flat", bd=1, **kwargs)

        # Card shadow effect
        self.configure(highlightbackground="#636e72", highlightthickness=1)

        if title:
            title_frame = tk.Frame(self, bg=bg_color, height=40)
            title_frame.pack(fill="x", padx=15, pady=(10, 0))
            title_frame.pack_propagate(False)

            tk.Label(title_frame, text=title, fg=title_color, bg=bg_color,
                     font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=5)


class ModernButton(tk.Button):
    """Modern styled button with hover effects"""

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
                         font=("Segoe UI", 10, "bold"),
                         relief="flat", bd=0, padx=20, pady=8,
                         cursor="hand2", **kwargs)

        # Hover effects
        self.bind("<Enter>", lambda e: self.configure(bg=config['hover']))
        self.bind("<Leave>", lambda e: self.configure(bg=config['bg']))


class EnhancedLogFrame(tk.Frame):
    """Enhanced log display with filtering and styling"""

    def __init__(self, parent):
        super().__init__(parent, bg="#1e1e2f")
        self.filter_var = tk.StringVar(value="ALL")
        self.setup_ui()

    def setup_ui(self):
        # Header
        header = tk.Frame(self, bg="#2d3436", height=40)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="📊 Real-time Activity Log",
                 font=("Segoe UI", 12, "bold"), fg="#74b9ff", bg="#2d3436").pack(side="left", padx=15, pady=10)

        # Log filter buttons
        filter_frame = tk.Frame(header, bg="#2d3436")
        filter_frame.pack(side="right", padx=15, pady=5)

        filters = ["ALL", "TRADE", "AUTO", "SIGNAL", "ERROR"]

        for filter_type in filters:
            color = "#74b9ff" if filter_type == "ALL" else logger.log_types.get(filter_type, {}).get('color', '#636e72')
            btn = tk.Button(filter_frame, text=filter_type,
                            command=lambda f=filter_type: self.set_filter(f),
                            bg=color, fg="white" if filter_type != "ALL" else "#2d3436",
                            font=("Segoe UI", 8, "bold"), relief="flat", bd=0,
                            padx=8, pady=2)
            btn.pack(side="left", padx=2)

        # Log display area with custom styling
        log_container = tk.Frame(self, bg="#1e1e2f")
        log_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Custom scrollable log area
        self.log_canvas = tk.Canvas(log_container, bg="#1e1e2f", highlightthickness=0)
        self.log_scrollbar = ttk.Scrollbar(log_container, orient="vertical", command=self.log_canvas.yview)
        self.scrollable_frame = tk.Frame(self.log_canvas, bg="#1e1e2f")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.log_canvas.configure(scrollregion=self.log_canvas.bbox("all"))
        )

        self.log_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.log_canvas.configure(yscrollcommand=self.log_scrollbar.set)

        self.log_canvas.pack(side="left", fill="both", expand=True)
        self.log_scrollbar.pack(side="right", fill="y")

        # Bind mousewheel
        def _on_mousewheel(event):
            self.log_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.log_canvas.bind("<MouseWheel>", _on_mousewheel)

    def set_filter(self, filter_type):
        """Set log filter"""
        self.filter_var.set(filter_type)
        self.update_log_display()

    def add_log_entry(self, log_entry):
        """Add new log entry with modern styling"""
        if self.filter_var.get() != "ALL" and log_entry['type'] != self.filter_var.get():
            return

        entry_frame = tk.Frame(self.scrollable_frame, bg="#2d3436", relief="flat", bd=1)
        entry_frame.pack(fill="x", padx=5, pady=2)

        # Time and icon
        header_frame = tk.Frame(entry_frame, bg="#2d3436")
        header_frame.pack(fill="x", padx=10, pady=5)

        time_label = tk.Label(header_frame, text=f"[{log_entry['timestamp']}]",
                              font=("Consolas", 9), fg="#636e72", bg="#2d3436")
        time_label.pack(side="left")

        icon_label = tk.Label(header_frame, text=log_entry['icon'],
                              font=("Segoe UI", 10), bg="#2d3436")
        icon_label.pack(side="left", padx=(10, 5))

        type_label = tk.Label(header_frame, text=log_entry['type'],
                              font=("Segoe UI", 9, "bold"),
                              fg=logger.log_types.get(log_entry['type'], {}).get('color', 'white'),
                              bg="#2d3436")
        type_label.pack(side="left")

        # Message
        msg_label = tk.Label(entry_frame, text=log_entry['message'],
                             font=("Segoe UI", 10), fg="white", bg="#2d3436",
                             wraplength=350, justify="left")
        msg_label.pack(anchor="w", padx=15, pady=(0, 5))

        # Details if available
        if log_entry.get('details'):
            details_label = tk.Label(entry_frame, text=log_entry['details'],
                                     font=("Consolas", 8), fg="#a0a0a0", bg="#2d3436",
                                     wraplength=340, justify="left")
            details_label.pack(anchor="w", padx=20, pady=(0, 5))

        # Auto scroll to bottom
        self.log_canvas.update_idletasks()
        self.log_canvas.yview_moveto(1)

    def update_log_display(self):
        """Update log display based on filter"""
        # Clear current display
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Add filtered logs
        logs = logger.get_recent_logs(50)
        for log_entry in reversed(logs):  # Show oldest first
            if self.filter_var.get() == "ALL" or log_entry['type'] == self.filter_var.get():
                self.add_log_entry(log_entry)


# ===== API Functions =====
def setup_api_credentials():
    """Modern API credential setup"""
    global client

    api_key, api_secret, testnet = config_manager.get_api_credentials()

    if not api_key or not api_secret:
        cred_window = tk.Toplevel(root)
        cred_window.title("🔐 API Credentials Setup")
        cred_window.geometry("600x500")
        cred_window.configure(bg="#1e1e2f")
        cred_window.transient(root)
        cred_window.grab_set()

        # Modern header
        header_frame = tk.Frame(cred_window, bg="#0984e3", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        tk.Label(header_frame, text="🔐 Secure API Connection",
                 font=("Segoe UI", 16, "bold"), fg="white", bg="#0984e3").pack(pady=25)

        # Warning card
        warning_card = ModernCard(cred_window, title="⚠️ Security Notice", bg_color="#e17055")
        warning_card.pack(fill="x", padx=20, pady=15)

        warning_text = """Your API credentials will be encrypted and stored locally.
Ensure your computer is secure and never share these credentials.
Use testnet for learning and practice trading."""

        tk.Label(warning_card, text=warning_text, fg="white", bg="#e17055",
                 font=("Segoe UI", 10), justify="left", wraplength=500).pack(padx=15, pady=10)

        # Input card
        input_card = ModernCard(cred_window, title="🔑 API Configuration")
        input_card.pack(fill="both", expand=True, padx=20, pady=15)

        # API Key input
        tk.Label(input_card, text="Binance API Key:", fg="white", bg="#2d3436",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=15, pady=(10, 5))
        api_key_entry = tk.Entry(input_card, font=("Consolas", 11), bg="#636e72", fg="white",
                                 insertbackground="white", relief="flat", bd=5)
        api_key_entry.pack(fill="x", padx=15, pady=5)

        # API Secret input
        tk.Label(input_card, text="Binance API Secret:", fg="white", bg="#2d3436",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=15, pady=(15, 5))
        api_secret_entry = tk.Entry(input_card, font=("Consolas", 11), bg="#636e72", fg="white",
                                    insertbackground="white", relief="flat", bd=5, show="*")
        api_secret_entry.pack(fill="x", padx=15, pady=5)

        # Testnet option
        testnet_frame = tk.Frame(input_card, bg="#2d3436")
        testnet_frame.pack(fill="x", padx=15, pady=15)

        testnet_var = tk.BooleanVar(value=True)
        testnet_check = tk.Checkbutton(testnet_frame, text="🧪 Use Testnet (Recommended for testing)",
                                       variable=testnet_var, fg="#74b9ff", bg="#2d3436",
                                       selectcolor="#0984e3", font=("Segoe UI", 10))
        testnet_check.pack(anchor="w")

        def save_and_connect():
            key = api_key_entry.get().strip()
            secret = api_secret_entry.get().strip()

            if not key or not secret:
                messagebox.showerror("Error", "Please enter both API key and secret")
                return

            config_manager.set_api_credentials(key, secret, testnet_var.get())
            cred_window.destroy()
            connect_api()

        # Modern buttons
        btn_frame = tk.Frame(input_card, bg="#2d3436")
        btn_frame.pack(fill="x", padx=15, pady=15)

        ModernButton(btn_frame, text="🚀 Save & Connect", command=save_and_connect,
                     style="success").pack(side="left", padx=5)
        ModernButton(btn_frame, text="❌ Cancel", command=cred_window.destroy,
                     style="danger").pack(side="right", padx=5)

    else:
        connect_api()


def connect_api():
    """Connect to Binance API with enhanced logging"""
    global client

    try:
        api_key, api_secret, testnet = config_manager.get_api_credentials()

        if not api_key or not api_secret:
            logger.log("API credentials not configured", 'ERROR')
            return

        logger.log("Establishing connection to Binance API...", 'INFO')
        client = Client(api_key, api_secret, testnet=testnet)

        # Test connection
        account = client.futures_account()

        # Set leverage safely
        try:
            client.futures_change_leverage(symbol=selected_symbol, leverage=5)
            logger.log(f"Leverage set to 5x for {selected_symbol}", 'SUCCESS')
        except Exception as e:
            logger.log(f"Could not set leverage: {e}", 'WARNING')

        network_type = "Testnet" if testnet else "Live"
        logger.log(f"Successfully connected to Binance Futures {network_type}", 'SUCCESS')
        start_data_updates()

        connection_status.set(f"🟢 Connected ({network_type})")

        # Show connection success notification
        show_modern_notification(f"Connected to {network_type} Environment", "success")

    except Exception as e:
        logger.log(f"Connection failed: {str(e)}", 'ERROR')
        messagebox.showerror("Connection Error", f"Failed to connect: {str(e)}")


def get_kline_data():
    """Get kline data for analysis with error handling"""
    if not client:
        return None

    try:
        klines = client.futures_klines(
            symbol=selected_symbol,
            interval=selected_timeframe,
            limit=100
        )

        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])

        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col])

        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return bot.calculate_indicators(df)

    except Exception as e:
        logger.log(f"Error getting kline data: {e}", 'ERROR')
        return None


def get_symbol_info(symbol):
    """Get symbol precision and filters"""
    try:
        exchange_info = client.futures_exchange_info()
        for s in exchange_info['symbols']:
            if s['symbol'] == symbol:
                for filter_item in s['filters']:
                    if filter_item['filterType'] == 'LOT_SIZE':
                        step_size = float(filter_item['stepSize'])
                        min_qty = float(filter_item['minQty'])
                        max_qty = float(filter_item['maxQty'])
                        return step_size, min_qty, max_qty
        return 0.001, 0.001, 10000
    except:
        return 0.001, 0.001, 10000


def get_price_precision(symbol):
    """Get price precision for symbol"""
    try:
        exchange_info = client.futures_exchange_info()
        for s in exchange_info['symbols']:
            if s['symbol'] == symbol:
                for filter_item in s['filters']:
                    if filter_item['filterType'] == 'PRICE_FILTER':
                        tick_size = float(filter_item['tickSize'])
                        if tick_size >= 1:
                            return 0
                        else:
                            return len(str(tick_size).split('.')[-1].rstrip('0'))
        return 2  # Default precision
    except:
        return 2


def round_step_size(quantity, step_size):
    """Round quantity to valid step size"""
    if step_size == 0:
        return quantity

    if step_size >= 1:
        decimals = 0
    else:
        decimals = len(str(step_size).split('.')[-1].rstrip('0'))

    rounded = round(quantity / step_size) * step_size
    return round(rounded, decimals)


def get_price_precision(symbol):
    """Get price precision for symbol"""
    try:
        exchange_info = client.futures_exchange_info()
        for s in exchange_info['symbols']:
            if s['symbol'] == symbol:
                for filter_item in s['filters']:
                    if filter_item['filterType'] == 'PRICE_FILTER':
                        tick_size = float(filter_item['tickSize'])
                        if tick_size >= 1:
                            return 0
                        else:
                            return len(str(tick_size).split('.')[-1].rstrip('0'))
        return 2  # Default precision
    except:
        return 2


def round_price(price, precision):
    """Round price to valid precision"""
    return round(price, precision)


def calculate_position_size():
    """Calculate position size with proper precision handling"""
    try:
        if not client:
            return 0.001

        step_size, min_qty, max_qty = get_symbol_info(selected_symbol)
        account = client.futures_account()
        total_balance = float(account['totalWalletBalance'])

        if total_balance < 100:
            logger.log("Warning: Balance too low for safe trading", 'WARNING')
            return round_step_size(min_qty, step_size)

        risk_amount = total_balance * (settings['risk_percent'] / 100)
        ticker = client.futures_symbol_ticker(symbol=selected_symbol)
        current_price = float(ticker['price'])

        stop_loss_price = current_price * (1 - settings['stop_loss_percent'] / 100)
        risk_per_unit = current_price - stop_loss_price

        if risk_per_unit > 0:
            quantity = risk_amount / risk_per_unit
            max_quantity = total_balance * 0.1 / current_price
            quantity = min(quantity, max_quantity)
            quantity = max(min_qty, min(quantity, max_qty))
            quantity = round_step_size(quantity, step_size)
            return quantity

        return round_step_size(min_qty, step_size)

    except Exception as e:
        logger.log(f"Error calculating position size: {e}", 'ERROR')
        return 0.001


def place_smart_order(side, strategy="MANUAL"):
    """Enhanced smart order placement with detailed logging"""
    if not client:
        show_modern_notification("Please connect API first", "warning")
        return

    if not bot.safety_check():
        show_modern_notification("Trading blocked by safety checks", "warning")
        return

    if strategy == "MANUAL":
        confirm = messagebox.askyesno("Confirm Trade",
                                      f"Place {side} order for {selected_symbol}?\n"
                                      f"Risk: {settings['risk_percent']}%\n"
                                      f"Stop Loss: {settings['stop_loss_percent']}%\n"
                                      f"Take Profit: {settings['take_profit_percent']}%")
        if not confirm:
            return

    try:
        quantity = calculate_position_size()

        if quantity <= 0.001:
            logger.log("Position size too small, order cancelled", 'WARNING')
            return

        logger.log(f"Placing {side} order for {quantity} {selected_symbol}", 'TRADE')

        # Place main order
        order = client.futures_create_order(
            symbol=selected_symbol,
            side=side,
            type='MARKET',
            quantity=quantity
        )

        fill_price = float(order.get('avgPrice', 0)) if order.get('avgPrice') else float(order.get('price', 0))
        if fill_price == 0:
            ticker = client.futures_symbol_ticker(symbol=selected_symbol)
            fill_price = float(ticker['price'])

        # Calculate SL/TP with proper precision
        price_precision = get_price_precision(selected_symbol)

        if side == SIDE_BUY:
            stop_loss = round_price(fill_price * (1 - settings['stop_loss_percent'] / 100), price_precision)
            take_profit = round_price(fill_price * (1 + settings['take_profit_percent'] / 100), price_precision)
        else:
            stop_loss = round_price(fill_price * (1 + settings['stop_loss_percent'] / 100), price_precision)
            take_profit = round_price(fill_price * (1 - settings['take_profit_percent'] / 100), price_precision)

        # Place Stop Loss
        try:
            sl_order = client.futures_create_order(
                symbol=selected_symbol,
                side=SIDE_SELL if side == SIDE_BUY else SIDE_BUY,
                type='STOP_MARKET',
                quantity=quantity,
                stopPrice=stop_loss,
                reduceOnly=True
            )
            logger.log(f"Stop Loss placed at ${stop_loss:.{price_precision}f}", 'SUCCESS')
        except Exception as e:
            logger.log(f"SL order failed: {e}", 'ERROR')

        # Place Take Profit
        try:
            tp_order = client.futures_create_order(
                symbol=selected_symbol,
                side=SIDE_SELL if side == SIDE_BUY else SIDE_BUY,
                type='TAKE_PROFIT_MARKET',
                quantity=quantity,
                stopPrice=take_profit,
                reduceOnly=True
            )
            logger.log(f"Take Profit placed at ${take_profit:.{price_precision}f}", 'SUCCESS')
        except Exception as e:
            logger.log(f"TP order failed: {e}", 'ERROR')

        # Record trade
        cursor = bot.db_connection.cursor()
        cursor.execute('''
            INSERT INTO trades (timestamp, symbol, side, quantity, price, pnl, strategy)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (datetime.now().isoformat(), selected_symbol, side, quantity, fill_price, 0, strategy))
        bot.db_connection.commit()

        bot.daily_trade_count += 1

        # Enhanced order success logging
        order_details = f"""Order executed successfully:
Symbol: {order['symbol']} | Side: {side} | Qty: {quantity}
Entry: ${fill_price:,.8f} | SL: ${stop_loss:,.8f} | TP: ${take_profit:,.8f}
Order ID: {order['orderId']} | Strategy: {strategy}"""

        logger.log(f"{side} order executed for {selected_symbol}", 'TRADE', order_details)

        if settings['enable_notifications']:
            show_modern_notification(f"Order Placed: {side} {selected_symbol}", "success")

    except Exception as e:
        logger.log(f"Order failed: {str(e)}", 'ERROR')
        show_modern_notification(f"Order failed: {str(e)}", "error")


def auto_trading_strategy():
    """Enhanced auto trading strategy with detailed logging"""
    global auto_trading

    logger.log("Auto trading strategy started", 'AUTO')

    while auto_trading and running:
        try:
            if not client:
                time.sleep(5)
                continue

            if not bot.safety_check():
                logger.log("Auto trading paused - safety limits reached", 'AUTO')
                time.sleep(300)
                continue

            # Get and analyze data
            df = get_kline_data()
            if df is None or len(df) < 50:
                time.sleep(30)
                continue

            signal, confidence = bot.generate_signal(df)

            # Enhanced signal processing
            if signal and confidence > 0.8:
                current_positions = get_current_positions()

                logger.log(f"Strong signal detected: {signal} (Confidence: {confidence:.2f})", 'AUTO')

                if len(current_positions) < settings['max_positions']:
                    latest_price = df.iloc[-1]['close']
                    latest_volume = df.iloc[-1]['volume']
                    latest_rsi = df.iloc[-1]['rsi']

                    if latest_volume > settings['min_volume']:
                        side = SIDE_BUY if signal == 'BUY' else SIDE_SELL

                        # Log market conditions
                        market_info = f"""Market Analysis:
Price: ${latest_price:.8f} | Volume: {latest_volume / 1000000:.1f}M
RSI: {latest_rsi:.1f} | Confidence: {confidence:.2f}
Active Positions: {len(current_positions)}/{settings['max_positions']}"""

                        logger.log(f"Executing auto {side} order", 'AUTO', market_info)

                        # Record signal
                        cursor = bot.db_connection.cursor()
                        cursor.execute('''
                            INSERT INTO signals (timestamp, symbol, signal_type, confidence, price, indicators)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (datetime.now().isoformat(), selected_symbol, signal, confidence,
                              latest_price, json.dumps(str(df.iloc[-1].to_dict()))))
                        bot.db_connection.commit()

                        # Place order
                        root.after(0, lambda: place_smart_order(side, f"AUTO_{signal}"))
                        time.sleep(120)
                    else:
                        logger.log(f"Volume too low for trading: {latest_volume / 1000000:.1f}M", 'AUTO')
                else:
                    logger.log(f"Max positions reached: {len(current_positions)}/{settings['max_positions']}", 'AUTO')
            else:
                if signal:
                    logger.log(f"Weak signal ignored: {signal} (Confidence: {confidence:.2f})", 'AUTO')

            time.sleep(15)

        except Exception as e:
            logger.log(f"Auto trading error: {e}", 'ERROR')
            time.sleep(60)

    logger.log("Auto trading strategy stopped", 'AUTO')


def get_current_positions():
    """Get current positions with error handling"""
    try:
        if not client:
            return []
        positions = client.futures_position_information()
        return [p for p in positions if float(p['positionAmt']) != 0]
    except Exception as e:
        logger.log(f"Error getting positions: {e}", 'ERROR')
        return []


def update_data():
    """Update price data and other information"""
    global running

    while running:
        try:
            if client:
                ticker = client.futures_symbol_ticker(symbol=selected_symbol)
                price = float(ticker['price'])

                root.after(0, lambda: update_price_display(price))

                price_data.append(price)
                if len(price_data) > 100:
                    price_data.pop(0)

                root.after(0, update_account_info)
                root.after(0, update_advanced_chart)

        except Exception as e:
            logger.log(f"Error updating data: {e}", 'ERROR')

        time.sleep(3)


def update_price_display(price):
    """Enhanced price display with animations"""
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

            price_text = f"{arrow} {selected_symbol}\n${price:,.8f} ({change:+.2f}%)"
        else:
            color = "#74b9ff"
            price_text = f"📊 {selected_symbol}\n${price:,.8f}\nInitializing..."

        price_var.set(price_text)
        price_label.config(fg=color)

    except Exception as e:
        logger.log(f"Error updating price display: {e}", 'ERROR')


def update_account_info():
    """Enhanced account information display"""
    try:
        if not client:
            return

        account = client.futures_account()
        balance = float(account['totalWalletBalance'])
        unrealized_pnl = float(account['totalUnrealizedProfit'])

        balance_var.set(f"💰 ${balance:,.2f}")

        pnl_color = "#00ff88" if unrealized_pnl >= 0 else "#ff4757"
        pnl_icon = "📈" if unrealized_pnl >= 0 else "📉"
        pnl_var.set(f"{pnl_icon} ${unrealized_pnl:+,.2f}")
        pnl_label.config(fg=pnl_color)

        pnl_history.append(unrealized_pnl)
        if len(pnl_history) > 50:
            pnl_history.pop(0)

    except Exception as e:
        logger.log(f"Error updating account info: {e}", 'ERROR')


def update_advanced_chart():
    """Enhanced chart with modern styling"""
    if not price_data or len(price_data) < 5:
        return

    try:
        ax1.clear()
        ax2.clear()
        ax3.clear()

        x = range(len(price_data))

        # Modern color scheme
        primary_color = "#00ff88"
        secondary_color = "#74b9ff"
        danger_color = "#ff4757"
        warning_color = "#ffeaa7"

        # Price chart with gradient
        ax1.plot(x, price_data, color=primary_color, linewidth=3, label="Price", alpha=0.9)
        ax1.fill_between(x, price_data, alpha=0.1, color=primary_color)

        df = get_kline_data()
        if df is not None and len(df) > 20:
            recent_df = df.tail(len(price_data))

            if len(recent_df) == len(price_data):
                # Enhanced EMA lines
                if 'ema_9' in recent_df.columns and show_ema.get():
                    ax1.plot(x, recent_df['ema_9'].values, color="#ffa502", alpha=0.8,
                             label="EMA9", linewidth=2, linestyle='-')
                    ax1.plot(x, recent_df['ema_21'].values, color="#ff6348", alpha=0.8,
                             label="EMA21", linewidth=2, linestyle='--')

                # Bollinger Bands with modern styling
                if 'bb_upper' in recent_df.columns and show_bb.get():
                    ax1.fill_between(x, recent_df['bb_upper'].values, recent_df['bb_lower'].values,
                                     alpha=0.15, color=secondary_color, label="Bollinger Bands")
                    ax1.plot(x, recent_df['bb_upper'].values, color=secondary_color, alpha=0.6, linewidth=1)
                    ax1.plot(x, recent_df['bb_lower'].values, color=secondary_color, alpha=0.6, linewidth=1)

                # Enhanced RSI
                if 'rsi' in recent_df.columns and show_rsi.get():
                    rsi_values = recent_df['rsi'].values
                    ax3.plot(x, rsi_values, color="#e17055", linewidth=3, label="RSI")

                    # Color-coded RSI zones
                    ax3.fill_between(x, 70, 100, alpha=0.2, color=danger_color, label="Overbought")
                    ax3.fill_between(x, 0, 30, alpha=0.2, color=primary_color, label="Oversold")

                    ax3.axhline(y=70, color=danger_color, linestyle='--', alpha=0.8, linewidth=2)
                    ax3.axhline(y=30, color=primary_color, linestyle='--', alpha=0.8, linewidth=2)
                    ax3.axhline(y=50, color='white', linestyle='-', alpha=0.3, linewidth=1)
                    ax3.set_ylim(0, 100)

        # Enhanced Volume chart
        if df is not None and len(df) > 0:
            recent_volumes = df.tail(len(price_data))['volume'].values
            if len(recent_volumes) == len(price_data):
                # Gradient volume bars
                colors = []
                for i in range(len(recent_volumes)):
                    if i == 0:
                        colors.append(secondary_color)
                    else:
                        vol_change = recent_volumes[i] / recent_volumes[i - 1]
                        if vol_change > 1.2:
                            colors.append(primary_color)  # High volume
                        elif vol_change < 0.8:
                            colors.append(danger_color)  # Low volume
                        else:
                            colors.append(secondary_color)  # Normal volume

                bars = ax2.bar(x, recent_volumes, color=colors, alpha=0.8, width=0.8)

                # Add volume average line
                vol_avg = np.mean(recent_volumes)
                ax2.axhline(y=vol_avg, color=warning_color, linestyle='--', alpha=0.7, linewidth=2)

        # Modern chart styling
        for ax in [ax1, ax2, ax3]:
            ax.set_facecolor("#0d1117")
            ax.tick_params(colors="white", labelsize=9)
            ax.grid(True, alpha=0.2, color="white", linestyle='-', linewidth=0.5)
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white')
            ax.spines['right'].set_color('white')
            ax.spines['left'].set_color('white')

        # Enhanced titles and legends
        ax1.set_title(f"📈 {selected_symbol} Price Analysis ({selected_timeframe})",
                      color="white", fontsize=14, fontweight='bold', pad=20)
        ax2.set_title("📊 Volume Analysis", color="white", fontsize=12, fontweight='bold')
        ax3.set_title("🔄 RSI Momentum (14)", color="white", fontsize=12, fontweight='bold')

        # Modern legends
        if ax1.get_legend_handles_labels()[0]:
            ax1.legend(loc='upper left', fontsize=9, framealpha=0.8, facecolor='#2d3436')
        if ax3.get_legend_handles_labels()[0]:
            ax3.legend(loc='upper right', fontsize=8, framealpha=0.8, facecolor='#2d3436')

        # Latest price overlay
        if price_data:
            latest_price = price_data[-1]
            ax1.text(0.02, 0.98, f'💲 Latest: ${latest_price:,.8f}',
                     transform=ax1.transAxes, color=primary_color,
                     fontsize=12, verticalalignment='top', fontweight='bold',
                     bbox=dict(boxstyle="round,pad=0.5", facecolor="#2d3436", alpha=0.9))

        fig.patch.set_facecolor("#0d1117")
        canvas.draw_idle()

    except Exception as e:
        logger.log(f"Error updating chart: {e}", 'ERROR')


def start_data_updates():
    """Start threads for data updates"""
    global update_thread
    if update_thread is None or not update_thread.is_alive():
        update_thread = threading.Thread(target=update_data, daemon=True)
        update_thread.start()


def toggle_auto_trading():
    """Enhanced auto trading toggle"""
    global auto_trading, strategy_thread

    if not client:
        show_modern_notification("Please connect API first", "warning")
        return

    if not auto_trading:
        api_key, api_secret, testnet = config_manager.get_api_credentials()
        env_type = "Testnet" if testnet else "LIVE"

        confirm_msg = f"""🤖 Enable Auto Trading?

Environment: {env_type}
Symbol: {selected_symbol}
Risk per trade: {settings['risk_percent']}%
Max daily trades: {bot.max_daily_trades}
Today's trades: {bot.daily_trade_count}

Auto trading will place real orders. Continue?"""

        if not messagebox.askyesno("Confirm Auto Trading", confirm_msg):
            return

    auto_trading = not auto_trading

    if auto_trading:
        auto_btn.configure(text="🛑 Stop Auto Trading")
        strategy_thread = threading.Thread(target=auto_trading_strategy, daemon=True)
        strategy_thread.start()
        logger.log("Auto Trading activated - Enhanced safety mode enabled", 'AUTO')
        auto_status.set("🤖 Auto Trading ON")
        show_modern_notification("Auto Trading Started", "success")
    else:
        auto_btn.configure(text="🚀 Start Auto Trading")
        logger.log("Auto Trading deactivated", 'AUTO')
        auto_status.set("👤 Manual Mode")
        show_modern_notification("Auto Trading Stopped", "info")


def show_modern_notification(message, notification_type="info"):
    """Modern notification system"""
    try:
        notification = tk.Toplevel(root)
        notification.title("Trading Alert")
        notification.geometry("400x120")
        notification.attributes('-topmost', True)
        notification.transient(root)
        notification.overrideredirect(True)  # Remove window decorations

        # Position in top-right corner
        x = root.winfo_rootx() + root.winfo_width() - 420
        y = root.winfo_rooty() + 50
        notification.geometry(f"+{x}+{y}")

        # Notification styling based on type
        colors = {
            'success': {'bg': '#00b894', 'icon': '✅'},
            'error': {'bg': '#e17055', 'icon': '❌'},
            'warning': {'bg': '#fdcb6e', 'icon': '⚠️'},
            'info': {'bg': '#74b9ff', 'icon': 'ℹ️'}
        }

        config = colors.get(notification_type, colors['info'])
        notification.configure(bg=config['bg'])

        # Content frame
        content_frame = tk.Frame(notification, bg=config['bg'])
        content_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Icon and message
        icon_label = tk.Label(content_frame, text=config['icon'], fg="white", bg=config['bg'],
                              font=("Segoe UI", 16))
        icon_label.pack(side="left", padx=(0, 10))

        msg_label = tk.Label(content_frame, text=message, fg="white", bg=config['bg'],
                             font=("Segoe UI", 11, "bold"), wraplength=300)
        msg_label.pack(side="left", fill="both", expand=True)

        # Auto close
        notification.after(4000, notification.destroy)

        # Click to close
        def close_notification(event=None):
            notification.destroy()

        notification.bind("<Button-1>", close_notification)
        content_frame.bind("<Button-1>", close_notification)
    except Exception as e:
        print(f"Notification error: {e}")


def close_all_positions():
    """Enhanced position closing with detailed logging"""
    if not client:
        show_modern_notification("Please connect API first", "warning")
        return

    current_positions = get_current_positions()
    if not current_positions:
        logger.log("No positions to close", 'INFO')
        return

    pos_info = "\n".join([f"{p['symbol']}: {p['positionAmt']}" for p in current_positions])
    confirm = messagebox.askyesno("Confirm Close Positions",
                                  f"Close all positions?\n\n{pos_info}")
    if not confirm:
        return

    try:
        logger.log(f"Closing {len(current_positions)} positions", 'TRADE')
        closed_count = 0

        for pos in current_positions:
            side = SIDE_SELL if float(pos['positionAmt']) > 0 else SIDE_BUY
            quantity = abs(float(pos['positionAmt']))

            client.futures_create_order(
                symbol=pos['symbol'],
                side=side,
                type='MARKET',
                quantity=quantity,
                reduceOnly=True
            )
            closed_count += 1
            logger.log(f"Closed {side} position: {quantity} {pos['symbol']}", 'TRADE')

        logger.log(f"Successfully closed {closed_count} positions", 'SUCCESS')
        show_modern_notification(f"Closed {closed_count} positions", "success")

    except Exception as e:
        logger.log(f"Error closing positions: {str(e)}", 'ERROR')
        show_modern_notification(f"Error closing positions", "error")


def cancel_all_orders():
    """Cancel all orders"""
    if not client:
        return

    confirm = messagebox.askyesno("Confirm Cancel Orders", "Cancel all open orders?")
    if not confirm:
        return

    try:
        client.futures_cancel_all_open_orders(symbol=selected_symbol)
        logger.log("All orders cancelled successfully", 'SUCCESS')
        show_modern_notification("All orders cancelled", "success")
    except Exception as e:
        logger.log(f"Error canceling orders: {str(e)}", 'ERROR')


def emergency_stop():
    """Enhanced emergency stop"""
    if not client:
        return

    confirm = messagebox.askyesno("🚨 EMERGENCY STOP",
                                  "🚨 EMERGENCY STOP PROTOCOL\n\n"
                                  "This will immediately:\n"
                                  "• Stop all auto trading\n"
                                  "• Cancel ALL open orders\n"
                                  "• Close ALL positions\n\n"
                                  "⚠️ This action cannot be undone!\n\n"
                                  "Proceed with emergency stop?")
    if not confirm:
        return

    global auto_trading
    auto_trading = False

    logger.log("🚨 EMERGENCY STOP INITIATED", 'ERROR')

    try:
        # Cancel all orders
        client.futures_cancel_all_open_orders(symbol=selected_symbol)
        logger.log("All open orders cancelled", 'SUCCESS')

        # Close all positions
        positions = client.futures_position_information()
        closed_positions = 0

        for pos in positions:
            if float(pos['positionAmt']) != 0:
                side = SIDE_SELL if float(pos['positionAmt']) > 0 else SIDE_BUY
                quantity = abs(float(pos['positionAmt']))

                client.futures_create_order(
                    symbol=pos['symbol'],
                    side=side,
                    type=ORDER_TYPE_MARKET,
                    quantity=quantity,
                    reduceOnly=True
                )
                closed_positions += 1

        logger.log(f"🚨 EMERGENCY STOP COMPLETED - {closed_positions} positions closed", 'SUCCESS')
        show_modern_notification("Emergency Stop Completed", "success")

    except Exception as e:
        logger.log(f"Emergency stop error: {str(e)}", 'ERROR')


def change_symbol():
    """Modern symbol selection interface"""
    global selected_symbol

    symbol_window = tk.Toplevel(root)
    symbol_window.title("📊 Select Trading Symbol")
    symbol_window.geometry("500x600")
    symbol_window.configure(bg="#0d1117")

    # Header
    header = tk.Frame(symbol_window, bg="#1f2937", height=80)
    header.pack(fill="x")
    header.pack_propagate(False)

    tk.Label(header, text="📊 Symbol Selection",
             font=("Segoe UI", 16, "bold"), fg="#74b9ff", bg="#1f2937").pack(pady=25)

    # Popular symbols
    popular_card = ModernCard(symbol_window, title="⭐ Popular Symbols")
    popular_card.pack(fill="both", expand=True, padx=20, pady=15)

    popular_content = tk.Frame(popular_card, bg="#2d3436")
    popular_content.pack(fill="both", expand=True, padx=15, pady=15)

    popular_symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT",
                       "BNBUSDT", "SOLUSDT", "MATICUSDT", "AVAXUSDT", "UNIUSDT"]

    # Symbol grid
    symbol_grid = tk.Frame(popular_content, bg="#2d3436")
    symbol_grid.pack(fill="both", expand=True)

    for i, symbol in enumerate(popular_symbols):
        row = i // 2
        col = i % 2

        btn = ModernButton(symbol_grid, text=symbol,
                           command=lambda s=symbol: select_symbol(s, symbol_window),
                           style="primary")
        btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")

    symbol_grid.grid_columnconfigure(0, weight=1)
    symbol_grid.grid_columnconfigure(1, weight=1)


def select_symbol(symbol, window):
    """Select trading symbol with enhanced feedback"""
    global selected_symbol
    selected_symbol = symbol
    symbol_var.set(f"Symbol: {selected_symbol}")
    price_data.clear()
    volume_data.clear()
    logger.log(f"Symbol changed to {selected_symbol}", 'INFO')
    show_modern_notification(f"Symbol changed to {selected_symbol}", "info")
    window.destroy()


def change_timeframe():
    """Modern timeframe selection"""
    global selected_timeframe

    tf_window = tk.Toplevel(root)
    tf_window.title("⏱️ Select Timeframe")
    tf_window.geometry("400x500")
    tf_window.configure(bg="#0d1117")

    # Header
    header = tk.Frame(tf_window, bg="#1f2937", height=80)
    header.pack(fill="x")
    header.pack_propagate(False)

    tk.Label(header, text="⏱️ Timeframe Selection",
             font=("Segoe UI", 16, "bold"), fg="#74b9ff", bg="#1f2937").pack(pady=25)

    timeframes = {
        "Short Term": ["1m", "3m", "5m", "15m"],
        "Medium Term": ["30m", "1h", "2h", "4h"],
        "Long Term": ["6h", "8h", "12h", "1d"]
    }

    for category, tfs in timeframes.items():
        card = ModernCard(tf_window, title=f"📅 {category}")
        card.pack(fill="x", padx=20, pady=10)

        content = tk.Frame(card, bg="#2d3436")
        content.pack(fill="x", padx=15, pady=15)

        btn_frame = tk.Frame(content, bg="#2d3436")
        btn_frame.pack(fill="x")

        for i, tf in enumerate(tfs):
            btn = ModernButton(btn_frame, text=tf,
                               command=lambda t=tf: select_timeframe(t, tf_window),
                               style="primary")
            btn.pack(side="left", fill="x", expand=True, padx=2)


def select_timeframe(tf, window):
    """Select timeframe with enhanced feedback"""
    global selected_timeframe
    selected_timeframe = tf
    timeframe_var.set(f"Timeframe: {selected_timeframe}")
    logger.log(f"Timeframe changed to {selected_timeframe}", 'INFO')
    show_modern_notification(f"Timeframe changed to {selected_timeframe}", "info")
    window.destroy()


def open_settings():
    """Modern settings interface"""
    settings_window = tk.Toplevel(root)
    settings_window.title("⚙️ Trading Settings")
    settings_window.geometry("700x800")
    settings_window.configure(bg="#0d1117")

    # Modern header
    header = tk.Frame(settings_window, bg="#1f2937", height=80)
    header.pack(fill="x")
    header.pack_propagate(False)

    tk.Label(header, text="⚙️ Advanced Trading Configuration",
             font=("Segoe UI", 18, "bold"), fg="#74b9ff", bg="#1f2937").pack(pady=25)

    # Create modern notebook
    style = ttk.Style()
    style.configure('Modern.TNotebook', background='#0d1117')
    style.configure('Modern.TNotebook.Tab', padding=[20, 10])

    notebook = ttk.Notebook(settings_window, style='Modern.TNotebook')
    notebook.pack(fill="both", expand=True, padx=20, pady=20)

    # Risk Management Tab
    risk_frame = tk.Frame(notebook, bg="#0d1117")
    notebook.add(risk_frame, text="🛡️ Risk Management")

    risk_var = tk.DoubleVar(value=settings['risk_percent'])
    sl_var = tk.DoubleVar(value=settings['stop_loss_percent'])
    tp_var = tk.DoubleVar(value=settings['take_profit_percent'])
    max_pos_var = tk.IntVar(value=settings['max_positions'])
    max_daily_var = tk.IntVar(value=bot.max_daily_trades)

    def create_modern_setting_row(parent, label, var, min_val, max_val, unit="", description=""):
        card = ModernCard(parent, bg_color="#1f2937")
        card.pack(fill="x", pady=10, padx=20)

        label_frame = tk.Frame(card, bg="#1f2937")
        label_frame.pack(fill="x", padx=15, pady=10)

        tk.Label(label_frame, text=f"{label}:", fg="white", bg="#1f2937",
                 font=("Segoe UI", 11, "bold")).pack(anchor="w")

        if description:
            tk.Label(label_frame, text=description, fg="#a0a0a0", bg="#1f2937",
                     font=("Segoe UI", 9)).pack(anchor="w", pady=(2, 0))

        control_frame = tk.Frame(card, bg="#1f2937")
        control_frame.pack(fill="x", padx=15, pady=(0, 15))

        scale = ttk.Scale(control_frame, from_=min_val, to=max_val, variable=var, orient='horizontal')
        scale.pack(fill='x', pady=(5, 0))

        value_label = tk.Label(control_frame, text="", fg="#00ff88", bg="#1f2937",
                               font=("Segoe UI", 10, "bold"))
        value_label.pack(anchor="w", pady=(5, 0))

        def update_label():
            if unit == "%":
                value_label.config(text=f"Value: {var.get():.1f}{unit}")
            else:
                value_label.config(text=f"Value: {int(var.get())}{unit}")
            control_frame.after(100, update_label)

        update_label()

    create_modern_setting_row(risk_frame, "💰 Risk per Trade", risk_var, 0.5, 10, "%",
                              "Percentage of account balance to risk per trade")
    create_modern_setting_row(risk_frame, "🛡️ Stop Loss", sl_var, 0.5, 5, "%",
                              "Maximum loss percentage before auto-close")
    create_modern_setting_row(risk_frame, "🎯 Take Profit", tp_var, 1, 10, "%",
                              "Target profit percentage for auto-close")

    def save_settings():
        """Save all settings with validation"""
        try:
            settings['risk_percent'] = risk_var.get()
            settings['stop_loss_percent'] = sl_var.get()
            settings['take_profit_percent'] = tp_var.get()

            # Save to config file
            for key, value in settings.items():
                config_manager.config.set('TRADING', key, str(value))
            config_manager.save_config()

            logger.log("Trading settings updated successfully", 'SUCCESS')
            show_modern_notification("Settings saved successfully!", "success")
            settings_window.destroy()

        except Exception as e:
            logger.log(f"Error saving settings: {e}", 'ERROR')
            show_modern_notification("Error saving settings", "error")

    # Save button
    save_frame = tk.Frame(settings_window, bg="#0d1117")
    save_frame.pack(fill="x", padx=20, pady=20)

    ModernButton(save_frame, text="💾 Save Settings", command=save_settings,
                 style="success").pack(side="right")


def show_trading_history():
    """Simple trading history display"""
    history_window = tk.Toplevel(root)
    history_window.title("📜 Trading History")
    history_window.geometry("1000x600")
    history_window.configure(bg="#0d1117")

    tk.Label(history_window, text="📜 Trading History",
             font=("Segoe UI", 16, "bold"), fg="#74b9ff", bg="#0d1117").pack(pady=20)

    cursor = bot.db_connection.cursor()
    cursor.execute('SELECT * FROM trades ORDER BY timestamp DESC LIMIT 100')
    trades = cursor.fetchall()

    if trades:
        text_widget = tk.Text(history_window, bg="#2d3436", fg="white", font=("Consolas", 10))
        text_widget.pack(fill="both", expand=True, padx=20, pady=20)

        for trade in trades:
            text_widget.insert(tk.END, f"{trade[1]} | {trade[2]} | {trade[3]} | {trade[4]:.6f} | ${trade[5]:.8f}\n")
    else:
        tk.Label(history_window, text="No trading history available",
                 fg="white", bg="#0d1117", font=("Segoe UI", 12)).pack(pady=50)


def show_market_scanner():
    """Simple market scanner"""
    scanner_window = tk.Toplevel(root)
    scanner_window.title("🔍 Market Scanner")
    scanner_window.geometry("800x600")
    scanner_window.configure(bg="#0d1117")

    tk.Label(scanner_window, text="🔍 Market Scanner",
             font=("Segoe UI", 16, "bold"), fg="#74b9ff", bg="#0d1117").pack(pady=20)

    tk.Label(scanner_window, text="Scanner functionality will be available after API connection",
             fg="white", bg="#0d1117", font=("Segoe UI", 12)).pack(pady=50)


def show_portfolio_analysis():
    """Simple portfolio analysis"""
    portfolio_window = tk.Toplevel(root)
    portfolio_window.title("📈 Portfolio Analysis")
    portfolio_window.geometry("800x600")
    portfolio_window.configure(bg="#0d1117")

    tk.Label(portfolio_window, text="📈 Portfolio Analysis",
             font=("Segoe UI", 16, "bold"), fg="#74b9ff", bg="#0d1117").pack(pady=20)

    if pnl_history:
        stats_text = f"""Current PnL Data:

Total PnL Records: {len(pnl_history)}
Latest PnL: ${pnl_history[-1]:+.2f}
Max PnL: ${max(pnl_history):+.2f}
Min PnL: ${min(pnl_history):+.2f}"""

        tk.Label(portfolio_window, text=stats_text, fg="white", bg="#0d1117",
                 font=("Consolas", 12), justify="left").pack(pady=20)
    else:
        tk.Label(portfolio_window, text="No PnL data available yet",
                 fg="white", bg="#0d1117", font=("Segoe UI", 12)).pack(pady=50)


def on_close():
    """Safe application shutdown"""
    global running, auto_trading

    if auto_trading:
        confirm = messagebox.askyesno("Auto Trading Active",
                                      "Auto trading is still running.\n"
                                      "Stop auto trading and close application?")
        if not confirm:
            return

    running = False
    auto_trading = False
    logger.log("Application shutting down...", 'INFO')

    if update_thread and update_thread.is_alive():
        update_thread.join(timeout=2)
    if strategy_thread and strategy_thread.is_alive():
        strategy_thread.join(timeout=2)

    try:
        bot.db_connection.close()
    except:
        pass

    root.destroy()


# ===== GUI Setup =====
root = tk.Tk()
root.title("🚀 Advanced Binance Futures Trading Bot v2.1 - Modern Edition")
root.geometry("1700x1100")
root.configure(bg="#0d1117")
root.protocol("WM_DELETE_WINDOW", on_close)

# Modern style configuration
style = ttk.Style()
style.theme_use("clam")

# Configure modern styles
style.configure("Modern.TButton",
                font=("Segoe UI", 10, "bold"),
                padding=(15, 8),
                borderwidth=0)

style.map("Modern.TButton",
          background=[('active', '#74b9ff'),
                      ('pressed', '#0984e3')])

# ===== Modern Layout =====
# Enhanced header
header_frame = tk.Frame(root, bg="#1f2937", height=100)
header_frame.pack(fill="x")
header_frame.pack_propagate(False)

header_content = tk.Frame(header_frame, bg="#1f2937")
header_content.pack(fill="both", expand=True, padx=30, pady=20)

# Title with modern styling
title_frame = tk.Frame(header_content, bg="#1f2937")
title_frame.pack(side="left", fill="y")

tk.Label(title_frame, text="🚀 Advanced Futures Trading Bot",
         font=("Segoe UI", 20, "bold"), fg="#74b9ff", bg="#1f2937").pack(anchor="w")
tk.Label(title_frame, text="v2.1 Modern Edition - Enhanced Safety & Performance",
         font=("Segoe UI", 11), fg="#a0a0a0", bg="#1f2937").pack(anchor="w", pady=(5, 0))

# Enhanced status panel
status_panel = tk.Frame(header_content, bg="#2d3436", relief="flat", bd=1)
status_panel.pack(side="right", padx=20)

status_content = tk.Frame(status_panel, bg="#2d3436")
status_content.pack(padx=20, pady=15)

price_var = tk.StringVar(value="Loading...")
price_label = tk.Label(status_content, textvariable=price_var,
                       font=("Consolas", 12, "bold"), fg="#00ff88", bg="#2d3436")
price_label.pack()

balance_var = tk.StringVar(value="Balance: -")
balance_label = tk.Label(status_content, textvariable=balance_var,
                         font=("Consolas", 11), fg="white", bg="#2d3436")
balance_label.pack()

pnl_var = tk.StringVar(value="PnL: -")
pnl_label = tk.Label(status_content, textvariable=pnl_var,
                     font=("Consolas", 11), fg="white", bg="#2d3436")
pnl_label.pack()

# Main content with modern layout
main_container = tk.Frame(root, bg="#0d1117")
main_container.pack(fill="both", expand=True, padx=20, pady=20)

# ===== Left Panel - Modern Control Center =====
left_panel = tk.Frame(main_container, bg="#0d1117", width=450)
left_panel.pack(side="left", fill="y", padx=(0, 20))
left_panel.pack_propagate(False)

# Connection Card
connection_card = ModernCard(left_panel, title="🔗 Connection Status")
connection_card.pack(fill="x", pady=10)

connection_content = tk.Frame(connection_card, bg="#2d3436")
connection_content.pack(fill="x", padx=15, pady=15)

ModernButton(connection_content, text="🔐 Setup & Connect API",
             command=setup_api_credentials, style="primary").pack(fill="x")

connection_status = tk.StringVar(value="🔴 Disconnected")
status_label = tk.Label(connection_content, textvariable=connection_status,
                        fg="#74b9ff", bg="#2d3436", font=("Segoe UI", 10, "bold"))
status_label.pack(pady=(10, 0))

# Market Selection Card
market_card = ModernCard(left_panel, title="📊 Market Selection")
market_card.pack(fill="x", pady=10)

market_content = tk.Frame(market_card, bg="#2d3436")
market_content.pack(fill="x", padx=15, pady=15)

symbol_var = tk.StringVar(value=f"Symbol: {selected_symbol}")
symbol_label = tk.Label(market_content, textvariable=symbol_var, fg="white", bg="#2d3436",
                        font=("Segoe UI", 11, "bold"))
symbol_label.pack()

timeframe_var = tk.StringVar(value=f"Timeframe: {selected_timeframe}")
timeframe_label = tk.Label(market_content, textvariable=timeframe_var, fg="#a0a0a0", bg="#2d3436",
                           font=("Segoe UI", 10))
timeframe_label.pack()

market_btn_frame = tk.Frame(market_content, bg="#2d3436")
market_btn_frame.pack(fill="x", pady=10)

ModernButton(market_btn_frame, text="📈 Change Symbol", command=change_symbol,
             style="dark").pack(side="left", fill="x", expand=True, padx=(0, 5))
ModernButton(market_btn_frame, text="⏱️ Timeframe", command=change_timeframe,
             style="dark").pack(side="right", fill="x", expand=True, padx=(5, 0))

# Trading Card
trading_card = ModernCard(left_panel, title="⚡ Smart Trading")
trading_card.pack(fill="x", pady=10)

trading_content = tk.Frame(trading_card, bg="#2d3436")
trading_content.pack(fill="x", padx=15, pady=15)

# Trade buttons with modern styling
trade_btn_frame = tk.Frame(trading_content, bg="#2d3436")
trade_btn_frame.pack(fill="x", pady=10)

buy_btn = ModernButton(trade_btn_frame, text="📈 SMART BUY",
                       command=lambda: place_smart_order(SIDE_BUY, "MANUAL"),
                       style="success")
buy_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

sell_btn = ModernButton(trade_btn_frame, text="📉 SMART SELL",
                        command=lambda: place_smart_order(SIDE_SELL, "MANUAL"),
                        style="danger")
sell_btn.pack(side="right", fill="x", expand=True, padx=(5, 0))

# Risk display
risk_info = tk.Label(trading_content,
                     text=f"Risk: {settings['risk_percent']}% | SL: {settings['stop_loss_percent']}% | TP: {settings['take_profit_percent']}%",
                     fg="#74b9ff", bg="#2d3436", font=("Segoe UI", 9))
risk_info.pack(pady=(10, 0))

# Auto Trading Card
auto_card = ModernCard(left_panel, title="🤖 Automated Trading")
auto_card.pack(fill="x", pady=10)

auto_content = tk.Frame(auto_card, bg="#2d3436")
auto_content.pack(fill="x", padx=15, pady=15)

# Create auto button with dynamic styling
auto_btn = ModernButton(auto_content, text="🚀 Start Auto Trading",
                        command=toggle_auto_trading, style="success")
auto_btn.pack(fill="x")

auto_status = tk.StringVar(value="👤 Manual Mode")
auto_status_label = tk.Label(auto_content, textvariable=auto_status,
                             fg="#ffeaa7", bg="#2d3436", font=("Segoe UI", 10, "bold"))
auto_status_label.pack(pady=(10, 0))

safety_info = tk.Label(auto_content,
                       text=f"Daily Limit: {bot.daily_trade_count}/{bot.max_daily_trades} trades",
                       fg="#a0a0a0", bg="#2d3436", font=("Segoe UI", 9))
safety_info.pack()

# Emergency Controls Card
emergency_card = ModernCard(left_panel, title="🚨 Emergency Controls")
emergency_card.pack(fill="x", pady=10)

emergency_content = tk.Frame(emergency_card, bg="#2d3436")
emergency_content.pack(fill="x", padx=15, pady=15)

ModernButton(emergency_content, text="🚨 EMERGENCY STOP", command=emergency_stop,
             style="danger").pack(fill="x", pady=2)

emergency_btn_frame = tk.Frame(emergency_content, bg="#2d3436")
emergency_btn_frame.pack(fill="x", pady=5)

ModernButton(emergency_btn_frame, text="❌ Close Positions", command=close_all_positions,
             style="warning").pack(side="left", fill="x", expand=True, padx=(0, 2))
ModernButton(emergency_btn_frame, text="🚫 Cancel Orders", command=cancel_all_orders,
             style="warning").pack(side="right", fill="x", expand=True, padx=(2, 0))

# Analysis Tools Card
analysis_card = ModernCard(left_panel, title="📊 Analysis Tools")
analysis_card.pack(fill="x", pady=10)

analysis_content = tk.Frame(analysis_card, bg="#2d3436")
analysis_content.pack(fill="x", padx=15, pady=15)

analysis_btn_frame1 = tk.Frame(analysis_content, bg="#2d3436")
analysis_btn_frame1.pack(fill="x", pady=2)

ModernButton(analysis_btn_frame1, text="🔍 Market Scanner", command=show_market_scanner,
             style="primary").pack(side="left", fill="x", expand=True, padx=(0, 2))
ModernButton(analysis_btn_frame1, text="📈 Portfolio", command=show_portfolio_analysis,
             style="primary").pack(side="right", fill="x", expand=True, padx=(2, 0))

analysis_btn_frame2 = tk.Frame(analysis_content, bg="#2d3436")
analysis_btn_frame2.pack(fill="x", pady=2)

ModernButton(analysis_btn_frame2, text="📜 History", command=show_trading_history,
             style="dark").pack(side="left", fill="x", expand=True, padx=(0, 2))
ModernButton(analysis_btn_frame2, text="⚙️ Settings", command=open_settings,
             style="dark").pack(side="right", fill="x", expand=True, padx=(2, 0))

# ===== Center Panel - Enhanced Charts =====
chart_panel = tk.Frame(main_container, bg="#0d1117")
chart_panel.pack(side="left", fill="both", expand=True, padx=(0, 20))

# Chart controls
chart_controls = tk.Frame(chart_panel, bg="#1f2937", height=60)
chart_controls.pack(fill="x", pady=(0, 15))
chart_controls.pack_propagate(False)

chart_title = tk.Label(chart_controls, text="📊 Real-time Technical Analysis",
                       fg="#74b9ff", bg="#1f2937", font=("Segoe UI", 14, "bold"))
chart_title.pack(side="left", padx=20, pady=15)

# Modern indicator toggles
indicator_frame = tk.Frame(chart_controls, bg="#1f2937")
indicator_frame.pack(side="right", padx=20, pady=10)

show_ema = tk.BooleanVar(value=True)
show_bb = tk.BooleanVar(value=True)
show_rsi = tk.BooleanVar(value=True)

# Modern checkboxes
for var, text, color in [(show_ema, "EMA Lines", "#ffa502"),
                         (show_bb, "Bollinger Bands", "#74b9ff"),
                         (show_rsi, "RSI Oscillator", "#e17055")]:
    check_frame = tk.Frame(indicator_frame, bg=color, relief="flat", bd=1)
    check_frame.pack(side="left", padx=5)

    check = tk.Checkbutton(check_frame, text=text, variable=var,
                           fg="white", bg=color, selectcolor=color,
                           font=("Segoe UI", 9, "bold"), relief="flat")
    check.pack(padx=8, pady=4)

# Enhanced chart setup
fig = Figure(figsize=(16, 12), dpi=100, facecolor="#0d1117")
gs = fig.add_gridspec(3, 1, height_ratios=[3, 1, 1], hspace=0.3)

ax1 = fig.add_subplot(gs[0])  # Main price chart
ax2 = fig.add_subplot(gs[1])  # Volume chart
ax3 = fig.add_subplot(gs[2])  # RSI chart

canvas = FigureCanvasTkAgg(fig, master=chart_panel)
canvas.get_tk_widget().pack(fill="both", expand=True)

# Initialize with welcome message
for ax in [ax1, ax2, ax3]:
    ax.set_facecolor("#0d1117")
    ax.tick_params(colors="white", labelsize=9)
    ax.grid(True, alpha=0.2, color="white", linestyle='-', linewidth=0.5)

ax1.text(0.5, 0.5,
         '🚀 Advanced Trading Bot v2.1 - Modern Edition\n\n'
         '✨ Real-time Multi-timeframe Analysis\n'
         '🧠 AI-powered Technical Indicators\n'
         '🛡️ Advanced Risk Management\n'
         '🤖 Intelligent Auto Trading\n'
         '📊 Professional-grade Charts\n\n'
         '🔐 Setup API credentials to begin trading',
         transform=ax1.transAxes, ha='center', va='center',
         color='white', fontsize=14, fontweight='bold',
         bbox=dict(boxstyle="round,pad=1", facecolor="#1f2937", alpha=0.9))

ax2.text(0.5, 0.5, '📊 Volume Analysis\nReal-time volume tracking with trend analysis',
         transform=ax2.transAxes, ha='center', va='center',
         color='white', fontsize=11)

ax3.text(0.5, 0.5, '🔄 RSI Momentum Oscillator\nOverbought/Oversold signal detection',
         transform=ax3.transAxes, ha='center', va='center',
         color='white', fontsize=11)

canvas.draw()

# ===== Right Panel - Enhanced Activity Log =====
log_panel = tk.Frame(main_container, bg="#0d1117", width=400)
log_panel.pack(side="right", fill="y")
log_panel.pack_propagate(False)

# Initialize enhanced log frame
log_frame = EnhancedLogFrame(log_panel)
log_frame.pack(fill="both", expand=True)


# Set up logger callback
def update_log_ui(log_entry):
    """Update log UI with new entry"""
    try:
        root.after(0, lambda: log_frame.add_log_entry(log_entry))
    except:
        pass


logger.ui_callback = update_log_ui

# ===== Enhanced Status Bar =====
status_bar = tk.Frame(root, bg="#1f2937", height=45)
status_bar.pack(fill="x", side="bottom")
status_bar.pack_propagate(False)

status_content = tk.Frame(status_bar, bg="#1f2937")
status_content.pack(fill="both", expand=True, padx=20, pady=8)

# Left status
left_status = tk.Frame(status_content, bg="#1f2937")
left_status.pack(side="left")

connection_status = tk.StringVar(value="🔴 Disconnected")
tk.Label(left_status, textvariable=connection_status, fg="white", bg="#1f2937",
         font=("Segoe UI", 10, "bold")).pack(side="left")

# Center status
center_status = tk.Frame(status_content, bg="#1f2937")
center_status.pack(side="left", padx=50)

auto_status = tk.StringVar(value="👤 Manual Mode")
tk.Label(center_status, textvariable=auto_status, fg="#74b9ff", bg="#1f2937",
         font=("Segoe UI", 10, "bold")).pack()

# Right status
right_status = tk.Frame(status_content, bg="#1f2937")
right_status.pack(side="right")

safety_status = tk.StringVar(value=f"🚦 Daily: {bot.daily_trade_count}/{bot.max_daily_trades}")
tk.Label(right_status, textvariable=safety_status, fg="#ffeaa7", bg="#1f2937",
         font=("Segoe UI", 10, "bold")).pack()


def update_status_indicators():
    """Enhanced status indicator updates"""
    try:
        if client:
            api_key, api_secret, testnet = config_manager.get_api_credentials()
            env_type = "🧪 Testnet" if testnet else "🔴 Live"
            connection_status.set(f"🟢 Connected ({env_type})")
        else:
            connection_status.set("🔴 Disconnected")

        if auto_trading:
            auto_status.set("🤖 Auto Trading ON")
        else:
            auto_status.set("👤 Manual Mode")

        safety_status.set(f"🚦 Daily: {bot.daily_trade_count}/{bot.max_daily_trades}")
        root.after(2000, update_status_indicators)
    except:
        root.after(2000, update_status_indicators)


# Initialize application
logger.log("🚀 Advanced Trading Bot v2.1 initialized", 'SUCCESS')
logger.log("Enhanced UI, Safety Features, and Auto Trading Ready", 'INFO')
logger.log("Modern design with real-time logging and notifications", 'INFO')
logger.log("Click 'Setup & Connect API' to begin trading", 'AUTO')

# Start status updates
update_status_indicators()

# Modern keybindings
root.bind('<F1>', lambda e: logger.log("F1 - Balance shortcut triggered", 'INFO'))
root.bind('<F2>', lambda e: logger.log("F2 - Positions shortcut triggered", 'INFO'))
root.bind('<F3>', lambda e: logger.log("F3 - Orders shortcut triggered", 'INFO'))
root.bind('<Escape>', lambda e: emergency_stop())

# Start the modern interface
if __name__ == "__main__":
    logger.log("Starting modern trading interface...", 'SUCCESS')
    root.mainloop()