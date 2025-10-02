"""
🌑 BLVCK TEA AiTrad - IMPROVED PROFITABLE VERSION 🌑
Advanced AI-Powered Cryptocurrency Trading Bot
Version: 2.0 - Fixed Strategy with Real Technical Analysis

Key Improvements:
✅ Real RSI + Volume Analysis (not random!)
✅ Proper Fee Calculation (0.5% Bitkub fees)
✅ Better Entry Signals (Score 60+ required)
✅ Smart Exit Strategy (Take Profit, Stop Loss, Trailing Stop)
✅ Risk Management (Max hold time, position sizing)
"""

import customtkinter as ctk
from datetime import datetime
import threading
import time
import numpy as np
from collections import deque
import json
import requests
import hmac
import hashlib
import math
from tkinter import messagebox

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


# === BITKUB API CLIENT ===
class BitkubAPIClient:
    """Bitkub API Client with REAL Trading Support"""

    def __init__(self, api_key="", api_secret=""):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.bitkub.com"
        self.request_times = deque(maxlen=250)
        self.rate_limit_lock = threading.Lock()

        # Bitkub actual fees
        self.trading_fees = {'maker_fee': 0.0025, 'taker_fee': 0.0025}

        self.all_bitkub_symbols = [
            "btc_thb", "eth_thb", "usdt_thb", "usdc_thb", "bnb_thb", "xrp_thb",
            "ada_thb", "sol_thb", "doge_thb", "dot_thb", "matic_thb", "atom_thb",
            "near_thb", "avax_thb", "link_thb", "uni_thb", "ltc_thb", "bch_thb",
        ]

        self.error_codes = {
            0: "Success", 1: "Invalid JSON", 2: "Missing API key",
            3: "Invalid API key", 6: "Missing/invalid signature",
            10: "Invalid parameter", 11: "Invalid symbol",
            12: "Invalid amount", 18: "Insufficient balance",
            90: "Server error"
        }

    def _wait_for_rate_limit(self):
        with self.rate_limit_lock:
            now = time.time()
            while self.request_times and (now - self.request_times[0]) > 10:
                self.request_times.popleft()
            if len(self.request_times) >= 190:
                time.sleep(1)
                self.request_times.clear()
            self.request_times.append(now)

    def get_server_time(self):
        try:
            response = requests.get(f"{self.base_url}/api/v3/servertime", timeout=10)
            return response.json()
        except:
            return int(time.time() * 1000)

    def create_signature(self, timestamp, method, path, body=""):
        signature_string = f"{timestamp}{method}{path}{body}"
        return hmac.new(
            self.api_secret.encode('utf-8'),
            signature_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def check_balance(self):
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
            return {"error": 999, "message": str(e)}

    def get_simple_ticker(self, symbol):
        try:
            self._wait_for_rate_limit()
            response = requests.get(f"{self.base_url}/api/market/ticker", timeout=10)
            data = response.json()

            if isinstance(data, dict):
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
                            'change_24h': float(ticker_data.get('percentChange', 0)),
                            'volume_24h': float(ticker_data.get('quoteVolume', 0)),
                            'high_24h': float(ticker_data.get('high24hr', 0)),
                            'low_24h': float(ticker_data.get('low24hr', 0))
                        }
            return None
        except Exception as e:
            return None

    def normalize_symbol_for_trading(self, symbol):
        symbol = symbol.lower().replace("thb_", "").replace("_thb", "")
        return f"{symbol}_thb"

    def place_buy_order_safe(self, symbol, amount_thb, buy_price, order_type="limit"):
        """🔥 PLACE REAL BUY ORDER"""
        try:
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

            print(f"🔥 REAL BUY - {trading_symbol}: {amount_thb} THB @ {buy_price}")
            print(f"API Response: {result}")

            return result
        except Exception as e:
            return {"error": 999, "message": str(e)}

    def place_sell_order_safe(self, symbol, amount_crypto, sell_price, order_type="limit"):
        """🔥 PLACE REAL SELL ORDER"""
        try:
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

            print(f"🔥 REAL SELL - {trading_symbol}: {amount_crypto} @ {sell_price}")
            print(f"API Response: {result}")

            return result
        except Exception as e:
            return {"error": 999, "message": str(e)}


