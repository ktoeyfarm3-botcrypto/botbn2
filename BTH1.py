import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import hashlib
import hmac
import json
import time
import requests
import threading
from datetime import datetime, timedelta
from collections import deque
import numpy as np
import sqlite3
import os

# Configure theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ImprovedBitkubAPI:
    """Improved Bitkub API Client with proven order execution"""

    def __init__(self, api_key="", api_secret=""):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.bitkub.com"
        self.request_times = deque(maxlen=250)
        self.rate_limit_lock = threading.Lock()

        # Error code mapping
        self.error_codes = {
            0: "Success", 1: "Invalid JSON payload", 2: "Missing X-BTK-APIKEY",
            3: "Invalid API key", 4: "API pending for activation", 5: "IP not allowed",
            6: "Missing / invalid signature", 7: "Missing timestamp", 8: "Invalid timestamp",
            9: "Invalid user / User not found", 10: "Invalid parameter", 11: "Invalid symbol",
            12: "Invalid amount / Amount too low", 13: "Invalid rate", 14: "Improper rate",
            15: "Amount too low", 16: "Failed to get balance", 17: "Wallet is empty",
            18: "Insufficient balance", 19: "Failed to insert order into db",
            20: "Failed to deduct balance", 21: "Invalid order for cancellation",
            22: "Invalid side", 23: "Failed to update order status", 24: "Invalid order for lookup",
            25: "KYC level 1 is required", 30: "Limit exceeds", 55: "Cancel only mode",
            56: "User suspended from purchasing", 57: "User suspended from selling",
            90: "Server error (contact support)"
        }

    def _wait_for_rate_limit(self):
        """Rate limiting management"""
        with self.rate_limit_lock:
            now = time.time()
            while self.request_times and (now - self.request_times[0]) > 10:
                self.request_times.popleft()
            if len(self.request_times) >= 190:  # Conservative limit
                time.sleep(1)
                self.request_times.clear()
            self.request_times.append(now)

    def get_server_time(self):
        """Get server timestamp"""
        try:
            response = requests.get(f"{self.base_url}/api/v3/servertime", timeout=10)
            return response.json()
        except:
            return int(time.time() * 1000)

    def create_signature(self, timestamp, method, path, body=""):
        """Create HMAC SHA256 signature"""
        signature_string = f"{timestamp}{method}{path}{body}"
        return hmac.new(
            self.api_secret.encode('utf-8'),
            signature_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def normalize_symbol_for_trading(self, symbol):
        """Convert symbol to correct format for trading API"""
        symbol = symbol.upper()

        # Convert display format to trading format
        symbol_map = {
            "THB_BTC": "btc_thb", "THB_ETH": "eth_thb", "THB_ADA": "ada_thb",
            "THB_XRP": "xrp_thb", "THB_BNB": "bnb_thb", "THB_DOGE": "doge_thb"
        }

        if symbol in symbol_map:
            return symbol_map[symbol]

        # If already in base_quote format, keep it
        parts = symbol.lower().split('_')
        if len(parts) == 2 and parts[1] == 'thb':
            return symbol.lower()
        elif len(parts) == 2 and parts[0] == 'thb':
            return f"{parts[1]}_thb"
        else:
            return symbol.lower()

    def get_simple_ticker(self, symbol):
        """Get ticker data using proven method"""
        try:
            self._wait_for_rate_limit()
            response = requests.get(f"{self.base_url}/api/market/ticker", timeout=10)
            data = response.json()

            if isinstance(data, dict):
                # Look for symbol in different formats
                symbol_variations = [
                    symbol.upper(), symbol.lower(),
                    f"THB_{symbol.split('_')[0].upper()}",
                    f"{symbol.split('_')[0].upper()}_THB"
                ]

                for variant in symbol_variations:
                    if variant in data:
                        ticker_data = data[variant]
                        return {
                            'symbol': variant,
                            'last_price': float(ticker_data.get('last', 0)),
                            'bid': float(ticker_data.get('highestBid', 0)),
                            'ask': float(ticker_data.get('lowestAsk', 0)),
                            'change_24h': float(ticker_data.get('percentChange', 0))
                        }

                # Try to find BTC related symbols as fallback
                for key in data.keys():
                    if 'BTC' in key.upper():
                        ticker_data = data[key]
                        return {
                            'symbol': key,
                            'last_price': float(ticker_data.get('last', 0)),
                            'bid': float(ticker_data.get('highestBid', 0)),
                            'ask': float(ticker_data.get('lowestAsk', 0)),
                            'change_24h': float(ticker_data.get('percentChange', 0))
                        }

            return None
        except Exception as e:
            print(f"Ticker error: {e}")
            return None

    def check_balance(self):
        """Check wallet balance"""
        try:
            self._wait_for_rate_limit()
            timestamp = self.get_server_time()
            path = "/api/v3/market/wallet"
            signature = self.create_signature(timestamp, "POST", path)

            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-BTK-APIKEY": self.api_key,
                "X-BTK-TIMESTAMP": str(timestamp),
                "X-BTK-SIGN": signature
            }

            response = requests.post(f"{self.base_url}{path}", headers=headers, timeout=10)
            return response.json()
        except Exception as e:
            print(f"Balance check error: {e}")
            return None

    def place_buy_order_safe(self, symbol, amount_thb, buy_price, order_type="limit"):
        """Place buy order using proven method"""
        try:
            # Convert to trading API format
            trading_symbol = self.normalize_symbol_for_trading(symbol)

            self._wait_for_rate_limit()

            order_data = {
                "sym": trading_symbol,
                "amt": amount_thb,
                "rat": buy_price if order_type == "limit" else 0,
                "typ": order_type
            }

            timestamp = self.get_server_time()
            path = "/api/v3/market/place-bid"
            body = json.dumps(order_data, separators=(',', ':'))
            signature = self.create_signature(timestamp, "POST", path, body)

            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-BTK-APIKEY": self.api_key,
                "X-BTK-TIMESTAMP": str(timestamp),
                "X-BTK-SIGN": signature
            }

            response = requests.post(f"{self.base_url}{path}", headers=headers, data=body, timeout=10)
            result = response.json()

            # Log for debugging
            print(f"Buy order - Symbol: {trading_symbol}, Amount: {amount_thb}, Price: {buy_price}")
            print(f"API Response: {result}")

            return result

        except Exception as e:
            return {"error": 999, "message": f"Request failed: {e}"}

    def place_sell_order_safe(self, symbol, amount_crypto, sell_price, order_type="limit"):
        """Place sell order using proven method"""
        try:
            # Convert to trading API format
            trading_symbol = self.normalize_symbol_for_trading(symbol)

            self._wait_for_rate_limit()

            order_data = {
                "sym": trading_symbol,
                "amt": amount_crypto,
                "rat": sell_price if order_type == "limit" else 0,
                "typ": order_type
            }

            timestamp = self.get_server_time()
            path = "/api/v3/market/place-ask"
            body = json.dumps(order_data, separators=(',', ':'))
            signature = self.create_signature(timestamp, "POST", path, body)

            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-BTK-APIKEY": self.api_key,
                "X-BTK-TIMESTAMP": str(timestamp),
                "X-BTK-SIGN": signature
            }

            response = requests.post(f"{self.base_url}{path}", headers=headers, data=body, timeout=10)
            result = response.json()

            print(f"Sell order - Symbol: {trading_symbol}, Amount: {amount_crypto}, Price: {sell_price}")
            print(f"API Response: {result}")

            return result

        except Exception as e:
            return {"error": 999, "message": f"Request failed: {e}"}

    def cancel_order_safe(self, symbol, order_id, side):
        """Cancel order safely"""
        try:
            trading_symbol = self.normalize_symbol_for_trading(symbol)

            self._wait_for_rate_limit()

            order_data = {
                "sym": trading_symbol,
                "id": str(order_id),
                "sd": side
            }

            timestamp = self.get_server_time()
            path = "/api/v3/market/cancel-order"
            body = json.dumps(order_data, separators=(',', ':'))
            signature = self.create_signature(timestamp, "POST", path, body)

            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-BTK-APIKEY": self.api_key,
                "X-BTK-TIMESTAMP": str(timestamp),
                "X-BTK-SIGN": signature
            }

            response = requests.post(f"{self.base_url}{path}", headers=headers, data=body, timeout=10)
            return response.json()

        except Exception as e:
            return {"error": 999, "message": f"Request failed: {e}"}

    def get_my_open_orders_safe(self, symbol):
        """Get open orders safely"""
        try:
            # Use GET method for open orders
            trading_symbol = self.normalize_symbol_for_trading(symbol)

            self._wait_for_rate_limit()

            timestamp = self.get_server_time()
            path = f"/api/v3/market/my-open-orders"
            query_string = f"?sym={trading_symbol.upper()}"

            signature = self.create_signature(timestamp, "GET", path + query_string)

            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-BTK-APIKEY": self.api_key,
                "X-BTK-TIMESTAMP": str(timestamp),
                "X-BTK-SIGN": signature
            }

            response = requests.get(f"{self.base_url}{path}{query_string}", headers=headers, timeout=10)
            return response.json()

        except Exception as e:
            return {"error": 999, "message": f"Request failed: {e}"}

    def check_system_status(self):
        """Check API system status"""
        try:
            response = requests.get(f"{self.base_url}/api/status", timeout=10)
            status_data = response.json()
            for service in status_data:
                if service["status"] != "ok":
                    return False, f"Service '{service['name']}' is not OK"
            return True, "All systems operational"
        except Exception as e:
            return False, f"Could not check system status: {e}"