# === 3D VISUAL WIDGET ===
class Visual3DWidget(ctk.CTkCanvas):
    """3D-like Visual Widget"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg="#0a0a0a", highlightthickness=0, **kwargs)

        self.width = kwargs.get('width', 900)
        self.height = kwargs.get('height', 700)
        self.center_x = self.width // 2
        self.center_y = self.height // 2

        self.angle = 0
        self.pulse = 0
        self.particles = []
        self.is_active = False
        self.trading_state = "IDLE"
        self.state_colors = {
            "IDLE": "#00ffff",
            "SCANNING": "#0099ff",
            "BUYING": "#00ff00",
            "HOLDING": "#ffff00",
            "SELLING": "#ff00ff",
            "PROFIT": "#00ff00",
            "LOSS": "#ff0000"
        }

        self.create_particles()
        self.animate()

    def create_particles(self):
        for i in range(50):
            particle = {
                'angle': np.random.uniform(0, 2 * math.pi),
                'radius': np.random.uniform(150, 350),
                'speed': np.random.uniform(0.01, 0.03),
                'size': np.random.randint(4, 10)
            }
            self.particles.append(particle)

    def set_trading_state(self, state):
        self.trading_state = state

    def set_active(self, active):
        self.is_active = active

    def animate(self):
        self.delete("all")

        state_color = self.state_colors.get(self.trading_state, "#00ffff")

        self.draw_grid(state_color)
        self.draw_center_sphere(state_color)
        self.draw_particles(state_color)
        self.draw_status_text()

        speed = 0.04 if self.is_active else 0.02
        self.angle += speed
        self.pulse += 0.08 if self.is_active else 0.05

        self.after(50, self.animate)

    def draw_grid(self, color):
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)

        for i in range(0, self.width, 50):
            alpha = int(30 + 20 * math.sin(self.angle + i * 0.1))
            grid_color = f"#{alpha:02x}{alpha:02x}{alpha:02x}"
            self.create_line(i, 0, i, self.height, fill=grid_color, width=1)

        for i in range(0, self.height, 50):
            alpha = int(30 + 20 * math.sin(self.angle + i * 0.1))
            grid_color = f"#{alpha:02x}{alpha:02x}{alpha:02x}"
            self.create_line(0, i, self.width, i, fill=grid_color, width=1)

    def draw_center_sphere(self, color):
        pulse_size = 80 + 40 * math.sin(self.pulse) if self.is_active else 80

        for i in range(8, 0, -1):
            radius = pulse_size + i * 15
            alpha = int(80 - i * 10)
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            glow_color = f"#{min(r + alpha, 255):02x}{min(g + alpha, 255):02x}{min(b + alpha, 255):02x}"
            self.create_oval(
                self.center_x - radius, self.center_y - radius,
                self.center_x + radius, self.center_y + radius,
                outline=glow_color, width=3
            )

        self.create_oval(
            self.center_x - pulse_size, self.center_y - pulse_size,
            self.center_x + pulse_size, self.center_y + pulse_size,
            fill="#001a1a", outline=color, width=5
        )

        for angle in range(0, 360, 15):
            rad = math.radians(angle + self.angle * 50)
            x1 = self.center_x + pulse_size * math.cos(rad) * 0.8
            y1 = self.center_y + pulse_size * math.sin(rad) * 0.8
            self.create_line(self.center_x, self.center_y, x1, y1, fill=color, width=2)

        dot_size = 12 + 6 * math.sin(self.pulse * 2)
        self.create_oval(
            self.center_x - dot_size, self.center_y - dot_size,
            self.center_x + dot_size, self.center_y + dot_size,
            fill=color, outline=""
        )

    def draw_particles(self, color):
        for particle in self.particles:
            particle['angle'] += particle['speed'] * (2 if self.is_active else 1)

            x = self.center_x + particle['radius'] * math.cos(particle['angle'])
            y = self.center_y + particle['radius'] * math.sin(particle['angle']) * 0.6

            z = math.sin(particle['angle'] + self.angle)
            size = particle['size'] * (0.5 + z * 0.5)

            self.create_oval(
                x - size, y - size,
                x + size, y + size,
                fill=color, outline=""
            )

    def draw_status_text(self):
        status_display = {
            "IDLE": "⚪ IDLE",
            "SCANNING": "🔍 SCANNING",
            "BUYING": "💰 BUYING",
            "HOLDING": "📊 HOLDING",
            "SELLING": "💸 SELLING",
            "PROFIT": "🎉 PROFIT",
            "LOSS": "📉 LOSS"
        }

        status = status_display.get(self.trading_state, "⚪ IDLE")
        color = self.state_colors.get(self.trading_state, "#00ffff")

        self.create_text(
            self.center_x, 50,
            text=status,
            fill=color, font=("Courier", 32, "bold")
        )

        if self.is_active:
            self.create_text(
                self.center_x, self.height - 30,
                text="🟢 TRADING ACTIVE",
                fill="#00ff00", font=("Courier", 24, "bold")
            )


# === IMPROVED AI DECISION ENGINE ===
class ImprovedAIEngine:
    """AI Engine with REAL Technical Analysis - Not Random!"""

    def __init__(self):
        self.decision_history = deque(maxlen=100)

    def analyze_coin_properly(self, symbol, ticker_data, historical_prices):
        """Proper analysis with REAL indicators"""

        decision = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'score': 0,
            'factors': {},
            'price': ticker_data['last_price']
        }

        # 1. RSI Analysis (25 = oversold, 75 = overbought)
        if len(historical_prices) >= 15:
            rsi = self.calculate_rsi(historical_prices)

            if rsi < 25:  # Strong oversold
                decision['factors']['rsi'] = 40
                decision['confidence'] = 'HIGH'
            elif rsi < 30:  # Oversold
                decision['factors']['rsi'] = 30
            elif rsi > 75:  # Overbought
                decision['factors']['rsi'] = -40
            elif rsi > 70:
                decision['factors']['rsi'] = -30
            else:
                decision['factors']['rsi'] = (50 - rsi) * 0.3

            decision['rsi_value'] = rsi

        # 2. Volume Analysis
        volume_24h = ticker_data.get('volume_24h', 0)
        if volume_24h > 0:
            # Volume spike (มากกว่า 1M = ดี)
            if volume_24h > 5000000:
                decision['factors']['volume'] = 30
            elif volume_24h > 1000000:
                decision['factors']['volume'] = 20
            else:
                decision['factors']['volume'] = 0

        # 3. Price Change Analysis (24h)
        change_24h = ticker_data.get('change_24h', 0)

        # ถ้าราคาลงมาก แต่ volume สูง = โอกาสดี (oversold bounce)
        if change_24h < -3 and volume_24h > 1000000:
            decision['factors']['price_drop'] = 30
        elif change_24h < -5:
            decision['factors']['price_drop'] = 20
        elif change_24h > 5:  # Pump มาก = อันตราย
            decision['factors']['price_drop'] = -20

        # 4. Volatility Check (High - Low range)
        high_24h = ticker_data.get('high_24h', 0)
        low_24h = ticker_data.get('low_24h', 0)
        current_price = ticker_data['last_price']

        if high_24h > 0 and low_24h > 0:
            range_pct = ((high_24h - low_24h) / low_24h) * 100
            position_in_range = ((current_price - low_24h) / (high_24h - low_24h)) * 100

            # ถ้าราคาใกล้ low ของวัน = โอกาสดี
            if position_in_range < 30:  # ใกล้ low
                decision['factors']['position'] = 20
            elif position_in_range > 70:  # ใกล้ high
                decision['factors']['position'] = -20

        # Calculate total score
        decision['score'] = sum(decision['factors'].values())

        # Recommendation with STRICT threshold
        if decision['score'] >= 60:
            decision['recommendation'] = 'STRONG BUY'
        elif decision['score'] >= 40:
            decision['recommendation'] = 'BUY'
        elif decision['score'] <= -30:
            decision['recommendation'] = 'SELL'
        else:
            decision['recommendation'] = 'HOLD'

        return decision

    def calculate_rsi(self, prices, period=14):
        """Calculate RSI properly"""
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


# === MAIN APPLICATION ===
class BlvckTeaAiTradImproved(ctk.CTk):
    """BLVCK TEA AiTrad - Improved Profitable Version"""

    def __init__(self):
        super().__init__()

        self.title("🌑 BLVCK TEA AiTrad V2 - Improved Strategy")
        self.geometry("1600x900")

        # Components
        self.api_client = None
        self.ai_engine = ImprovedAIEngine()

        # States
        self.is_trading = False
        self.is_paper_trading = True
        self.current_balance = 0
        self.trade_count = 0
        self.win_count = 0
        self.loss_count = 0
        self.current_position = None
        self.trade_amount_thb = 1000

        # Price history storage
        self.price_history = {}

        # Setup UI
        self.setup_ui()

    def setup_ui(self):
        """Setup UI"""
        # Header
        header = ctk.CTkFrame(self, height=70, fg_color="#0a0a0a")
        header.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(
            header,
            text="🌑 BLVCK TEA AiTrad V2 - IMPROVED 🌑",
            font=("Arial", 28, "bold"),
            text_color="#00ffff"
        ).pack(pady=10)

        # Main container
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=5, pady=5)

        # === LEFT: 3D Visual ===
        left_panel = ctk.CTkFrame(main_container)
        left_panel.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        ctk.CTkLabel(
            left_panel,
            text="🎯 AI CORE VISUALIZATION",
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        visual_container = ctk.CTkFrame(left_panel, fg_color="transparent")
        visual_container.pack(fill="both", expand=True, padx=10, pady=10)

        self.visual_3d = Visual3DWidget(visual_container, width=900, height=700)
        self.visual_3d.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Log overlay
        log_overlay = ctk.CTkFrame(
            visual_container,
            width=550,
            height=250,
            fg_color="#000000",
            corner_radius=10,
            border_width=2,
            border_color="#00ffff"
        )
        log_overlay.place(relx=0.98, rely=0.98, anchor="se")

        ctk.CTkLabel(
            log_overlay,
            text="📜 TRADING LOG",
            font=("Arial", 14, "bold"),
            text_color="#00ffff"
        ).pack(pady=5)

        self.log_display = ctk.CTkTextbox(
            log_overlay,
            font=("Courier", 11, "bold"),
            text_color="#00ffff",
            fg_color="transparent"
        )
        self.log_display.pack(fill="both", expand=True, padx=5, pady=5)

        # === RIGHT: Controls ===
        right_panel = ctk.CTkFrame(main_container, width=500)
        right_panel.pack(side="right", fill="both", padx=5, pady=5)

        # API Section
        api_frame = ctk.CTkFrame(right_panel)
        api_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(api_frame, text="🔌 API CONNECTION", font=("Arial", 14, "bold")).pack()

        self.api_key_entry = ctk.CTkEntry(api_frame, width=400, show="*", placeholder_text="API Key")
        self.api_key_entry.pack(pady=5)

        self.api_secret_entry = ctk.CTkEntry(api_frame, width=400, show="*", placeholder_text="API Secret")
        self.api_secret_entry.pack(pady=5)

        ctk.CTkButton(api_frame, text="🔗 Connect API", command=self.connect_api, height=35).pack(pady=5)

        # Trading Mode
        mode_frame = ctk.CTkFrame(right_panel)
        mode_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(mode_frame, text="🎮 TRADING MODE", font=("Arial", 14, "bold")).pack()

        self.mode_var = ctk.StringVar(value="paper")

        ctk.CTkRadioButton(
            mode_frame,
            text="📝 Paper Trading (Safe - Recommended)",
            variable=self.mode_var,
            value="paper",
            command=self.change_mode
        ).pack(pady=5)

        ctk.CTkRadioButton(
            mode_frame,
            text="🔥 Real Trading (ACTUAL MONEY!)",
            variable=self.mode_var,
            value="real",
            command=self.change_mode
        ).pack(pady=5)

        # Trade Amount
        amount_frame = ctk.CTkFrame(mode_frame)
        amount_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(amount_frame, text="💰 Trade Amount (THB):").pack(side="left", padx=5)
        self.amount_entry = ctk.CTkEntry(amount_frame, width=100)
        self.amount_entry.insert(0, "1000")
        self.amount_entry.pack(side="left", padx=5)

        # Status
        status_frame = ctk.CTkFrame(right_panel)
        status_frame.pack(fill="x", padx=10, pady=10)

        self.status_labels = {}
        status_items = ["Balance", "Position", "Trades", "Win Rate"]

        for name in status_items:
            row = ctk.CTkFrame(status_frame)
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{name}:", width=100).pack(side="left")
            label = ctk.CTkLabel(row, text="---", text_color="#00ffff")
            label.pack(side="right")
            self.status_labels[name] = label

        # Controls
        control_frame = ctk.CTkFrame(right_panel)
        control_frame.pack(fill="x", padx=10, pady=10)

        self.start_button = ctk.CTkButton(
            control_frame,
            text="🚀 START AUTO TRADING",
            command=self.toggle_trading,
            fg_color="#00ff00",
            text_color="#000",
            height=50,
            font=("Arial", 14, "bold")
        )
        self.start_button.pack(pady=5)

        ctk.CTkButton(
            control_frame,
            text="🔍 SCAN COINS",
            command=self.manual_scan,
            height=40
        ).pack(pady=5)

        # Improvements Info
        info_frame = ctk.CTkFrame(right_panel)
        info_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            info_frame,
            text="✅ V2 IMPROVEMENTS",
            font=("Arial", 12, "bold"),
            text_color="#00ff00"
        ).pack()

        improvements = [
            "• Real RSI Analysis (not random!)",
            "• Proper Fee Calculation (0.5%)",
            "• Better Entry (Score 60+)",
            "• Smart Exit Strategy",
            "• Risk Management"
        ]

        for imp in improvements:
            ctk.CTkLabel(
                info_frame,
                text=imp,
                font=("Arial", 10),
                text_color="#00ffff"
            ).pack(anchor="w", padx=10)

    def log(self, message, color="#00ffff"):
        """Add log entry"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        if "BUY SIGNAL" in message or "EXIT" in message or "=" in message:
            self.log_display.insert("1.0", f"{message}\n")
        else:
            self.log_display.insert("1.0", f"[{timestamp}] {message}\n")

        content = self.log_display.get("1.0", "end").split("\n")
        if len(content) > 100:
            self.log_display.delete("100.0", "end")

    def connect_api(self):
        """Connect API"""
        api_key = self.api_key_entry.get()
        api_secret = self.api_secret_entry.get()

        if not api_key or not api_secret:
            messagebox.showwarning("Error", "Enter API credentials")
            return

        self.log("🔄 Connecting to Bitkub API...")

        def connect():
            self.api_client = BitkubAPIClient(api_key, api_secret)
            balance = self.api_client.check_balance()

            if balance and balance.get('error') == 0:
                try:
                    thb_data = balance['result'].get('THB', 0)
                    if isinstance(thb_data, dict):
                        thb = float(thb_data.get('available', 0))
                    else:
                        thb = float(thb_data)

                    self.current_balance = thb
                    self.status_labels['Balance'].configure(text=f"{thb:,.2f} THB")
                    self.log("✅ API Connected Successfully")
                    self.log(f"💰 Balance: {thb:,.2f} THB")
                except:
                    self.log("⚠️ Connected but parse error")
            else:
                self.log("❌ Connection failed")

        threading.Thread(target=connect, daemon=True).start()

    def change_mode(self):
        """Change trading mode"""
        mode = self.mode_var.get()

        if mode == "real":
            if not messagebox.askyesno(
                    "⚠️ REAL TRADING WARNING",
                    "Switch to REAL TRADING mode?\n\n"
                    "⚠️ THIS WILL USE REAL MONEY!\n\n"
                    "Have you:\n"
                    "✅ Tested with Paper Trading first?\n"
                    "✅ Set appropriate trade amount?\n"
                    "✅ Checked your Bitkub balance?\n\n"
                    "Are you sure?"
            ):
                self.mode_var.set("paper")
                return

            if not messagebox.askyesno(
                    "🔥 FINAL WARNING",
                    "LAST CHANCE TO CANCEL!\n\n"
                    "This will enable REAL MONEY TRADING.\n\n"
                    "Continue?"
            ):
                self.mode_var.set("paper")
                return

            self.is_paper_trading = False
            self.log("🔥 SWITCHED TO REAL TRADING MODE", "#ff0000")
        else:
            self.is_paper_trading = True
            self.log("📝 Switched to Paper Trading (Safe)", "#00ff00")

    def toggle_trading(self):
        """Toggle trading"""
        if self.is_trading:
            self.stop_trading()
        else:
            self.start_trading()

    def start_trading(self):
        """Start trading"""
        if not self.api_client:
            messagebox.showwarning("Error", "Please connect API first")
            return

        try:
            self.trade_amount_thb = float(self.amount_entry.get())
            if self.trade_amount_thb < 100:
                messagebox.showwarning("Error", "Minimum 100 THB")
                return
        except:
            messagebox.showwarning("Error", "Invalid amount")
            return

        if not self.is_paper_trading:
            if not messagebox.askyesno(
                    "🔥 START REAL TRADING",
                    f"Start with REAL MONEY?\n\n"
                    f"Amount: {self.trade_amount_thb:,.0f} THB\n"
                    f"Balance: {self.current_balance:,.2f} THB\n\n"
                    f"Start?"
            ):
                return

        self.is_trading = True
        self.visual_3d.set_active(True)

        mode_text = "📝 PAPER" if self.is_paper_trading else "🔥 REAL"

        self.start_button.configure(
            text="⏸️ STOP TRADING",
            fg_color="#ff0000"
        )

        self.log("")
        self.log("=" * 60)
        self.log(f"🚀 AUTO TRADING STARTED ({mode_text})")
        self.log("=" * 60)
        self.log(f"💰 Trade Amount: {self.trade_amount_thb:,.0f} THB")
        self.log(f"🤖 Strategy: Real RSI + Volume Analysis")
        self.log(f"🎯 Entry Threshold: Score 60+")
        self.log(f"💸 Fees: 0.5% (Buy 0.25% + Sell 0.25%)")
        self.log(f"📊 Take Profit: +2.0% | Stop Loss: -1.5%")
        self.log("=" * 60)
        self.log("")

        threading.Thread(target=self.trading_loop, daemon=True).start()

    def stop_trading(self):
        """Stop trading"""
        self.is_trading = False
        self.visual_3d.set_active(False)

        self.start_button.configure(
            text="🚀 START AUTO TRADING",
            fg_color="#00ff00"
        )

        total_trades = self.win_count + self.loss_count
        win_rate = (self.win_count / total_trades * 100) if total_trades > 0 else 0

        self.log("")
        self.log("=" * 60)
        self.log("⏸️ AUTO TRADING STOPPED")
        self.log(f"📊 Total Trades: {total_trades}")
        self.log(f"✅ Wins: {self.win_count} | ❌ Losses: {self.loss_count}")
        self.log(f"📈 Win Rate: {win_rate:.1f}%")
        self.log("=" * 60)

    def trading_loop(self):
        """Trading loop"""
        cycle = 0
        while self.is_trading:
            cycle += 1

            time.sleep(10)  # Check every 10 seconds

            if self.current_position:
                self.check_exit_conditions(cycle)
            else:
                self.look_for_entry(cycle)

    def look_for_entry(self, cycle):
        """Look for entry with REAL analysis"""
        self.visual_3d.set_trading_state("SCANNING")

        coins = ['btc_thb', 'eth_thb', 'sol_thb', 'avax_thb', 'matic_thb', 'link_thb']

        best_coin = None
        best_score = 0
        best_decision = None

        self.log(f"🔍 Cycle {cycle} - Analyzing {len(coins)} coins...")

        for coin in coins:
            ticker = self.api_client.get_simple_ticker(coin)
            if not ticker:
                continue

            # Store price history
            if coin not in self.price_history:
                self.price_history[coin] = deque(maxlen=50)
            self.price_history[coin].append(ticker['last_price'])

            # Analyze with REAL indicators
            decision = self.ai_engine.analyze_coin_properly(
                coin, ticker, list(self.price_history[coin])
            )

            rsi_val = decision.get('rsi_value', 50)

            self.log(f"   {coin.upper()}: Score={decision['score']:.1f} "
                     f"RSI={rsi_val:.0f} Vol={ticker['volume_24h'] / 1000000:.1f}M")

            if decision['score'] > best_score:
                best_score = decision['score']
                best_coin = coin
                best_decision = decision

        # Only buy if score >= 60
        if best_score >= 60 and best_coin and best_decision:
            ticker = self.api_client.get_simple_ticker(best_coin)

            self.log("")
            self.log(f"🎯 STRONG BUY SIGNAL DETECTED!")
            self.log(f"   Coin: {best_coin.upper()}")
            self.log(f"   Score: {best_score:.1f}/100 (Threshold: 60)")

            factors_str = ", ".join([f"{k}={v:+.1f}" for k, v in best_decision['factors'].items()])
            self.log(f"   Factors: {factors_str}")

            self.execute_buy(best_coin, ticker['last_price'], best_decision)
        else:
            if best_coin:
                self.log(f"⏸️ Best: {best_coin.upper()} ({best_score:.1f}) - Need 60+ to buy")
            else:
                self.log(f"⏸️ No signals found")
            self.visual_3d.set_trading_state("IDLE")

    def execute_buy(self, symbol, price, decision):
        """Execute buy with proper targets"""
        mode = "📝 PAPER" if self.is_paper_trading else "🔥 REAL"

        # Calculate REAL break-even (includes 0.5% fees)
        fee_percent = 0.005
        break_even_price = price * (1 + fee_percent)

        # Targets
        take_profit_price = break_even_price * 1.015  # +1.5% above break-even = +2% total
        stop_loss_price = price * 0.985  # -1.5%

        self.log("")
        self.log("=" * 60)
        self.log(f"✅ BUY SIGNAL: {symbol.upper()}")
        self.log("=" * 60)
        self.log(f"{mode} Executing: {self.trade_amount_thb:,.0f} THB")
        self.log("")
        self.log(f"📈 PRICE TARGETS:")
        self.log(f"   Entry:        {price:,.2f} THB")
        self.log(f"   Break-even:   {break_even_price:,.2f} THB (+0.5%)")
        self.log(f"   Take Profit:  {take_profit_price:,.2f} THB (+2.0%)")
        self.log(f"   Stop Loss:    {stop_loss_price:,.2f} THB (-1.5%)")
        self.log("")
        self.log(f"🎯 DECISION FACTORS:")
        for factor, value in decision['factors'].items():
            self.log(f"   {factor}: {value:+.1f}")
        self.log("=" * 60)

        if self.is_paper_trading:
            crypto_amount = self.trade_amount_thb / price
            self.current_position = {
                'symbol': symbol,
                'entry_price': price,
                'amount': crypto_amount,
                'entry_time': datetime.now(),
                'break_even': break_even_price,
                'take_profit': take_profit_price,
                'stop_loss': stop_loss_price,
                'mode': 'paper',
                'peak_price': price
            }
            self.log(f"📝 Paper position: {crypto_amount:.6f} {symbol.split('_')[0].upper()}")
        else:
            buy_price = price * 1.002

            result = self.api_client.place_buy_order_safe(
                symbol, self.trade_amount_thb, buy_price, 'limit'
            )

            if result and result.get('error') == 0:
                order_info = result['result']
                crypto_amount = order_info.get('rec', self.trade_amount_thb / buy_price)

                self.current_position = {
                    'symbol': symbol,
                    'entry_price': buy_price,
                    'amount': crypto_amount,
                    'entry_time': datetime.now(),
                    'break_even': break_even_price,
                    'take_profit': take_profit_price,
                    'stop_loss': stop_loss_price,
                    'order_id': order_info.get('id'),
                    'mode': 'real',
                    'peak_price': buy_price
                }

                self.log(f"✅ 🔥 REAL BUY SUCCESS!", "#00ff00")
            else:
                error_msg = result.get("message", "Unknown error")
                self.log(f"❌ 🔥 REAL BUY FAILED: {error_msg}", "#ff0000")
                return

        self.trade_count += 1
        self.status_labels['Trades'].configure(text=str(self.trade_count))
        self.status_labels['Position'].configure(text=f"LONG {symbol.upper()}")
        self.visual_3d.set_trading_state("HOLDING")

    def check_exit_conditions(self, cycle):
        """Check exit with proper targets"""
        if not self.current_position:
            return

        symbol = self.current_position['symbol']
        ticker = self.api_client.get_simple_ticker(symbol)

        if not ticker:
            return

        current_price = ticker['last_price']
        entry_price = self.current_position['entry_price']
        break_even = self.current_position['break_even']
        take_profit = self.current_position['take_profit']
        stop_loss = self.current_position['stop_loss']
        peak_price = self.current_position.get('peak_price', entry_price)

        # Update peak price
        if current_price > peak_price:
            self.current_position['peak_price'] = current_price
            peak_price = current_price

        # Calculate P&L
        pnl_percent = ((current_price - entry_price) / entry_price) * 100
        pnl_from_breakeven = ((current_price - break_even) / break_even) * 100

        hold_time = (datetime.now() - self.current_position['entry_time']).total_seconds()

        should_exit = False
        reason = ""

        # 1. Take Profit
        if current_price >= take_profit:
            should_exit = True
            reason = f"✅ TAKE PROFIT ({pnl_percent:+.2f}%)"
            self.visual_3d.set_trading_state("PROFIT")

        # 2. Stop Loss
        elif current_price <= stop_loss:
            should_exit = True
            reason = f"🛑 STOP LOSS ({pnl_percent:+.2f}%)"
            self.visual_3d.set_trading_state("LOSS")

        # 3. Trailing Stop (if above break-even)
        elif current_price > break_even:
            # If price drops 0.7% from peak
            drop_from_peak = ((current_price - peak_price) / peak_price) * 100
            if drop_from_peak <= -0.7:
                should_exit = True
                reason = f"📉 TRAILING STOP ({pnl_percent:+.2f}%)"

        # 4. Max Hold Time (15 minutes)
        elif hold_time >= 900:
            should_exit = True
            reason = f"⏰ TIME EXIT ({pnl_percent:+.2f}%)"

        # Log status every 15 seconds
        if int(hold_time) % 15 == 0 and int(hold_time) > 0:
            mins = int(hold_time / 60)
            secs = int(hold_time % 60)

            self.log("")
            self.log(f"📊 POSITION STATUS ({mins}:{secs:02d})")
            self.log(f"   Current:   {current_price:,.2f} THB")
            self.log(f"   Entry:     {entry_price:,.2f} THB")
            self.log(f"   P&L:       {pnl_percent:+.2f}%")

            if current_price >= break_even:
                self.log(f"   ✅ Above break-even: {pnl_from_breakeven:+.2f}%")
                self.log(f"   🎯 Target TP: {take_profit:,.2f} THB")
            else:
                need = ((break_even - current_price) / current_price) * 100
                self.log(f"   ⚠️ Below break-even: Need +{need:.2f}%")

        if should_exit:
            self.execute_sell(current_price, reason)

    def execute_sell(self, price, reason):
        """Execute sell"""
        if not self.current_position:
            return

        mode = "📝 PAPER" if self.is_paper_trading else "🔥 REAL"
        symbol = self.current_position['symbol']
        amount = self.current_position['amount']
        entry_price = self.current_position['entry_price']

        # Calculate real P&L (after fees)
        pnl_percent = ((price - entry_price) / entry_price) * 100
        pnl_thb = (price - entry_price) * amount

        # Fees
        buy_fee = entry_price * amount * 0.0025
        sell_fee = price * amount * 0.0025
        net_pnl = pnl_thb - buy_fee - sell_fee

        self.log("")
        self.log("=" * 60)
        self.log(f"🔔 EXIT: {reason}")
        self.log("=" * 60)
        self.log(f"{mode} Selling: {amount:.6f} @ {price:,.2f}")
        self.log("")
        self.log(f"📊 TRADE SUMMARY:")
        self.log(f"   Entry:     {entry_price:,.2f} THB")
        self.log(f"   Exit:      {price:,.2f} THB")
        self.log(f"   Gross P&L: {pnl_percent:+.2f}%")
        self.log(f"   Fees:      -{(buy_fee + sell_fee):.2f} THB")
        self.log(f"   Net P&L:   {net_pnl:+.2f} THB")

        if self.is_paper_trading:
            if net_pnl > 0:
                self.log(f"🎉 Paper Profit: +{net_pnl:.2f} THB", "#00ff00")
                self.win_count += 1
            else:
                self.log(f"📉 Paper Loss: {net_pnl:.2f} THB", "#ff0000")
                self.loss_count += 1
        else:
            sell_price = price * 0.998

            result = self.api_client.place_sell_order_safe(
                symbol, amount, sell_price, 'limit'
            )

            if result and result.get('error') == 0:
                self.log(f"✅ 🔥 REAL SELL SUCCESS!", "#00ff00")

                if net_pnl > 0:
                    self.log(f"🎉 Real Profit: +{net_pnl:.2f} THB", "#00ff00")
                    self.win_count += 1
                else:
                    self.log(f"📉 Real Loss: {net_pnl:.2f} THB", "#ff0000")
                    self.loss_count += 1
            else:
                error_msg = result.get("message", "Unknown")
                self.log(f"❌ 🔥 REAL SELL FAILED: {error_msg}", "#ff0000")
                return

        self.log("=" * 60)

        # Update win rate
        total = self.win_count + self.loss_count
        win_rate = (self.win_count / total * 100) if total > 0 else 0
        self.status_labels['Win Rate'].configure(text=f"{win_rate:.1f}%")

        # Clear position
        self.current_position = None
        self.status_labels['Position'].configure(text="None")
        self.visual_3d.set_trading_state("IDLE")

    def manual_scan(self):
        """Manual scan"""
        if not self.api_client:
            messagebox.showwarning("Error", "Connect API first")
            return

        self.log("🔍 Manual scan initiated...")

        def scan():
            coins = ['btc_thb', 'eth_thb', 'sol_thb', 'avax_thb', 'matic_thb', 'link_thb']
            results = []

            for coin in coins:
                ticker = self.api_client.get_simple_ticker(coin)
                if not ticker:
                    continue

                if coin not in self.price_history:
                    self.price_history[coin] = deque(maxlen=50)
                self.price_history[coin].append(ticker['last_price'])

                decision = self.ai_engine.analyze_coin_properly(
                    coin, ticker, list(self.price_history[coin])
                )

                results.append((coin, decision['score'], decision.get('rsi_value', 50)))

            results.sort(key=lambda x: x[1], reverse=True)

            self.log("")
            self.log(f"✅ Scan complete - {len(results)} coins analyzed")
            self.log("")
            for coin, score, rsi in results:
                self.log(f"   {coin.upper()}: Score={score:.1f} RSI={rsi:.0f}")

            if results:
                self.log("")
                self.log(f"🎯 Top: {results[0][0].upper()} (Score: {results[0][1]:.1f})")

        threading.Thread(target=scan, daemon=True).start()

    def run(self):
        """Run app"""
        self.mainloop()


if __name__ == "__main__":
    print("🌑 Starting BLVCK TEA AiTrad V2 - Improved...")
    app = BlvckTeaAiTradImproved()
    app.run()