class SafeTradingStrategy:
    """Improved trading strategy with better risk management"""

    def __init__(self):
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.stop_loss_pct = 0.02  # 2%
        self.take_profit_pct = 0.04  # 4%
        self.position = None
        self.max_position_age_hours = 24  # Close position after 24 hours

    def calculate_rsi(self, prices, period=14):
        """Calculate RSI with improved accuracy"""
        if len(prices) < period + 1:
            return 50

        deltas = np.diff(prices[-period - 1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)

        if avg_loss == 0:
            return 100

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def should_buy(self, price, rsi, balance_thb, min_trade_size):
        """Enhanced buy signal logic"""
        if self.position:
            return False, "Already have position"

        if balance_thb < min_trade_size:
            return False, f"Insufficient balance: {balance_thb:.2f} < {min_trade_size}"

        # Multiple conditions for buy signal
        conditions = []

        if rsi < self.rsi_oversold:
            conditions.append(f"RSI oversold ({rsi:.1f})")

        # Could add more conditions here (moving averages, volume, etc.)

        if conditions:
            return True, " & ".join(conditions)

        return False, f"No buy signal (RSI: {rsi:.1f})"

    def should_sell(self, current_price, rsi):
        """Enhanced sell signal logic"""
        if not self.position:
            return False, "No position"

        entry_price = self.position['entry_price']
        entry_time = self.position.get('entry_time', datetime.now())

        # Time-based exit
        hours_held = (datetime.now() - entry_time).total_seconds() / 3600
        if hours_held > self.max_position_age_hours:
            return True, f"Max holding time exceeded ({hours_held:.1f}h)"

        # Price-based exits
        price_change_pct = (current_price - entry_price) / entry_price

        # Stop loss
        if price_change_pct <= -self.stop_loss_pct:
            return True, f"Stop Loss triggered ({price_change_pct * 100:.1f}%)"

        # Take profit
        if price_change_pct >= self.take_profit_pct:
            return True, f"Take Profit triggered ({price_change_pct * 100:.1f}%)"

        # RSI overbought
        if rsi > self.rsi_overbought:
            return True, f"RSI overbought ({rsi:.1f})"

        return False, f"Hold (P&L: {price_change_pct * 100:.1f}%, RSI: {rsi:.1f})"


class ImprovedTradingBot:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("🚀 Improved Bitkub Trading Bot - REAL MONEY")
        self.root.geometry("1400x900")

        # Core components
        self.api_client = None
        self.strategy = SafeTradingStrategy()
        self.price_history = deque(maxlen=100)

        # Trading state
        self.is_trading = False
        self.is_paper_trading = True
        self.emergency_stop = False

        # Trading config with safer defaults
        self.config = {
            'symbol': 'btc_thb',
            'trade_amount_thb': 100,  # Start smaller for safety
            'max_daily_trades': 3,  # Reduced for safety
            'max_daily_loss': 500,  # Reduced for safety
            'min_trade_interval': 600,  # Increased interval
        }

        # Statistics
        self.daily_trades = 0
        self.daily_pnl = 0
        self.last_trade_time = None

        # Database
        self.init_database()

        # Setup UI
        self.setup_ui()

    def init_database(self):
        """Initialize database for trade history"""
        self.db_path = "improved_trading_bot.db"
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                symbol TEXT,
                side TEXT,
                amount REAL,
                price REAL,
                total_thb REAL,
                order_id TEXT,
                status TEXT,
                pnl REAL,
                reason TEXT,
                is_paper BOOLEAN,
                api_response TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def setup_ui(self):
        """Create improved UI with better safety features"""

        # Enhanced warning banner
        warning_frame = ctk.CTkFrame(self.root, fg_color="red", height=60)
        warning_frame.pack(fill="x", padx=10, pady=5)
        warning_frame.pack_propagate(False)

        warning_text = "⚠️ REAL MONEY TRADING BOT - IMPROVED ORDER EXECUTION ⚠️\nAlways test with paper trading first!"
        ctk.CTkLabel(warning_frame, text=warning_text,
                     font=("Arial", 14, "bold"),
                     text_color="white").pack(expand=True)

        # Tabs
        self.tabview = ctk.CTkTabview(self.root)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_dashboard = self.tabview.add("📊 Dashboard")
        self.tab_trading = self.tabview.add("💹 Trading")
        self.tab_api = self.tabview.add("🔌 API Config")
        self.tab_testing = self.tabview.add("🧪 Testing")
        self.tab_history = self.tabview.add("📜 History")
        self.tab_settings = self.tabview.add("⚙️ Settings")

        self.setup_dashboard_tab()
        self.setup_trading_tab()
        self.setup_api_tab()
        self.setup_testing_tab()
        self.setup_history_tab()
        self.setup_settings_tab()

    def setup_dashboard_tab(self):
        """Enhanced dashboard"""
        # Status cards
        stats_frame = ctk.CTkFrame(self.tab_dashboard)
        stats_frame.pack(fill="x", padx=10, pady=10)

        self.status_cards = {}
        cards = [
            ("Mode", "PAPER TRADING", "orange"),
            ("System Status", "Checking...", "blue"),
            ("Balance THB", "---", "green"),
            ("Daily P&L", "0.00", "blue"),
            ("Daily Trades", "0/3", "purple"),
            ("Position", "None", "gray")
        ]

        for i, (label, value, color) in enumerate(cards):
            card = ctk.CTkFrame(stats_frame)
            card.grid(row=0, column=i, padx=5, pady=5, sticky="ew")

            ctk.CTkLabel(card, text=label, font=("Arial", 10)).pack(pady=2)
            self.status_cards[label] = ctk.CTkLabel(card, text=value,
                                                    font=("Arial", 12, "bold"))
            self.status_cards[label].pack(pady=5)

            stats_frame.grid_columnconfigure(i, weight=1)

        # Control panel with improved safety
        control_frame = ctk.CTkFrame(self.tab_dashboard)
        control_frame.pack(fill="x", padx=10, pady=10)

        # Paper/Real toggle with extra safety
        safety_frame = ctk.CTkFrame(control_frame)
        safety_frame.pack(side="left", padx=10)

        ctk.CTkLabel(safety_frame, text="Trading Mode:",
                     font=("Arial", 12, "bold")).pack(pady=2)

        self.paper_switch = ctk.CTkSwitch(safety_frame,
                                          text="REAL Trading (Dangerous!)",
                                          command=self.toggle_paper_trading,
                                          button_color="red",
                                          progress_color="darkred")
        self.paper_switch.pack(pady=2)

        # Emergency controls
        emergency_frame = ctk.CTkFrame(control_frame)
        emergency_frame.pack(side="right", padx=10)

        ctk.CTkButton(emergency_frame, text="🚨 EMERGENCY STOP",
                      command=self.emergency_stop_trading,
                      fg_color="red", height=50, width=150,
                      font=("Arial", 12, "bold")).pack(pady=2)

        ctk.CTkButton(emergency_frame, text="🔄 System Check",
                      command=self.system_health_check,
                      height=30, width=150).pack(pady=2)

        # Enhanced display
        self.dashboard_display = ctk.CTkTextbox(self.tab_dashboard, font=("Consolas", 11))
        self.dashboard_display.pack(fill="both", expand=True, padx=10, pady=10)

    def setup_testing_tab(self):
        """New testing tab for safe order testing"""
        test_frame = ctk.CTkFrame(self.tab_testing)
        test_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(test_frame, text="🧪 Order Testing (Safe Testing Environment)",
                     font=("Arial", 16, "bold")).pack(pady=10)

        # Test controls
        test_controls = ctk.CTkFrame(test_frame)
        test_controls.pack(fill="x", padx=10, pady=10)

        # Test amount
        amount_frame = ctk.CTkFrame(test_controls)
        amount_frame.pack(side="left", padx=5)

        ctk.CTkLabel(amount_frame, text="Test Amount (THB):").pack()
        self.test_amount_var = tk.IntVar(value=50)  # Small amount for testing
        ctk.CTkEntry(amount_frame, textvariable=self.test_amount_var, width=80).pack()

        # Test buttons
        btn_frame = ctk.CTkFrame(test_controls)
        btn_frame.pack(side="left", padx=20)

        ctk.CTkButton(btn_frame, text="📊 Check Market Data",
                      command=self.test_market_data).pack(side="left", padx=5)

        ctk.CTkButton(btn_frame, text="💰 Check Balance",
                      command=self.test_balance).pack(side="left", padx=5)

        ctk.CTkButton(btn_frame, text="🧪 Test Buy Order",
                      command=self.test_buy_order,
                      fg_color="orange").pack(side="left", padx=5)

        # Test results
        self.test_display = ctk.CTkTextbox(self.tab_testing, font=("Consolas", 10))
        self.test_display.pack(fill="both", expand=True, padx=10, pady=10)

    def setup_trading_tab(self):
        """Enhanced trading tab"""
        # Trading controls
        control_frame = ctk.CTkFrame(self.tab_trading)
        control_frame.pack(fill="x", padx=10, pady=10)

        self.start_btn = ctk.CTkButton(control_frame, text="▶️ Start Trading Bot",
                                       command=self.toggle_trading,
                                       fg_color="green", height=40, width=200)
        self.start_btn.pack(side="left", padx=10)

        ctk.CTkButton(control_frame, text="📊 Check Signals",
                      command=self.check_signals,
                      height=40).pack(side="left", padx=5)

        ctk.CTkButton(control_frame, text="📋 Open Orders",
                      command=self.check_open_orders,
                      height=40).pack(side="left", padx=5)

        # Strategy settings (same as before but with better organization)
        strategy_frame = ctk.CTkFrame(self.tab_trading)
        strategy_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(strategy_frame, text="Strategy Settings:",
                     font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=5)

        # RSI settings
        rsi_frame = ctk.CTkFrame(strategy_frame)
        rsi_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(rsi_frame, text="RSI Oversold:").pack(side="left", padx=5)
        self.rsi_oversold_var = tk.IntVar(value=30)
        ctk.CTkSlider(rsi_frame, from_=10, to=40, variable=self.rsi_oversold_var,
                      command=self.update_strategy).pack(side="left", padx=5)
        self.rsi_oversold_label = ctk.CTkLabel(rsi_frame, text="30")
        self.rsi_oversold_label.pack(side="left", padx=5)

        ctk.CTkLabel(rsi_frame, text="RSI Overbought:").pack(side="left", padx=20)
        self.rsi_overbought_var = tk.IntVar(value=70)
        ctk.CTkSlider(rsi_frame, from_=60, to=90, variable=self.rsi_overbought_var,
                      command=self.update_strategy).pack(side="left", padx=5)
        self.rsi_overbought_label = ctk.CTkLabel(rsi_frame, text="70")
        self.rsi_overbought_label.pack(side="left", padx=5)

        # Risk settings
        risk_frame = ctk.CTkFrame(strategy_frame)
        risk_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(risk_frame, text="Stop Loss %:").pack(side="left", padx=5)
        self.stop_loss_var = tk.DoubleVar(value=2.0)
        ctk.CTkSlider(risk_frame, from_=0.5, to=5.0, variable=self.stop_loss_var,
                      command=self.update_strategy).pack(side="left", padx=5)
        self.stop_loss_label = ctk.CTkLabel(risk_frame, text="2.0%")
        self.stop_loss_label.pack(side="left", padx=5)

        ctk.CTkLabel(risk_frame, text="Take Profit %:").pack(side="left", padx=20)
        self.take_profit_var = tk.DoubleVar(value=4.0)
        ctk.CTkSlider(risk_frame, from_=1.0, to=10.0, variable=self.take_profit_var,
                      command=self.update_strategy).pack(side="left", padx=5)
        self.take_profit_label = ctk.CTkLabel(risk_frame, text="4.0%")
        self.take_profit_label.pack(side="left", padx=5)

        # Trading log
        self.trading_log = ctk.CTkTextbox(self.tab_trading, font=("Consolas", 10))
        self.trading_log.pack(fill="both", expand=True, padx=10, pady=10)

    def setup_api_tab(self):
        """API configuration with enhanced security notes"""
        api_frame = ctk.CTkFrame(self.tab_api)
        api_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(api_frame, text="Bitkub API Configuration",
                     font=("Arial", 18, "bold")).pack(pady=10)

        # Enhanced security warning
        warning_text = """
🔒 ENHANCED SECURITY NOTES:
• This bot now uses proven order execution methods
• Start with PAPER TRADING and small amounts
• API credentials are handled securely
• Set IP whitelist in Bitkub for maximum security
• Use a dedicated trading account with limited funds
• Monitor trades closely during first runs
        """
        ctk.CTkLabel(api_frame, text=warning_text,
                     font=("Arial", 10), justify="left",
                     text_color="yellow").pack(pady=10)

        # API inputs (same as before)
        ctk.CTkLabel(api_frame, text="API Key:").pack(anchor="w", padx=20, pady=5)
        self.api_key_entry = ctk.CTkEntry(api_frame, show="*", width=400)
        self.api_key_entry.pack(padx=20, pady=5)

        ctk.CTkLabel(api_frame, text="API Secret:").pack(anchor="w", padx=20, pady=5)
        self.api_secret_entry = ctk.CTkEntry(api_frame, show="*", width=400)
        self.api_secret_entry.pack(padx=20, pady=5)

        # Enhanced buttons
        btn_frame = ctk.CTkFrame(api_frame)
        btn_frame.pack(pady=20)

        ctk.CTkButton(btn_frame, text="🔐 Save & Connect",
                      command=self.connect_api,
                      fg_color="green", height=40).pack(side="left", padx=5)

        ctk.CTkButton(btn_frame, text="🔌 Test Connection",
                      command=self.test_connection,
                      height=40).pack(side="left", padx=5)

        ctk.CTkButton(btn_frame, text="🏥 Health Check",
                      command=self.api_health_check,
                      height=40).pack(side="left", padx=5)

        # Status display
        self.api_status_display = ctk.CTkTextbox(self.tab_api, font=("Consolas", 11))
        self.api_status_display.pack(fill="both", expand=True, padx=10, pady=10)

    def setup_history_tab(self):
        """Enhanced history tab"""
        control_frame = ctk.CTkFrame(self.tab_history)
        control_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(control_frame, text="🔄 Refresh",
                      command=self.load_trade_history).pack(side="left", padx=5)

        ctk.CTkButton(control_frame, text="📊 Statistics",
                      command=self.show_statistics).pack(side="left", padx=5)

        ctk.CTkButton(control_frame, text="📤 Export CSV",
                      command=self.export_history).pack(side="left", padx=5)

        # History display
        self.history_display = ctk.CTkTextbox(self.tab_history, font=("Consolas", 10))
        self.history_display.pack(fill="both", expand=True, padx=10, pady=10)

    def setup_settings_tab(self):
        """Enhanced settings tab with safer defaults"""
        settings_frame = ctk.CTkFrame(self.tab_settings)
        settings_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(settings_frame, text="Trading Configuration",
                     font=("Arial", 16, "bold")).pack(pady=10)

        # Symbol selection
        symbol_frame = ctk.CTkFrame(settings_frame)
        symbol_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(symbol_frame, text="Trading Pair:").pack(side="left", padx=5)
        self.symbol_var = tk.StringVar(value="btc_thb")
        symbol_menu = ctk.CTkOptionMenu(symbol_frame, variable=self.symbol_var,
                                        values=["btc_thb", "eth_thb", "bnb_thb",
                                                "ada_thb", "doge_thb"])
        symbol_menu.pack(side="left", padx=5)

        # Trade amount with safer defaults
        amount_frame = ctk.CTkFrame(settings_frame)
        amount_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(amount_frame, text="Trade Amount (THB):").pack(side="left", padx=5)
        self.trade_amount_var = tk.IntVar(value=100)  # Reduced default
        amount_entry = ctk.CTkEntry(amount_frame, textvariable=self.trade_amount_var, width=100)
        amount_entry.pack(side="left", padx=5)

        ctk.CTkLabel(amount_frame, text="(Start small for testing)",
                     text_color="yellow").pack(side="left", padx=5)

        # Risk limits with safer defaults
        risk_frame = ctk.CTkFrame(settings_frame)
        risk_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(risk_frame, text="Max Daily Trades:").pack(side="left", padx=5)
        self.max_trades_var = tk.IntVar(value=3)  # Reduced
        ctk.CTkEntry(risk_frame, textvariable=self.max_trades_var, width=50).pack(side="left", padx=5)

        ctk.CTkLabel(risk_frame, text="Max Daily Loss (THB):").pack(side="left", padx=20)
        self.max_loss_var = tk.IntVar(value=500)  # Reduced
        ctk.CTkEntry(risk_frame, textvariable=self.max_loss_var, width=100).pack(side="left", padx=5)

        # Save button
        ctk.CTkButton(settings_frame, text="💾 Save Settings",
                      command=self.save_settings,
                      fg_color="green", height=40).pack(pady=20)

    # === Enhanced Core Functions ===

    def connect_api(self):
        """Enhanced API connection with better validation"""
        api_key = self.api_key_entry.get().strip()
        api_secret = self.api_secret_entry.get().strip()

        if not api_key or not api_secret:
            messagebox.showwarning("Error", "Please enter API credentials")
            return

        # Create improved API client
        self.api_client = ImprovedBitkubAPI(api_key, api_secret)

        # Test connection with system status check
        self.log("🔌 Connecting to API...")

        # Check system status first
        status_ok, status_msg = self.api_client.check_system_status()
        if not status_ok:
            self.log(f"❌ System status issue: {status_msg}")
            messagebox.showwarning("System Status", f"API Status Issue: {status_msg}")
            return

        # Test balance check
        balance = self.api_client.check_balance()
        if balance and balance.get('error') == 0:
            self.log("✅ API Connected successfully")
            self.update_balance()
            messagebox.showinfo("Success", "API Connected and validated!")

            # Update system status
            self.status_cards["System Status"].configure(text="Connected", text_color="green")
        else:
            error_msg = "Unknown error"
            if balance:
                error_code = balance.get("error", 999)
                error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")

            self.log(f"❌ API Connection failed: {error_msg}")
            messagebox.showerror("Error", f"Failed to connect: {error_msg}")
            self.status_cards["System Status"].configure(text="Failed", text_color="red")

    def system_health_check(self):
        """Comprehensive system health check"""
        self.log("🏥 Running system health check...")

        if not self.api_client:
            self.log("❌ No API client configured")
            return

        # 1. System status
        status_ok, status_msg = self.api_client.check_system_status()
        self.log(f"System Status: {'✅' if status_ok else '❌'} {status_msg}")

        # 2. Balance check
        balance = self.api_client.check_balance()
        if balance and balance.get('error') == 0:
            thb_balance = balance['result'].get('THB', 0)
            self.log(f"Balance Check: ✅ THB {thb_balance:,.2f}")
        else:
            self.log("Balance Check: ❌ Failed")

        # 3. Market data check
        ticker = self.api_client.get_simple_ticker(self.config['symbol'])
        if ticker:
            self.log(f"Market Data: ✅ {ticker['symbol']} @ {ticker['last_price']:,.0f}")
        else:
            self.log("Market Data: ❌ Failed")

        # 4. Configuration check
        if self.config['trade_amount_thb'] > 1000:
            self.log("⚠️ Warning: Trade amount > 1000 THB")
        if self.config['max_daily_trades'] > 10:
            self.log("⚠️ Warning: High daily trade limit")

        self.log("🏥 Health check completed")

    def test_market_data(self):
        """Test market data retrieval"""
        if not self.api_client:
            self.test_log("❌ Please connect API first")
            return

        self.test_log("📊 Testing market data...")

        ticker = self.api_client.get_simple_ticker(self.config['symbol'])
        if ticker:
            self.test_log(f"✅ Market data retrieved:")
            self.test_log(f"   Symbol: {ticker['symbol']}")
            self.test_log(f"   Last Price: {ticker['last_price']:,.0f} THB")
            self.test_log(f"   Bid: {ticker['bid']:,.0f} THB")
            self.test_log(f"   Ask: {ticker['ask']:,.0f} THB")
            self.test_log(f"   24h Change: {ticker['change_24h']:,.2f}%")
        else:
            self.test_log("❌ Failed to get market data")

    def test_balance(self):
        """Test balance check"""
        if not self.api_client:
            self.test_log("❌ Please connect API first")
            return

        self.test_log("💰 Testing balance check...")

        balance = self.api_client.check_balance()
        if balance and balance.get('error') == 0:
            self.test_log("✅ Balance retrieved:")
            for currency, amount in balance['result'].items():
                if float(amount) > 0:
                    self.test_log(f"   {currency}: {float(amount):,.8f}")
        else:
            error_msg = "Unknown error"
            if balance:
                error_code = balance.get("error", 999)
                error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")
            self.test_log(f"❌ Balance check failed: {error_msg}")

    def test_buy_order(self):
        """Test buy order with small amount"""
        if not self.api_client:
            self.test_log("❌ Please connect API first")
            return

        # Double confirmation for test order
        test_amount = self.test_amount_var.get()

        if not messagebox.askyesno("Confirm Test Order",
                                   f"Place a REAL test buy order for {test_amount} THB?\n\n" +
                                   "This will use real money!"):
            return

        self.test_log(f"🧪 Testing buy order for {test_amount} THB...")

        # Get current market price
        ticker = self.api_client.get_simple_ticker(self.config['symbol'])
        if not ticker:
            self.test_log("❌ Cannot get current price")
            return

        current_price = ticker['last_price']
        buy_price = current_price * 1.01  # 1% above market for quick execution

        self.test_log(f"   Current price: {current_price:,.0f} THB")
        self.test_log(f"   Order price: {buy_price:,.0f} THB")

        # Check balance first
        balance = self.api_client.check_balance()
        if not balance or balance.get('error') != 0:
            self.test_log("❌ Cannot check balance")
            return

        thb_balance = float(balance['result'].get('THB', 0))
        if thb_balance < test_amount:
            self.test_log(f"❌ Insufficient balance: {thb_balance:.2f} < {test_amount}")
            return

        # Place test order
        result = self.api_client.place_buy_order_safe(
            self.config['symbol'], test_amount, buy_price, "limit"
        )

        if result.get("error") == 0:
            order_info = result["result"]
            self.test_log("✅ Test buy order placed successfully!")
            self.test_log(f"   Order ID: {order_info['id']}")
            self.test_log(f"   Amount: {order_info['amt']} THB")
            self.test_log(f"   Rate: {order_info['rat']} THB")
            self.test_log(f"   Fee: {order_info['fee']} THB")
            self.test_log(f"   Expected: {order_info['rec']:.8f} crypto")

            # Ask if user wants to cancel the order
            if messagebox.askyesno("Cancel Test Order?",
                                   f"Test order placed successfully!\n\n" +
                                   f"Order ID: {order_info['id']}\n" +
                                   f"Do you want to cancel it now?"):
                self.cancel_test_order(order_info['id'])
        else:
            error_code = result.get("error", 999)
            error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")
            self.test_log(f"❌ Test buy order failed: {error_msg}")

    def cancel_test_order(self, order_id):
        """Cancel test order"""
        self.test_log(f"🗑️ Cancelling test order {order_id}...")

        result = self.api_client.cancel_order_safe(self.config['symbol'], order_id, "buy")

        if result.get("error") == 0:
            self.test_log("✅ Test order cancelled successfully")
        else:
            error_code = result.get("error", 999)
            error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")
            self.test_log(f"❌ Cancel failed: {error_msg}")

    def check_open_orders(self):
        """Check open orders"""
        if not self.api_client:
            self.log("❌ Please connect API first")
            return

        self.log("📋 Checking open orders...")

        orders = self.api_client.get_my_open_orders_safe(self.config['symbol'])

        if orders and orders.get("error") == 0:
            order_list = orders.get("result", [])
            if order_list:
                self.log(f"📋 Found {len(order_list)} open orders:")
                for order in order_list:
                    self.log(f"   {order.get('side', 'unknown').upper()} "
                             f"Order ID: {order.get('id', 'N/A')} "
                             f"@ {order.get('rate', 'N/A')} THB")
            else:
                self.log("📋 No open orders")
        else:
            error_code = orders.get("error", 999) if orders else 999
            error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")
            self.log(f"❌ Failed to get open orders: {error_msg}")

    def execute_buy_enhanced(self, price, reason):
        """Enhanced buy execution with better error handling"""
        try:
            amount_thb = self.config['trade_amount_thb']

            # Set buy price slightly above market for better execution
            buy_price = price * 1.005  # 0.5% above market

            if self.is_paper_trading:
                # Paper trading
                self.strategy.position = {
                    'entry_price': price,
                    'amount': amount_thb / price,
                    'entry_time': datetime.now()
                }
                self.log(f"📝 PAPER BUY: {amount_thb} THB @ {price:.2f} - {reason}")
                self.save_trade_enhanced('buy', amount_thb / price, price, amount_thb,
                                         'PAPER', 0, reason, True, None)
            else:
                # Real trading with enhanced execution
                self.log(f"💰 Executing REAL BUY: {amount_thb} THB @ {buy_price:.2f}")

                result = self.api_client.place_buy_order_safe(
                    self.config['symbol'], amount_thb, buy_price, 'limit'
                )

                if result and result.get('error') == 0:
                    order_info = result['result']
                    order_id = order_info.get('id', 'unknown')
                    actual_amount = order_info.get('rec', amount_thb / price)

                    self.strategy.position = {
                        'entry_price': buy_price,
                        'amount': actual_amount,
                        'entry_time': datetime.now(),
                        'order_id': order_id
                    }

                    self.log(f"✅ REAL BUY SUCCESS: {amount_thb} THB @ {buy_price:.2f}")
                    self.log(f"   Order ID: {order_id}")
                    self.log(f"   Expected: {actual_amount:.8f} crypto")

                    self.save_trade_enhanced('buy', actual_amount, buy_price, amount_thb,
                                             order_id, 0, reason, False, result)
                else:
                    error_code = result.get("error", 999) if result else 999
                    error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")
                    self.log(f"❌ Buy order failed: {error_msg}")
                    return

            self.daily_trades += 1
            self.last_trade_time = datetime.now()
            self.status_cards["Position"].configure(text=f"LONG @ {price:.2f}")
            self.status_cards["Daily Trades"].configure(
                text=f"{self.daily_trades}/{self.config['max_daily_trades']}"
            )

        except Exception as e:
            self.log(f"❌ Buy execution error: {e}")

    def save_trade_enhanced(self, side, amount, price, total_thb, order_id, pnl, reason, is_paper, api_response):
        """Enhanced trade saving with API response"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            api_response_str = json.dumps(api_response) if api_response else None

            cursor.execute('''
                INSERT INTO trades 
                (timestamp, symbol, side, amount, price, total_thb, 
                 order_id, status, pnl, reason, is_paper, api_response)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (datetime.now(), self.config['symbol'], side, amount, price,
                  total_thb, order_id, 'completed', pnl, reason, is_paper, api_response_str))

            conn.commit()
            conn.close()

        except Exception as e:
            self.log(f"Database error: {e}")

    def export_history(self):
        """Export trade history to CSV"""
        try:
            import csv
            from tkinter import filedialog

            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                title="Export Trade History"
            )

            if filename:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT timestamp, symbol, side, amount, price, total_thb, 
                           order_id, pnl, reason, is_paper
                    FROM trades ORDER BY timestamp DESC
                ''')

                trades = cursor.fetchall()
                conn.close()

                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Timestamp', 'Symbol', 'Side', 'Amount', 'Price',
                                     'Total THB', 'Order ID', 'P&L', 'Reason', 'Paper Trading'])
                    writer.writerows(trades)

                messagebox.showinfo("Export Complete", f"Trade history exported to {filename}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {e}")

    def api_health_check(self):
        """Detailed API health check"""
        if not self.api_client:
            self.api_status_display.delete("1.0", "end")
            self.api_status_display.insert("1.0", "❌ No API client configured")
            return

        self.api_status_display.delete("1.0", "end")
        self.api_status_display.insert("1.0", "🏥 Running API Health Check...\n\n")

        # System status
        status_ok, status_msg = self.api_client.check_system_status()
        self.api_status_display.insert("end", f"System Status: {'✅' if status_ok else '❌'} {status_msg}\n")

        # Balance check
        balance = self.api_client.check_balance()
        if balance and balance.get('error') == 0:
            self.api_status_display.insert("end", "Balance Check: ✅ Success\n")
            for currency, amount in balance['result'].items():
                if float(amount) > 0:
                    self.api_status_display.insert("end", f"  {currency}: {float(amount):,.8f}\n")
        else:
            self.api_status_display.insert("end", "Balance Check: ❌ Failed\n")

        # Market data check
        ticker = self.api_client.get_simple_ticker(self.config['symbol'])
        if ticker:
            self.api_status_display.insert("end", f"Market Data: ✅ {ticker['symbol']} @ {ticker['last_price']:,.0f}\n")
        else:
            self.api_status_display.insert("end", "Market Data: ❌ Failed\n")

        self.api_status_display.insert("end", f"\nHealth Check Completed: {datetime.now().strftime('%H:%M:%S')}")

    def test_log(self, message):
        """Add message to test log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.test_display.insert("end", log_entry)
        self.test_display.see("end")

    def toggle_paper_trading(self):
        """Enhanced paper trading toggle with multiple confirmations"""
        if self.paper_switch.get():
            # Multiple confirmations for real trading
            if not messagebox.askyesno("⚠️ WARNING - Real Trading",
                                       "Enable REAL MONEY trading?\n\n" +
                                       "This bot will trade with actual funds!\n" +
                                       "Have you tested thoroughly with paper trading?"):
                self.paper_switch.deselect()
                return

            if not messagebox.askyesno("⚠️ FINAL CONFIRMATION",
                                       "This is your FINAL warning!\n\n" +
                                       "Real money will be at risk.\n" +
                                       "Are you using a small test amount?\n" +
                                       "Do you accept full responsibility?"):
                self.paper_switch.deselect()
                return

            # Additional safety check
            if self.config['trade_amount_thb'] > 500:
                if not messagebox.askyesno("⚠️ High Amount Warning",
                                           f"Trade amount is {self.config['trade_amount_thb']} THB.\n\n" +
                                           "Recommended to start with smaller amounts.\n" +
                                           "Continue anyway?"):
                    self.paper_switch.deselect()
                    return

            self.is_paper_trading = False
            self.status_cards["Mode"].configure(text="REAL TRADING", text_color="red")
            self.log("⚠️ REAL TRADING ENABLED - USE CAUTION!")

        else:
            self.is_paper_trading = True
            self.status_cards["Mode"].configure(text="PAPER TRADING", text_color="orange")
            self.log("📝 Switched to Paper Trading")

    # === Rest of the functions remain the same as the original ===
    # (toggle_trading, trading_loop, execute_sell, emergency_stop_trading, etc.)
    # I'll include the key ones with improvements:

    def toggle_trading(self):
        """Enhanced trading toggle with better validation"""
        if not self.is_trading:
            if not self.api_client:
                messagebox.showwarning("Error", "Please connect API first")
                return

            # Pre-flight checks
            if not self.pre_flight_check():
                return

            if not self.is_paper_trading:
                if not messagebox.askyesno("Start Real Trading",
                                           f"Start trading with REAL money?\n\n" +
                                           f"Amount per trade: {self.config['trade_amount_thb']} THB\n" +
                                           f"Max daily trades: {self.config['max_daily_trades']}\n" +
                                           f"Symbol: {self.config['symbol'].upper()}"):
                    return

            self.is_trading = True
            self.emergency_stop = False
            self.start_btn.configure(text="⏹️ Stop Trading Bot", fg_color="red")
            self.log(f"🚀 Started {'PAPER' if self.is_paper_trading else 'REAL'} trading")

            # Start trading thread
            threading.Thread(target=self.trading_loop_enhanced, daemon=True).start()
        else:
            self.is_trading = False
            self.start_btn.configure(text="▶️ Start Trading Bot", fg_color="green")
            self.log("🛑 Stopped trading")

    def pre_flight_check(self):
        """Pre-flight safety check before trading"""
        self.log("🛫 Running pre-flight check...")

        # System status
        status_ok, status_msg = self.api_client.check_system_status()
        if not status_ok:
            self.log(f"❌ System not ready: {status_msg}")
            return False

        # Balance check
        balance = self.api_client.check_balance()
        if not balance or balance.get('error') != 0:
            self.log("❌ Cannot verify balance")
            return False

        thb_balance = float(balance['result'].get('THB', 0))
        if thb_balance < self.config['trade_amount_thb']:
            self.log(f"❌ Insufficient balance: {thb_balance:.2f} < {self.config['trade_amount_thb']}")
            return False

        # Market data check
        ticker = self.api_client.get_simple_ticker(self.config['symbol'])
        if not ticker:
            self.log("❌ Cannot get market data")
            return False

        self.log("✅ Pre-flight check passed")
        return True

    def trading_loop_enhanced(self):
        """Enhanced trading loop with better error handling"""
        consecutive_errors = 0
        max_consecutive_errors = 5

        while self.is_trading and not self.emergency_stop:
            try:
                # Check daily limits
                if self.daily_trades >= self.config['max_daily_trades']:
                    self.log(f"📊 Daily trade limit reached ({self.daily_trades}/{self.config['max_daily_trades']})")
                    time.sleep(3600)  # Wait 1 hour
                    continue

                if self.daily_pnl <= -self.config['max_daily_loss']:
                    self.log(f"💸 Daily loss limit reached ({self.daily_pnl:.2f}/{-self.config['max_daily_loss']})")
                    self.emergency_stop_trading()
                    break

                # Check minimum trade interval
                if self.last_trade_time:
                    time_since_trade = (datetime.now() - self.last_trade_time).seconds
                    if time_since_trade < self.config['min_trade_interval']:
                        time.sleep(30)
                        continue

                # Get market data
                ticker = self.api_client.get_simple_ticker(self.config['symbol'])
                if not ticker:
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        self.log("❌ Too many consecutive errors, stopping")
                        break
                    time.sleep(60)
                    continue

                current_price = ticker['last_price']
                self.price_history.append(current_price)

                # Reset error counter on success
                consecutive_errors = 0

                # Calculate indicators
                if len(self.price_history) >= 15:
                    rsi = self.strategy.calculate_rsi(list(self.price_history))

                    # Check for buy signal
                    balance = self.api_client.check_balance()
                    if balance and balance.get('error') == 0:
                        thb_balance = float(balance['result'].get('THB', 0))

                        should_buy, reason = self.strategy.should_buy(
                            current_price, rsi, thb_balance,
                            self.config['trade_amount_thb']
                        )

                        if should_buy:
                            self.execute_buy_enhanced(current_price, reason)

                    # Check for sell signal
                    if self.strategy.position:
                        should_sell, reason = self.strategy.should_sell(current_price, rsi)
                        if should_sell:
                            self.execute_sell_enhanced(current_price, reason)

                # Update display
                self.update_dashboard_enhanced()

                # Wait before next check
                time.sleep(30)

            except Exception as e:
                consecutive_errors += 1
                self.log(f"❌ Trading loop error: {e}")
                if consecutive_errors >= max_consecutive_errors:
                    self.log("❌ Too many errors, stopping trading")
                    break
                time.sleep(60)

        self.log("🛑 Trading loop ended")

    def execute_sell_enhanced(self, price, reason):
        """Enhanced sell execution"""
        try:
            if not self.strategy.position:
                return

            amount = self.strategy.position['amount']
            entry_price = self.strategy.position['entry_price']
            pnl = (price - entry_price) * amount

            # Set sell price slightly below market for better execution
            sell_price = price * 0.995  # 0.5% below market

            if self.is_paper_trading:
                # Paper trading
                self.log(f"📝 PAPER SELL: {amount:.8f} @ {price:.2f} - P&L: {pnl:.2f} THB - {reason}")
                self.save_trade_enhanced('sell', amount, price, amount * price,
                                         'PAPER', pnl, reason, True, None)
            else:
                # Real trading
                self.log(f"💰 Executing REAL SELL: {amount:.8f} @ {sell_price:.2f}")

                result = self.api_client.place_sell_order_safe(
                    self.config['symbol'], amount, sell_price, 'limit'
                )

                if result and result.get('error') == 0:
                    order_info = result['result']
                    order_id = order_info.get('id', 'unknown')

                    self.log(f"✅ REAL SELL SUCCESS: {amount:.8f} @ {sell_price:.2f}")
                    self.log(f"   Order ID: {order_id}")
                    self.log(f"   P&L: {pnl:.2f} THB")

                    self.save_trade_enhanced('sell', amount, sell_price, amount * sell_price,
                                             order_id, pnl, reason, False, result)
                else:
                    error_code = result.get("error", 999) if result else 999
                    error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")
                    self.log(f"❌ Sell order failed: {error_msg}")
                    return

            self.daily_pnl += pnl
            self.strategy.position = None
            self.status_cards["Position"].configure(text="None")
            self.status_cards["Daily P&L"].configure(text=f"{self.daily_pnl:.2f}")

        except Exception as e:
            self.log(f"❌ Sell execution error: {e}")

    def emergency_stop_trading(self):
        """Enhanced emergency stop with order cancellation"""
        self.emergency_stop = True
        self.is_trading = False
        self.start_btn.configure(text="▶️ Start Trading Bot", fg_color="green")

        self.log("🚨 EMERGENCY STOP ACTIVATED!")

        # Cancel all open orders if real trading
        if not self.is_paper_trading and self.api_client:
            try:
                self.log("🗑️ Cancelling all open orders...")
                orders = self.api_client.get_my_open_orders_safe(self.config['symbol'])
                if orders and orders.get('error') == 0:
                    order_list = orders.get('result', [])
                    for order in order_list:
                        result = self.api_client.cancel_order_safe(
                            self.config['symbol'],
                            order['id'],
                            order['side']
                        )
                        if result.get('error') == 0:
                            self.log(f"✅ Cancelled order {order['id']}")
                        else:
                            self.log(f"❌ Failed to cancel order {order['id']}")
                else:
                    self.log("No open orders to cancel")
            except Exception as e:
                self.log(f"❌ Error during emergency stop: {e}")

        messagebox.showwarning("Emergency Stop", "All trading has been stopped and orders cancelled!")

    def update_balance(self):
        """Enhanced balance update"""
        if not self.api_client:
            return

        balance = self.api_client.check_balance()
        if balance and balance.get('error') == 0:
            thb_balance = float(balance['result'].get('THB', 0))
            self.status_cards["Balance THB"].configure(text=f"{thb_balance:,.2f}")

            # Get crypto balance
            symbol_base = self.config['symbol'].split('_')[0].upper()
            crypto_balance = float(balance['result'].get(symbol_base, 0))

            display_text = f"💰 ACCOUNT BALANCE\n"
            display_text += f"{'=' * 30}\n"
            display_text += f"THB: {thb_balance:,.2f}\n"
            display_text += f"{symbol_base}: {crypto_balance:.8f}\n\n"

            # Add trading info if position exists
            if self.strategy.position:
                entry_price = self.strategy.position['entry_price']
                amount = self.strategy.position['amount']
                entry_time = self.strategy.position['entry_time']

                # Get current price for P&L calculation
                ticker = self.api_client.get_simple_ticker(self.config['symbol'])
                if ticker:
                    current_price = ticker['last_price']
                    unrealized_pnl = (current_price - entry_price) * amount

                    display_text += f"📈 CURRENT POSITION\n"
                    display_text += f"{'=' * 30}\n"
                    display_text += f"Entry Price: {entry_price:,.2f} THB\n"
                    display_text += f"Current Price: {current_price:,.2f} THB\n"
                    display_text += f"Amount: {amount:.8f} {symbol_base}\n"
                    display_text += f"Unrealized P&L: {unrealized_pnl:.2f} THB\n"
                    display_text += f"Entry Time: {entry_time.strftime('%H:%M:%S')}\n\n"

            # Add daily stats
            display_text += f"📊 TODAY'S STATS\n"
            display_text += f"{'=' * 30}\n"
            display_text += f"Trades: {self.daily_trades}/{self.config['max_daily_trades']}\n"
            display_text += f"Daily P&L: {self.daily_pnl:.2f} THB\n"
            display_text += f"Mode: {'PAPER' if self.is_paper_trading else 'REAL'} TRADING\n"

            self.dashboard_display.delete("1.0", "end")
            self.dashboard_display.insert("1.0", display_text)

    def check_signals(self):
        """Enhanced signal checking with detailed analysis"""
        if not self.api_client:
            messagebox.showwarning("Error", "Please connect API first")
            return

        ticker = self.api_client.get_simple_ticker(self.config['symbol'])
        if ticker and len(self.price_history) >= 15:
            price = ticker['last_price']
            rsi = self.strategy.calculate_rsi(list(self.price_history))

            # Get balance for buy signal analysis
            balance = self.api_client.check_balance()
            thb_balance = 0
            if balance and balance.get('error') == 0:
                thb_balance = float(balance['result'].get('THB', 0))

            signal_text = f"\n📊 SIGNAL ANALYSIS - {datetime.now().strftime('%H:%M:%S')}\n"
            signal_text += f"{'=' * 50}\n"
            signal_text += f"Symbol: {ticker['symbol']}\n"
            signal_text += f"Current Price: {price:,.2f} THB\n"
            signal_text += f"24h Change: {ticker['change_24h']:,.2f}%\n"
            signal_text += f"RSI: {rsi:.1f}\n"
            signal_text += f"Available Balance: {thb_balance:,.2f} THB\n\n"

            # Buy signal analysis
            should_buy, buy_reason = self.strategy.should_buy(
                price, rsi, thb_balance, self.config['trade_amount_thb']
            )

            if should_buy:
                signal_text += f"📈 BUY SIGNAL: {buy_reason}\n"
                signal_text += f"   Recommended amount: {self.config['trade_amount_thb']} THB\n"
            else:
                signal_text += f"⏸️ NO BUY SIGNAL: {buy_reason}\n"

            # Sell signal analysis (if position exists)
            if self.strategy.position:
                should_sell, sell_reason = self.strategy.should_sell(price, rsi)
                if should_sell:
                    signal_text += f"📉 SELL SIGNAL: {sell_reason}\n"
                else:
                    signal_text += f"📊 HOLD POSITION: {sell_reason}\n"
            else:
                signal_text += f"💼 NO POSITION\n"

            self.trading_log.insert("end", signal_text)
            self.trading_log.see("end")

    def update_strategy(self, value=None):
        """Enhanced strategy update with validation"""
        self.strategy.rsi_oversold = self.rsi_oversold_var.get()
        self.strategy.rsi_overbought = self.rsi_overbought_var.get()
        self.strategy.stop_loss_pct = self.stop_loss_var.get() / 100
        self.strategy.take_profit_pct = self.take_profit_var.get() / 100

        # Update labels
        self.rsi_oversold_label.configure(text=str(self.strategy.rsi_oversold))
        self.rsi_overbought_label.configure(text=str(self.strategy.rsi_overbought))
        self.stop_loss_label.configure(text=f"{self.strategy.stop_loss_pct * 100:.1f}%")
        self.take_profit_label.configure(text=f"{self.strategy.take_profit_pct * 100:.1f}%")

        # Validate settings
        if self.strategy.rsi_oversold >= self.strategy.rsi_overbought:
            self.log("⚠️ Warning: RSI oversold should be less than overbought")

    def save_settings(self):
        """Enhanced settings save with validation"""
        # Validate settings before saving
        new_amount = self.trade_amount_var.get()
        new_max_trades = self.max_trades_var.get()
        new_max_loss = self.max_loss_var.get()

        warnings = []
        if new_amount > 1000:
            warnings.append(f"High trade amount: {new_amount} THB")
        if new_max_trades > 10:
            warnings.append(f"High daily trade limit: {new_max_trades}")
        if new_max_loss > 5000:
            warnings.append(f"High daily loss limit: {new_max_loss} THB")

        if warnings and not messagebox.askyesno("Settings Warning",
                                                "High risk settings detected:\n\n" +
                                                "\n".join(warnings) +
                                                "\n\nContinue anyway?"):
            return

        # Save settings
        self.config['symbol'] = self.symbol_var.get()
        self.config['trade_amount_thb'] = new_amount
        self.config['max_daily_trades'] = new_max_trades
        self.config['max_daily_loss'] = new_max_loss

        messagebox.showinfo("Success", "Settings saved!")
        self.log(f"Settings updated: Amount={new_amount}, MaxTrades={new_max_trades}, MaxLoss={new_max_loss}")

    def load_trade_history(self):
        """Enhanced trade history loading"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT timestamp, symbol, side, amount, price, pnl, reason, is_paper, order_id
                FROM trades
                ORDER BY timestamp DESC
                LIMIT 100
            ''')

            trades = cursor.fetchall()
            conn.close()

            self.history_display.delete("1.0", "end")

            if not trades:
                self.history_display.insert("1.0", "No trade history found.")
                return

            header = f"{'Time':<10} {'Mode':<6} {'Side':<4} {'Amount':<12} {'Price':<10} {'P&L':<8} {'Order ID':<12} {'Reason'}\n"
            header += "=" * 100 + "\n"
            self.history_display.insert("end", header)

            for trade in trades:
                timestamp, symbol, side, amount, price, pnl, reason, is_paper, order_id = trade
                time_str = datetime.fromisoformat(timestamp).strftime('%H:%M:%S')
                mode = "PAPER" if is_paper else "REAL"

                pnl_str = f"{pnl:.2f}" if pnl else "0.00"
                order_id_str = order_id if order_id else "N/A"

                trade_line = f"{time_str:<10} {mode:<6} {side.upper():<4} {amount:<12.8f} {price:<10.2f} {pnl_str:<8} {order_id_str:<12} {reason}\n"
                self.history_display.insert("end", trade_line)

        except Exception as e:
            self.log(f"Error loading history: {e}")

    def show_statistics(self):
        """Enhanced statistics display"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Overall statistics
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losses,
                    SUM(pnl) as total_pnl,
                    AVG(pnl) as avg_pnl,
                    MAX(pnl) as best_trade,
                    MIN(pnl) as worst_trade
                FROM trades
                WHERE pnl IS NOT NULL
            ''')

            overall_stats = cursor.fetchone()

            # Paper vs Real trading stats
            cursor.execute('''
                SELECT 
                    is_paper,
                    COUNT(*) as trades,
                    SUM(pnl) as total_pnl,
                    AVG(pnl) as avg_pnl
                FROM trades
                WHERE pnl IS NOT NULL
                GROUP BY is_paper
            ''')

            mode_stats = cursor.fetchall()
            conn.close()

            if overall_stats and overall_stats[0] > 0:
                total, wins, losses, total_pnl, avg_pnl, best_trade, worst_trade = overall_stats
                win_rate = (wins / total * 100) if total > 0 else 0

                stats_text = f"""
=== TRADING STATISTICS ===

Overall Performance:
• Total Trades: {total}
• Wins: {wins} ({win_rate:.1f}%)
• Losses: {losses}
• Total P&L: {total_pnl:.2f} THB
• Average P&L: {avg_pnl:.2f} THB
• Best Trade: {best_trade:.2f} THB
• Worst Trade: {worst_trade:.2f} THB

Mode Breakdown:"""

                for is_paper, trades, mode_pnl, mode_avg in mode_stats:
                    mode_name = "Paper Trading" if is_paper else "Real Trading"
                    stats_text += f"""
• {mode_name}: {trades} trades, {mode_pnl:.2f} THB total, {mode_avg:.2f} THB avg"""

                messagebox.showinfo("Trading Statistics", stats_text)
            else:
                messagebox.showinfo("Statistics", "No completed trades found.")

        except Exception as e:
            self.log(f"Error showing statistics: {e}")

    def update_dashboard_enhanced(self):
        """Enhanced dashboard update"""
        # Update status cards
        self.status_cards["Daily Trades"].configure(
            text=f"{self.daily_trades}/{self.config['max_daily_trades']}"
        )

        self.status_cards["Daily P&L"].configure(text=f"{self.daily_pnl:.2f}")

        # Update balance periodically
        self.update_balance()

    def test_connection(self):
        """Enhanced connection test"""
        if not self.api_client:
            self.api_status_display.delete("1.0", "end")
            self.api_status_display.insert("1.0", "❌ Please connect API first")
            return

        self.api_status_display.delete("1.0", "end")
        self.api_status_display.insert("1.0", "🔌 Testing API Connection...\n\n")

        # Test ticker
        ticker = self.api_client.get_simple_ticker(self.config['symbol'])
        if ticker:
            self.api_status_display.insert("end",
                                           f"✅ Market Data: {ticker['symbol']} @ {ticker['last_price']:,.2f} THB\n")
        else:
            self.api_status_display.insert("end", "❌ Market Data: Failed\n")

        # Test balance
        balance = self.api_client.check_balance()
        if balance and balance.get('error') == 0:
            thb_balance = balance['result'].get('THB', 0)
            self.api_status_display.insert("end", f"✅ Balance: {float(thb_balance):,.2f} THB\n")
        else:
            self.api_status_display.insert("end", "❌ Balance: Failed\n")

        # Test system status
        status_ok, status_msg = self.api_client.check_system_status()
        self.api_status_display.insert("end", f"{'✅' if status_ok else '❌'} System: {status_msg}\n")

        self.api_status_display.insert("end", f"\nConnection Test: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def log(self, message):
        """Enhanced logging with timestamps"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        # Add to trading log
        self.trading_log.insert("end", log_entry)
        self.trading_log.see("end")

        # Keep log size manageable
        lines = self.trading_log.get("1.0", "end").split('\n')
        if len(lines) > 1000:
            # Keep last 500 lines
            self.trading_log.delete("1.0", f"{len(lines) - 500}.0")

    def run(self):
        """Start the improved application"""
        # Reset daily counters at startup
        self.daily_trades = 0
        self.daily_pnl = 0

        self.log("🚀 Improved Bitkub Trading Bot Started")
        self.log("📝 Default: PAPER TRADING mode")
        self.log("⚠️ Always test thoroughly before enabling real trading")
        self.log("🧪 Use the Testing tab to verify order execution")

        # Initialize system status
        self.status_cards["System Status"].configure(text="Not Connected", text_color="gray")

        self.root.mainloop()


if __name__ == "__main__":
    # Enhanced startup warning
    print("\n" + "=" * 70)
    print("⚠️  IMPROVED BITKUB TRADING BOT")
    print("=" * 70)
    print("ENHANCEMENTS:")
    print("• Proven order execution methods from successful tests")
    print("• Enhanced error handling and debugging")
    print("• Comprehensive testing features")
    print("• Better risk management and safety checks")
    print("• Improved UI with detailed monitoring")
    print("\nWARNING:")
    print("• This bot trades with REAL MONEY when enabled")
    print("• Always start with PAPER TRADING")
    print("• Use small amounts for initial real trading tests")
    print("• Monitor closely and use emergency stop if needed")
    print("=" * 70 + "\n")

    response = input("Do you understand the risks and want to proceed? (yes/no): ")

    if response.lower() == 'yes':
        app = ImprovedTradingBot()
        app.run()
    else:
        print("Exiting. Please understand the risks before using this bot.")
