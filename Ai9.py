"""
🌑 BLVCK TEA AiTrad V3 - ENHANCED MULTI-COIN EDITION 🌑
Advanced Multi-Coin Analysis with Backtesting
Version: 3.5 - Enhanced Complete

⚠️ WARNING: TRADING CRYPTOCURRENCIES INVOLVES SUBSTANTIAL RISK
- This is experimental software with NO GUARANTEES
- Test in paper mode for at least 3 months before considering real money
- Only use money you can afford to lose completely
- Past performance does not indicate future results

New Features:
✅ Multi-coin scanning (all Bitkub pairs)
✅ 100-200 period data collection
✅ Liquidity & Volatility filtering
✅ Basic backtesting
✅ Enhanced coin scoring system
"""

import customtkinter as ctk
from datetime import datetime, timedelta
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
class FixedBitkubAPI:
    """Fixed Bitkub API with Correct Order Format"""

    def __init__(self, api_key="", api_secret=""):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.bitkub.com"
        self.request_times = deque(maxlen=250)
        self.rate_limit_lock = threading.Lock()

        self.trading_fees = {'maker_fee': 0.0025, 'taker_fee': 0.0025}

        # Complete Bitkub symbol list - CORRECT FORMAT: THB_XXX
        self.all_bitkub_symbols = [
            # Major coins
            "THB_BTC", "THB_ETH", "THB_USDT", "THB_USDC", "THB_BNB", "THB_XRP",
            "THB_ADA", "THB_SOL", "THB_DOGE", "THB_DOT", "THB_MATIC", "THB_ATOM",

            # DeFi & Layer 1
            "THB_LINK", "THB_AVAX", "THB_NEAR", "THB_ALGO", "THB_FTM", "THB_ONE",
            "THB_EGLD", "THB_HBAR", "THB_FLOW", "THB_ICP", "THB_VET", "THB_THETA",
            "THB_FIL", "THB_XTZ", "THB_EOS", "THB_NEO", "THB_WAVES", "THB_QTUM",

            # Gaming & Metaverse
            "THB_SAND", "THB_MANA", "THB_AXS", "THB_GALA", "THB_ENJ", "THB_APE",
            "THB_CHZ", "THB_IMX", "THB_GMX", "THB_MAGIC", "THB_ILV", "THB_YGG",

            # Layer 2 & Scaling
            "THB_ARB", "THB_OP", "THB_LRC", "THB_SKL",

            # Meme coins
            "THB_SHIB", "THB_PEPE", "THB_FLOKI", "THB_BONK",

            # AI & Infrastructure
            "THB_RENDER", "THB_FET", "THB_GRT", "THB_OCEAN", "THB_AGIX",

            # Oracles & Data
            "THB_BAND", "THB_TRB",

            # Exchange tokens
            "THB_KUB", "THB_UNI", "THB_SUSHI", "THB_CAKE", "THB_CRV",

            # Stablecoins & Wrapped
            "THB_DAI", "THB_BUSD", "THB_TUSD", "THB_USDP",
            "THB_WBTC", "THB_WETH", "THB_STETH",

            # Older coins
            "THB_LTC", "THB_BCH", "THB_ETC", "THB_DASH", "THB_ZEC",
            "THB_XMR", "THB_BAT", "THB_ZRX", "THB_OMG", "THB_KNC",

            # Other popular
            "THB_AAVE", "THB_COMP", "THB_MKR", "THB_SNX", "THB_1INCH",
            "THB_BAL", "THB_YFI", "THB_UMA", "THB_REN", "THB_LDO",
            "THB_RPL", "THB_CVX", "THB_FXS", "THB_FRAX",

            # NFT & Social
            "THB_BLUR", "THB_LOOKS", "THB_AUDIO", "THB_MASK",

            # Privacy & Security
            "THB_ROSE", "THB_SCRT", "THB_KEEP",

            # Web3 & Storage
            "THB_AR", "THB_STORJ", "THB_ANKR", "THB_GNO",

            # Regional & Specific
            "THB_JASMY", "THB_C98", "THB_WOO", "THB_TRX",
            "THB_BTT", "THB_WIN", "THB_JST", "THB_SUN",

            # Additional DeFi
            "THB_ALPHA", "THB_RUNE", "THB_PERP", "THB_DYDX",
            "THB_INJ", "THB_KAVA", "THB_LUNA", "THB_LUNC",

            # Emerging projects
            "THB_APT", "THB_SUI", "THB_SEI", "THB_TIA",
            "THB_STRK", "THB_ZK", "THB_GAS", "THB_METIS",

            # Gaming tokens
            "THB_SFP", "THB_TLM", "THB_ALICE", "THB_GODS",
            "THB_MC", "THB_PYR", "THB_VOXEL", "THB_HIGH",

            # Utility tokens
            "THB_HOT", "THB_IOTX", "THB_CELR", "THB_CTSI",
            "THB_CKB", "THB_COTI", "THB_DENT", "THB_PUNDIX",

            # Legacy & Others
            "THB_XEM", "THB_ONT", "THB_ICX", "THB_ZIL",
            "THB_RVN", "THB_SC", "THB_DGB", "THB_SYS",

            # New listings (2024-2025)
            "THB_ORDI", "THB_SATS", "THB_RATS", "THB_PUPS",
            "THB_WIF", "THB_MYRO", "THB_BOME", "THB_SLERF",
            "THB_JTO", "THB_PYTH", "THB_WEN", "THB_JUP",

            # More recent
            "THB_MEME", "THB_NFP", "THB_AI",
            "THB_XAI", "THB_MANTA", "THB_PORTAL",
            "THB_PIXEL", "THB_AEVO", "THB_DYM", "THB_OMNI",

            # Additional tokens
            "THB_PENDLE", "THB_ONDO", "THB_ETHFI", "THB_ENA",
            "THB_W", "THB_SAGA", "THB_TAIKO", "THB_ZRO",
            "THB_LISTA", "THB_IO", "THB_NOT",
            "THB_DOGS", "THB_TON", "THB_CATI", "THB_HMSTR",
            "THB_EIGEN", "THB_NEIRO", "THB_TURBO", "THB_MOG",

            # Very recent additions
            "THB_POPCAT", "THB_GOAT", "THB_GRASS", "THB_USUAL",
            "THB_MOVE", "THB_ME", "THB_VIRTUAL", "THB_VANA"
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
            result = response.json()

            if result.get('error') == 0 and 'result' in result:
                return result
            return {"error": 1, "message": "Invalid response"}

        except Exception as e:
            return {"error": 999, "message": str(e)}

    def get_simple_ticker(self, symbol):
        try:
            self._wait_for_rate_limit()
            response = requests.get(f"{self.base_url}/api/market/ticker", timeout=10)
            data = response.json()

            if isinstance(data, dict):
                # Bitkub uses THB_XXX format
                if symbol in data:
                    ticker_data = data[symbol]
                    return {
                        'symbol': symbol,
                        'last_price': float(ticker_data.get('last', 0)),
                        'change_24h': float(ticker_data.get('percentChange', 0)),
                        'volume_24h': float(ticker_data.get('quoteVolume', 0)),
                        'high_24h': float(ticker_data.get('high24hr', 0)),
                        'low_24h': float(ticker_data.get('low24hr', 0))
                    }

            return None
        except Exception as e:
            print(f"Ticker error for {symbol}: {e}")
            return None

    def calculate_trading_fees(self, amount, price, side):
        """Calculate trading fees"""
        total_value = amount * price
        fee_rate = self.trading_fees['taker_fee']
        return total_value * fee_rate

    def calculate_break_even_price(self, entry_price, side="buy"):
        """Calculate break-even price"""
        fee_rate = self.trading_fees['taker_fee']

        if side == "buy":
            total_fee_impact = (fee_rate * 2) / (1 - fee_rate)
            break_even = entry_price * (1 + total_fee_impact)
        else:
            break_even = entry_price * (1 - fee_rate * 2)

        return break_even

    def place_buy_order_safe(self, symbol, amount_thb, buy_price, order_type="limit"):
        """Place buy order - symbol should be THB_XXX format"""
        try:
            # Symbol should already be in THB_XXX format
            trading_symbol = symbol

            self._wait_for_rate_limit()

            order_data = {
                "sym": trading_symbol,
                "amt": float(amount_thb),
                "rat": float(buy_price) if order_type == "limit" else 0,
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
            return response.json()

        except Exception as e:
            return {"error": 999, "message": str(e)}

    def place_sell_order_safe(self, symbol, amount_crypto, sell_price, order_type="limit"):
        """Place sell order - symbol should be THB_XXX format"""
        try:
            # Symbol should already be in THB_XXX format
            trading_symbol = symbol

            self._wait_for_rate_limit()

            order_data = {
                "sym": trading_symbol,
                "amt": float(amount_crypto),
                "rat": float(sell_price) if order_type == "limit" else 0,
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
            return response.json()

        except Exception as e:
            return {"error": 999, "message": str(e)}


# === ENHANCED MULTI-COIN STRATEGY ===
class AdvancedMultiCoinStrategy:
    """Enhanced Multi-Coin Strategy with Backtesting"""

    def __init__(self, api_client, log_callback=None):
        self.api_client = api_client
        self.log_callback = log_callback

        # Multi-coin data storage
        self.coin_data = {}
        self.min_data_points = 100
        self.max_data_points = 200

        self.position = None

        # Strategy parameters
        self.buy_threshold = 50
        self.min_profit_margin = 0.015
        self.take_profit = 0.025
        self.stop_loss = -0.02
        self.trailing_stop = 0.015

        # Filtering criteria
        self.min_volume_24h = 1000000
        self.max_volatility = 0.15
        self.min_volatility = 0.01

        # Backtesting
        self.backtest_results = {}

    def ai_log(self, message, log_type="decision"):
        """Log AI decisions to appropriate column"""
        if self.log_callback:
            # Always pass as "AI" type to route to columns
            self.log_callback(message, "AI")

    def initialize_coin_data(self, symbol):
        """Initialize data structure for a coin"""
        if symbol not in self.coin_data:
            self.coin_data[symbol] = {
                'prices': deque(maxlen=self.max_data_points),
                'volumes': deque(maxlen=self.max_data_points),
                'timestamps': deque(maxlen=self.max_data_points),
                'highs': deque(maxlen=self.max_data_points),
                'lows': deque(maxlen=self.max_data_points),
                'data_ready': False,
                'last_score': 0,
                'liquidity_ok': False,
                'volatility_ok': False
            }

    def collect_market_data(self, symbols):
        """Collect data for all symbols"""
        collected = 0
        for symbol in symbols:
            self.initialize_coin_data(symbol)

            ticker = self.api_client.get_simple_ticker(symbol)
            if not ticker:
                continue

            coin_data = self.coin_data[symbol]
            coin_data['prices'].append(ticker['last_price'])
            coin_data['volumes'].append(ticker['volume_24h'])
            coin_data['highs'].append(ticker['high_24h'])
            coin_data['lows'].append(ticker['low_24h'])
            coin_data['timestamps'].append(datetime.now())

            if len(coin_data['prices']) >= self.min_data_points:
                coin_data['data_ready'] = True
                collected += 1

            # Log to MARKET column
            if collected % 10 == 0:
                self.ai_log(f"Scanned {collected} coins", "AI")

        return collected

    def calculate_rsi(self, prices, period=14):
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50

        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        if avg_loss == 0:
            return 100

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_volatility(self, prices):
        """Calculate price volatility"""
        if len(prices) < 20:
            return 0

        returns = np.diff(prices) / prices[:-1]
        return np.std(returns)

    def check_liquidity(self, volume_24h):
        """Check liquidity"""
        return volume_24h >= self.min_volume_24h

    def check_volatility(self, symbol):
        """Check volatility range"""
        coin_data = self.coin_data.get(symbol)
        if not coin_data or len(coin_data['prices']) < 20:
            return False

        volatility = self.calculate_volatility(list(coin_data['prices']))
        return self.min_volatility <= volatility <= self.max_volatility

    def filter_tradeable_coins(self):
        """Filter coins based on criteria"""
        tradeable = []

        for symbol, data in self.coin_data.items():
            if not data['data_ready']:
                continue

            current_volume = data['volumes'][-1] if data['volumes'] else 0
            liquidity_ok = self.check_liquidity(current_volume)
            volatility_ok = self.check_volatility(symbol)

            data['liquidity_ok'] = liquidity_ok
            data['volatility_ok'] = volatility_ok

            if liquidity_ok and volatility_ok:
                tradeable.append(symbol)

        return tradeable

    def score_coin(self, symbol):
        """Score a coin"""
        coin_data = self.coin_data.get(symbol)
        if not coin_data or not coin_data['data_ready']:
            return 0

        prices = list(coin_data['prices'])
        volumes = list(coin_data['volumes'])

        score = 20

        # RSI - Log to INDICATORS column
        rsi = self.calculate_rsi(prices)
        self.ai_log(f"RSI: {rsi:.1f}", "AI")

        if rsi < 25:
            score += 40
        elif rsi < 30:
            score += 30
        elif rsi < 40:
            score += 20
        elif rsi > 75:
            score -= 30
        elif rsi > 70:
            score -= 20
        else:
            score += 10

        # Volume - Log to INDICATORS column
        if len(volumes) >= 20:
            recent_avg = np.mean(volumes[-10:])
            older_avg = np.mean(volumes[-20:-10])
            volume_ratio = recent_avg / older_avg if older_avg > 0 else 1

            self.ai_log(f"Vol Ratio: {volume_ratio:.2f}x", "AI")

            if volume_ratio > 1.5:
                score += 25
            elif volume_ratio > 1.3:
                score += 20
            elif volume_ratio > 1.1:
                score += 10

        # Price Trend - Log to INDICATORS column
        if len(prices) >= 10:
            short_trend = (prices[-1] - prices[-5]) / prices[-5] * 100
            medium_trend = (prices[-1] - prices[-10]) / prices[-10] * 100

            self.ai_log(f"Trend: {short_trend:+.1f}%", "AI")

            if short_trend < -2 and medium_trend > -5:
                score += 20
            elif short_trend < -1:
                score += 15
            elif short_trend > 5:
                score -= 15

        # Volatility bonus
        volatility = self.calculate_volatility(prices)
        if 0.03 <= volatility <= 0.08:
            score += 15
        elif 0.02 <= volatility <= 0.10:
            score += 10

        coin_data['last_score'] = score
        return score

    def find_best_coin_to_buy(self, tradeable_coins):
        """Find best coin to buy"""
        if not tradeable_coins:
            return None, 0, "No tradeable coins"

        # Log to DECISION column
        self.ai_log(f"Analyzing {len(tradeable_coins)} coins", "AI")

        best_coin = None
        best_score = 0

        for symbol in tradeable_coins:
            score = self.score_coin(symbol)

            if score > best_score:
                best_score = score
                best_coin = symbol

        # Log result to DECISION column
        if best_coin and best_score >= self.buy_threshold:
            self.ai_log(f"BEST: {best_coin.upper()}", "AI")
            self.ai_log(f"Score: {best_score}", "AI")
            return best_coin, best_score, f"Best signal (Score: {best_score})"
        else:
            self.ai_log(f"No strong signal", "AI")
            self.ai_log(f"Best score: {best_score}", "AI")

        return None, best_score, f"No strong signal (Best: {best_score})"

    def simple_backtest(self, symbol, periods=50):
        """Simple backtest"""
        coin_data = self.coin_data.get(symbol)
        if not coin_data or len(coin_data['prices']) < periods + 20:
            return None

        prices = list(coin_data['prices'])[-periods:]
        wins = 0
        losses = 0
        total_return = 0

        for i in range(20, len(prices) - 5):
            historical_prices = prices[:i]
            score = self.calculate_simple_score(historical_prices)

            if score >= self.buy_threshold:
                entry_price = prices[i]

                for j in range(i + 1, min(i + 6, len(prices))):
                    exit_price = prices[j]
                    return_pct = (exit_price - entry_price) / entry_price

                    if return_pct >= self.take_profit or return_pct <= self.stop_loss:
                        total_return += return_pct
                        if return_pct > 0:
                            wins += 1
                        else:
                            losses += 1
                        break

        total_trades = wins + losses
        win_rate = wins / total_trades if total_trades > 0 else 0

        return {
            'symbol': symbol,
            'trades': total_trades,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'total_return': total_return * 100,
            'avg_return': (total_return / total_trades * 100) if total_trades > 0 else 0
        }

    def calculate_simple_score(self, prices):
        """Simplified scoring for backtesting"""
        if len(prices) < 20:
            return 0

        score = 20
        rsi = self.calculate_rsi(prices)

        if rsi < 30:
            score += 30
        elif rsi < 40:
            score += 20

        return score

    def should_sell_profitable(self, current_price, volume):
        """Check sell conditions"""
        if not self.position:
            return False, "No position"

        entry_price = self.position['entry_price']
        entry_time = self.position['entry_time']

        profit_pct = ((current_price - entry_price) / entry_price)
        hold_time_minutes = (datetime.now() - entry_time).total_seconds() / 60

        if profit_pct >= self.take_profit:
            return True, f"Take profit {profit_pct * 100:.2f}%"

        if profit_pct <= self.stop_loss:
            return True, f"Stop loss {profit_pct * 100:.2f}%"

        if hold_time_minutes > 30 and profit_pct < 0:
            return True, f"Max hold time"

        return False, f"Holding ({profit_pct * 100:.2f}%)"


# === VISUAL WIDGET (same as before) ===
class EnhancedVisualWidget(ctk.CTkFrame):
    """Enhanced Visual Widget"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.canvas = ctk.CTkCanvas(self, bg="#0a0a0a", highlightthickness=0, height=350)
        self.canvas.pack(fill="both", expand=True, pady=(10, 5))

        self.canvas_width = 700
        self.canvas_height = 350
        self.center_x = self.canvas_width // 2
        self.center_y = self.canvas_height // 2

        self.angle = 0
        self.pulse = 0
        self.particles = []
        self.is_active = False
        self.trading_state = "IDLE"

        self.state_colors = {
            "IDLE": "#00ffff",
            "SCANNING": "#0099ff",
            "ANALYZING": "#ff00ff",
            "BUYING": "#00ff00",
            "HOLDING": "#ffff00",
            "SELLING": "#ff00ff",
            "PROFIT": "#00ff00",
            "LOSS": "#ff0000"
        }

        ai_log_label = ctk.CTkLabel(
            self,
            text="AI MULTI-COIN DASHBOARD",
            font=("Arial", 13, "bold"),
            text_color="#00ffff"
        )
        ai_log_label.pack(pady=(5, 5))

        self.log_container = ctk.CTkFrame(self, fg_color="#0a0a0a")
        self.log_container.pack(fill="both", expand=True, padx=5, pady=(0, 5))

        self.column_configs = [
            {"name": "MARKET DATA", "color": "#00ffff", "bg": "#001a1a", "type": "market"},
            {"name": "INDICATORS", "color": "#ff00ff", "bg": "#1a001a", "type": "indicators"},
            {"name": "AI DECISION", "color": "#ffff00", "bg": "#1a1a00", "type": "decision"},
            {"name": "TRADE LOG", "color": "#00ff00", "bg": "#001a00", "type": "trade"}
        ]

        self.ai_log_displays = []

        for i, config in enumerate(self.column_configs):
            col_header = ctk.CTkLabel(
                self.log_container,
                text=config["name"],
                font=("Arial", 10, "bold"),
                text_color=config["color"]
            )
            col_header.grid(row=0, column=i, padx=2, pady=(2, 0), sticky="ew")

            log_box = ctk.CTkTextbox(
                self.log_container,
                font=("Courier", 9, "bold"),
                fg_color=config["bg"],
                text_color=config["color"],
                border_width=2,
                border_color=config["color"]
            )
            log_box.grid(row=1, column=i, padx=2, pady=2, sticky="nsew")
            self.ai_log_displays.append({
                "widget": log_box,
                "type": config["type"],
                "color": config["color"]
            })

        for i in range(4):
            self.log_container.grid_columnconfigure(i, weight=1, uniform="col")

        self.log_container.grid_rowconfigure(0, weight=0)
        self.log_container.grid_rowconfigure(1, weight=1)

        self.create_particles()
        self.animate()

    def create_particles(self):
        for i in range(30):
            particle = {
                'angle': np.random.uniform(0, 2 * math.pi),
                'radius': np.random.uniform(80, 180),
                'speed': np.random.uniform(0.01, 0.02),
                'size': np.random.randint(2, 6)
            }
            self.particles.append(particle)

    def set_trading_state(self, state):
        self.trading_state = state

    def set_active(self, active):
        self.is_active = active

    def animate(self):
        self.canvas.delete("all")

        self.canvas_width = self.canvas.winfo_width() or 700
        self.canvas_height = 350
        self.center_x = self.canvas_width // 2
        self.center_y = self.canvas_height // 2

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
        for i in range(0, self.canvas_width, 40):
            alpha = int(20 + 10 * math.sin(self.angle + i * 0.1))
            grid_color = f"#{alpha:02x}{alpha:02x}{alpha:02x}"
            self.canvas.create_line(i, 0, i, self.canvas_height, fill=grid_color, width=1)

        for i in range(0, self.canvas_height, 40):
            alpha = int(20 + 10 * math.sin(self.angle + i * 0.1))
            grid_color = f"#{alpha:02x}{alpha:02x}{alpha:02x}"
            self.canvas.create_line(0, i, self.canvas_width, i, fill=grid_color, width=1)

    def draw_center_sphere(self, color):
        pulse_size = 60 + 25 * math.sin(self.pulse) if self.is_active else 60

        for i in range(5, 0, -1):
            radius = pulse_size + i * 10
            alpha = int(50 - i * 8)
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            glow_color = f"#{min(r + alpha, 255):02x}{min(g + alpha, 255):02x}{min(b + alpha, 255):02x}"

            self.canvas.create_oval(
                self.center_x - radius, self.center_y - radius,
                self.center_x + radius, self.center_y + radius,
                outline=glow_color, width=2
            )

        self.canvas.create_oval(
            self.center_x - pulse_size, self.center_y - pulse_size,
            self.center_x + pulse_size, self.center_y + pulse_size,
            fill="#001a1a", outline=color, width=3
        )

        for angle in range(0, 360, 24):
            rad = math.radians(angle + self.angle * 50)
            x1 = self.center_x + pulse_size * math.cos(rad) * 0.7
            y1 = self.center_y + pulse_size * math.sin(rad) * 0.7
            self.canvas.create_line(self.center_x, self.center_y, x1, y1, fill=color, width=1)

        dot_size = 10 + 4 * math.sin(self.pulse * 2)
        self.canvas.create_oval(
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

            self.canvas.create_oval(x - size, y - size, x + size, y + size, fill=color, outline="")

    def draw_status_text(self):
        status_display = {
            "IDLE": "IDLE",
            "SCANNING": "SCANNING",
            "ANALYZING": "ANALYZING",
            "BUYING": "BUYING",
            "HOLDING": "HOLDING",
            "SELLING": "SELLING",
            "PROFIT": "PROFIT",
            "LOSS": "LOSS"
        }

        status = status_display.get(self.trading_state, "IDLE")
        color = self.state_colors.get(self.trading_state, "#00ffff")

        self.canvas.create_text(
            self.center_x, 30,
            text=status,
            fill=color, font=("Courier", 20, "bold")
        )

        if self.is_active:
            self.canvas.create_text(
                self.center_x, self.canvas_height - 20,
                text="AI ACTIVE",
                fill="#00ff00", font=("Courier", 14, "bold")
            )

    def add_ai_log(self, message, log_type="decision"):
        """Add message to specific column"""
        timestamp = datetime.now().strftime("%M:%S")

        target_column = None
        for col_config in self.ai_log_displays:
            if col_config["type"] == log_type:
                target_column = col_config
                break

        if not target_column:
            target_column = self.ai_log_displays[2]

        widget = target_column["widget"]

        if len(message) > 50:
            message = message[:47] + "..."

        log_entry = f"[{timestamp}] {message}\n"
        widget.insert("end", log_entry)
        widget.see("end")

        lines = widget.get("1.0", "end").split("\n")
        if len(lines) > 80:
            widget.delete("1.0", "40.0")


# === MAIN TRADING BOT ===
class EnhancedTradingBot(ctk.CTk):
    """Enhanced Multi-Coin Trading Bot"""

    def __init__(self):
        super().__init__()

        self.title("BLVCK TEA AiTrad V3 - ENHANCED MULTI-COIN")
        self.geometry("1400x850")

        self.api_client = None
        self.strategy = None

        self.is_trading = False
        self.is_paper_trading = True
        self.current_balance = 0
        self.paper_balance = 10000
        self.trade_count = 0
        self.win_count = 0
        self.total_pnl = 0
        self.trade_amount_thb = 500

        self.setup_ui()

    def setup_ui(self):
        """Setup UI"""

        # Header
        header = ctk.CTkFrame(self, height=60, fg_color="#1a1a1a")
        header.pack(fill="x", padx=10, pady=(10, 5))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="BLVCK TEA AiTrad V3 - ENHANCED MULTI-COIN",
            font=("Arial", 24, "bold"),
            text_color="#00ffff"
        ).pack(expand=True)

        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=10, pady=5)

        # LEFT
        left_panel = ctk.CTkFrame(main_container)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 5))

        ctk.CTkLabel(
            left_panel,
            text="AI CORE VISUALIZATION",
            font=("Arial", 14, "bold"),
            text_color="#00ffff"
        ).pack(pady=(5, 0))

        self.visual = EnhancedVisualWidget(left_panel, fg_color="#0a0a0a")
        self.visual.pack(fill="both", expand=True, padx=10, pady=5)

        sys_log_label = ctk.CTkLabel(
            left_panel,
            text="SYSTEM LOG",
            font=("Arial", 12, "bold"),
            text_color="#00aaff"
        )
        sys_log_label.pack(pady=(5, 0))

        self.log_display = ctk.CTkTextbox(
            left_panel,
            height=200,
            font=("Courier", 10, "bold"),
            fg_color="#0a0a0a",
            text_color="#ffffff"
        )
        self.log_display.pack(fill="x", padx=10, pady=(5, 10))

        # RIGHT
        right_panel = ctk.CTkFrame(main_container, width=500)
        right_panel.pack(side="right", fill="both", padx=(5, 0))
        right_panel.pack_propagate(False)

        # API
        api_frame = ctk.CTkFrame(right_panel)
        api_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(api_frame, text="API", font=("Arial", 12, "bold")).pack(pady=(5, 5))

        self.api_key_entry = ctk.CTkEntry(api_frame, width=460, height=32, placeholder_text="API Key", show="*")
        self.api_key_entry.pack(pady=2)

        self.api_secret_entry = ctk.CTkEntry(api_frame, width=460, height=32, placeholder_text="API Secret", show="*")
        self.api_secret_entry.pack(pady=2)

        ctk.CTkButton(api_frame, text="Connect", command=self.connect_api, height=30, width=460).pack(pady=3)

        # Mode
        mode_frame = ctk.CTkFrame(right_panel)
        mode_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(mode_frame, text="MODE", font=("Arial", 12, "bold")).pack(pady=5)

        self.mode_var = ctk.StringVar(value="paper")

        mode_btns = ctk.CTkFrame(mode_frame, fg_color="transparent")
        mode_btns.pack()

        ctk.CTkRadioButton(mode_btns, text="Paper", variable=self.mode_var, value="paper",
                           command=self.change_mode).pack(side="left", padx=10)
        ctk.CTkRadioButton(mode_btns, text="Real", variable=self.mode_var, value="real", command=self.change_mode).pack(
            side="left", padx=10)

        amt_row = ctk.CTkFrame(mode_frame, fg_color="transparent")
        amt_row.pack(pady=5)

        ctk.CTkLabel(amt_row, text="Amount:", font=("Arial", 10)).pack(side="left", padx=3)
        self.amount_entry = ctk.CTkEntry(amt_row, width=80)
        self.amount_entry.insert(0, "500")
        self.amount_entry.pack(side="left", padx=3)
        ctk.CTkLabel(amt_row, text="THB").pack(side="left")

        # STRATEGY
        strategy_frame = ctk.CTkFrame(right_panel)
        strategy_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(strategy_frame, text="STRATEGY", font=("Arial", 12, "bold")).pack(pady=(5, 10))

        self.strategy_mode = ctk.StringVar(value="full_auto")

        strategy_radio_frame = ctk.CTkFrame(strategy_frame, fg_color="transparent")
        strategy_radio_frame.pack(fill="x", padx=10)

        ctk.CTkRadioButton(strategy_radio_frame, text="Full Auto", variable=self.strategy_mode, value="full_auto",
                           font=("Arial", 10)).pack(anchor="w", pady=2)
        ctk.CTkRadioButton(strategy_radio_frame, text="Manual", variable=self.strategy_mode, value="manual",
                           font=("Arial", 10)).pack(anchor="w", pady=2)

        self.manual_settings_frame = ctk.CTkFrame(strategy_frame)
        self.manual_settings_frame.pack(fill="x", padx=10, pady=5)

        # Buy
        buy_frame = ctk.CTkFrame(self.manual_settings_frame, fg_color="transparent")
        buy_frame.pack(fill="x", pady=2)

        ctk.CTkLabel(buy_frame, text="Buy:", font=("Arial", 9), width=50).pack(side="left")
        self.buy_threshold_slider = ctk.CTkSlider(buy_frame, from_=20, to=70, number_of_steps=50, height=15)
        self.buy_threshold_slider.set(50)
        self.buy_threshold_slider.pack(side="left", fill="x", expand=True, padx=3)
        self.buy_threshold_label = ctk.CTkLabel(buy_frame, text="50", font=("Arial", 9, "bold"), width=25)
        self.buy_threshold_label.pack(side="left")
        self.buy_threshold_slider.configure(command=lambda v: self.buy_threshold_label.configure(text=f"{int(v)}"))

        # T/P
        tp_frame = ctk.CTkFrame(self.manual_settings_frame, fg_color="transparent")
        tp_frame.pack(fill="x", pady=2)

        ctk.CTkLabel(tp_frame, text="T/P:", font=("Arial", 9), width=50).pack(side="left")
        self.tp_slider = ctk.CTkSlider(tp_frame, from_=0.5, to=5, number_of_steps=45, height=15)
        self.tp_slider.set(2.5)
        self.tp_slider.pack(side="left", fill="x", expand=True, padx=3)
        self.tp_label = ctk.CTkLabel(tp_frame, text="2.5%", font=("Arial", 9, "bold"), width=35)
        self.tp_label.pack(side="left")
        self.tp_slider.configure(command=lambda v: self.tp_label.configure(text=f"{v:.1f}%"))

        # S/L
        sl_frame = ctk.CTkFrame(self.manual_settings_frame, fg_color="transparent")
        sl_frame.pack(fill="x", pady=2)

        ctk.CTkLabel(sl_frame, text="S/L:", font=("Arial", 9), width=50).pack(side="left")
        self.sl_slider = ctk.CTkSlider(sl_frame, from_=0.5, to=3, number_of_steps=25, height=15)
        self.sl_slider.set(2.0)
        self.sl_slider.pack(side="left", fill="x", expand=True, padx=3)
        self.sl_label = ctk.CTkLabel(sl_frame, text="2.0%", font=("Arial", 9, "bold"), width=35)
        self.sl_label.pack(side="left")
        self.sl_slider.configure(command=lambda v: self.sl_label.configure(text=f"{v:.1f}%"))

        ctk.CTkButton(
            self.manual_settings_frame,
            text="Apply",
            command=self.apply_strategy_settings,
            height=28,
            font=("Arial", 10, "bold"),
            fg_color="#0066cc"
        ).pack(pady=5, fill="x", padx=5)

        # Status
        status_frame = ctk.CTkFrame(right_panel)
        status_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(status_frame, text="STATUS", font=("Arial", 12, "bold")).pack(pady=5)

        self.status_labels = {}
        items = [
            ("Mode", "Paper", "#ff8800"),
            ("Balance", "0 THB", "#00ff00"),
            ("Position", "None", "#888888"),
            ("Trades", "0", "#00aaff"),
            ("Win Rate", "0%", "#00ff00"),
            ("P/L", "0 THB", "#00ffff")
        ]

        for label, value, color in items:
            row = ctk.CTkFrame(status_frame, fg_color="transparent")
            row.pack(fill="x", pady=2, padx=10)
            ctk.CTkLabel(row, text=f"{label}:", font=("Arial", 10), width=80, anchor="w").pack(side="left")
            lbl = ctk.CTkLabel(row, text=value, font=("Arial", 10, "bold"), text_color=color, anchor="e")
            lbl.pack(side="right", expand=True, fill="x")
            self.status_labels[label] = lbl

        # Controls
        control_frame = ctk.CTkFrame(right_panel)
        control_frame.pack(fill="x", padx=10, pady=10)

        self.start_button = ctk.CTkButton(
            control_frame,
            text="START",
            command=self.toggle_trading,
            height=45,
            font=("Arial", 13, "bold"),
            fg_color="#00aa00"
        )
        self.start_button.pack(pady=5, padx=10, fill="x")

        ctk.CTkButton(control_frame, text="SCAN ALL", command=self.manual_scan, height=35).pack(pady=5, padx=10,
                                                                                                fill="x")
        ctk.CTkButton(control_frame, text="RUN BACKTEST", command=self.run_backtest, height=35,
                      fg_color="#ff8800").pack(pady=5, padx=10, fill="x")

    def apply_strategy_settings(self):
        """Apply settings"""
        if self.strategy_mode.get() == "manual":
            buy_threshold = int(self.buy_threshold_slider.get())
            take_profit = self.tp_slider.get() / 100
            stop_loss = self.sl_slider.get() / 100

            if self.strategy:
                self.strategy.buy_threshold = buy_threshold
                self.strategy.take_profit = take_profit
                self.strategy.stop_loss = -stop_loss

                self.ai_log(f"Manual Settings Applied", "SYSTEM")
                self.ai_log(f"Buy: {buy_threshold}, TP: {take_profit * 100:.1f}%, SL: {stop_loss * 100:.1f}%", "SYSTEM")
            else:
                self.ai_log("Connect API first", "SYSTEM")
        else:
            self.ai_log("Full Auto Mode", "SYSTEM")

    def ai_log(self, message, log_type="AI"):
        """Unified logging with smart routing to 4 columns"""

        # Default to system log if not AI type
        if log_type != "AI":
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_display.insert("end", f"[{timestamp}] {message}\n")
            self.log_display.see("end")
            return

        # Route to appropriate column
        column_type = "decision"  # default

        # Column 1: MARKET DATA
        if any(keyword in message for keyword in
               ["Price", "Break-even", "Amount:", "Volume", "collected", "data points", "THB", "Entry:", "Exit:"]):
            column_type = "market"

        # Column 2: INDICATORS
        elif any(keyword in message for keyword in
                 ["RSI", "Volatility", "Score", "Ratio", "trend", "oversold", "overbought", "WR=", "Avg=", "trades"]):
            column_type = "indicators"

        # Column 3: AI DECISION
        elif any(keyword in message for keyword in
                 ["ANALYZING", "SIGNAL", "Strategy", "HOLDING", "tradeable", "Best", "strong"]):
            column_type = "decision"

        # Column 4: TRADE LOG
        elif any(keyword in message for keyword in
                 ["BUY", "SELL", "PROFIT", "LOSS", "Order", "Position", "EXECUTION", "FAILED", "opened", "closed"]):
            column_type = "trade"

        # Send to visual widget
        self.visual.add_ai_log(message, column_type)

    def connect_api(self):
        """Connect API"""
        api_key = self.api_key_entry.get().strip()
        api_secret = self.api_secret_entry.get().strip()

        if not api_key or not api_secret:
            self.ai_log("Enter API credentials")
            return

        self.api_client = FixedBitkubAPI(api_key, api_secret)
        self.strategy = AdvancedMultiCoinStrategy(self.api_client, self.ai_log)

        balance = self.api_client.check_balance()

        if balance.get('error') != 0:
            self.ai_log(f"Connection failed: {balance.get('message')}")
            return

        self.ai_log("API Connected")

        if 'result' in balance:
            thb_data = balance['result'].get('THB', {})
            if isinstance(thb_data, dict):
                self.current_balance = float(thb_data.get('available', 0))
            else:
                self.current_balance = float(thb_data)

            self.ai_log(f"Balance: {self.current_balance:,.2f} THB")
            self.update_status()

    def change_mode(self):
        """Change mode"""
        mode = self.mode_var.get()
        self.is_paper_trading = (mode == "paper")

        if self.is_paper_trading:
            self.ai_log("Paper mode")
            self.status_labels["Mode"].configure(text="Paper", text_color="#ff8800")
            self.status_labels["Balance"].configure(text=f"{self.paper_balance:,.0f} THB")
        else:
            self.ai_log("REAL mode - USE WITH EXTREME CAUTION")
            self.status_labels["Mode"].configure(text="REAL", text_color="#ff0000")
            if self.api_client:
                balance = self.api_client.check_balance()
                if balance.get('error') == 0:
                    thb_data = balance['result'].get('THB', {})
                    if isinstance(thb_data, dict):
                        self.current_balance = float(thb_data.get('available', 0))
                    self.status_labels["Balance"].configure(text=f"{self.current_balance:,.0f} THB")

    def toggle_trading(self):
        """Toggle trading"""
        if not self.api_client or not self.strategy:
            self.ai_log("Connect API first")
            return

        self.is_trading = not self.is_trading

        if self.is_trading:
            self.start_button.configure(text="STOP", fg_color="#ff0000")
            self.visual.set_active(True)
            self.ai_log("Trading started")
            threading.Thread(target=self.trading_loop, daemon=True).start()
        else:
            self.start_button.configure(text="START", fg_color="#00aa00")
            self.visual.set_active(False)
            self.ai_log("Stopped")

    def trading_loop(self):
        """Main trading loop"""

        self.ai_log("Collecting market data...")
        self.ai_log("Wait 15-20 minutes for data collection...")

        warmup_count = 0
        required_warmup = self.strategy.min_data_points

        symbols = self.api_client.all_bitkub_symbols

        while self.is_trading:
            try:
                self.trade_amount_thb = float(self.amount_entry.get())

                self.visual.set_trading_state("SCANNING")

                # Collect data
                collected = self.strategy.collect_market_data(symbols)

                if warmup_count < required_warmup:
                    warmup_count += 1
                    if warmup_count % 10 == 0:
                        self.ai_log(f"Collecting data: {warmup_count}/{required_warmup}", "SYSTEM")
                        self.ai_log(f"{collected} coins with data", "AI")
                    time.sleep(10)
                    continue

                if warmup_count == required_warmup:
                    self.ai_log("Data collection complete")
                    self.ai_log("AI Trading Mode: ACTIVE")
                    warmup_count += 1

                current_balance = self.paper_balance if self.is_paper_trading else self.current_balance

                if self.strategy.position is None:
                    self.visual.set_trading_state("ANALYZING")

                    # Filter coins
                    tradeable = self.strategy.filter_tradeable_coins()
                    self.ai_log(f"{len(tradeable)} tradeable coins", "AI")

                    if not tradeable:
                        self.ai_log("No tradeable coins found", "AI")
                        time.sleep(10)
                        continue

                    # Find best coin
                    best_coin, score, reason = self.strategy.find_best_coin_to_buy(tradeable)

                    if best_coin:
                        ticker = self.api_client.get_simple_ticker(best_coin)
                        if ticker:
                            self.execute_buy(best_coin, ticker, reason)
                    else:
                        self.ai_log(reason, "AI")

                else:
                    # Check sell
                    pos_symbol = self.strategy.position['symbol']
                    ticker = self.api_client.get_simple_ticker(pos_symbol)

                    if ticker:
                        should_sell, reason = self.strategy.should_sell_profitable(
                            ticker['last_price'],
                            ticker['volume_24h']
                        )

                        if should_sell:
                            self.execute_sell(pos_symbol, ticker, reason)

                self.update_status()
                time.sleep(10)

            except Exception as e:
                self.ai_log(f"Error: {e}")
                time.sleep(10)

    def execute_buy(self, symbol, ticker, reason):
        """Execute buy with proper logging to all columns"""
        try:
            if self.strategy.position is not None:
                return

            price = ticker['last_price']
            amount_thb = self.trade_amount_thb

            self.visual.set_trading_state("BUYING")

            buy_fee = self.api_client.calculate_trading_fees(amount_thb / price, price, "buy")
            break_even = self.api_client.calculate_break_even_price(price, "buy")

            # Log to MARKET column
            self.ai_log(f"Price: {price:,.2f} THB", "AI")
            self.ai_log(f"Amount: {amount_thb:.0f} THB", "AI")
            self.ai_log(f"Break-even: {break_even:,.2f}", "AI")

            # Log to TRADE column
            self.ai_log(f"BUY: {symbol.upper()}", "AI")
            self.ai_log(f"EXECUTION START", "AI")

            amount_crypto = amount_thb / price

            self.strategy.position = {
                'symbol': symbol,
                'entry_price': price,
                'amount': amount_crypto,
                'entry_time': datetime.now(),
                'invested': amount_thb,
                'break_even_price': break_even,
                'buy_fee': buy_fee,
                'pending': True
            }

            if not self.is_paper_trading:
                result = self.api_client.place_buy_order_safe(symbol, amount_thb, price * 1.002, 'limit')

                if result.get('error') != 0:
                    error_msg = self.api_client.error_codes.get(result.get('error'), 'Unknown error')
                    self.ai_log(f"BUY FAILED: {error_msg}", "AI")
                    self.strategy.position = None
                    return
                else:
                    order_id = result.get('result', {}).get('id', 'N/A')
                    self.ai_log(f"Order ID: {order_id}", "AI")
                    self.strategy.position['pending'] = False
                    self.strategy.position['order_id'] = order_id

            if self.is_paper_trading:
                self.paper_balance -= amount_thb
                self.strategy.position['pending'] = False
            else:
                self.current_balance -= amount_thb

            self.trade_count += 1

            # Log to TRADE column
            self.ai_log("Position opened!", "AI")

            self.visual.set_trading_state("HOLDING")

        except Exception as e:
            self.ai_log(f"BUY ERROR: {str(e)[:30]}", "AI")
            self.strategy.position = None

    def execute_sell(self, symbol, ticker, reason):
        """Execute sell with proper logging"""
        try:
            price = ticker['last_price']
            position = self.strategy.position
            amount = position['amount']

            self.visual.set_trading_state("SELLING")

            entry_price = position['entry_price']
            buy_fee = position['buy_fee']
            sell_fee = self.api_client.calculate_trading_fees(amount, price, "sell")

            gross_pnl = (price - entry_price) * amount
            net_pnl = gross_pnl - buy_fee - sell_fee

            # Log to MARKET column
            self.ai_log(f"Entry: {entry_price:,.0f}", "AI")
            self.ai_log(f"Exit: {price:,.0f}", "AI")

            # Log to TRADE column
            self.ai_log(f"SELL: {reason[:20]}", "AI")
            self.ai_log(f"Net P/L: {net_pnl:+.2f} THB", "AI")

            if not self.is_paper_trading:
                result = self.api_client.place_sell_order_safe(symbol, amount, price * 0.998, 'limit')
                if result.get('error') != 0:
                    self.ai_log(f"SELL FAILED", "AI")
                    return
                else:
                    order_id = result.get('result', {}).get('id', 'N/A')
                    self.ai_log(f"Order: {order_id}", "AI")

            proceeds = amount * price
            if self.is_paper_trading:
                self.paper_balance += proceeds
            else:
                self.current_balance += proceeds

            self.total_pnl += net_pnl

            if net_pnl > 0:
                self.win_count += 1
                self.visual.set_trading_state("PROFIT")
                self.ai_log(f"PROFIT +{net_pnl:,.2f}", "AI")
            else:
                self.visual.set_trading_state("LOSS")
                self.ai_log(f"LOSS {net_pnl:,.2f}", "AI")

            self.ai_log("Position closed!", "AI")
            self.strategy.position = None

        except Exception as e:
            self.ai_log(f"SELL ERROR: {str(e)[:30]}", "AI")

    def manual_scan(self):
        """Manual scan all coins with better debugging"""
        if not self.api_client or not self.strategy:
            self.ai_log("Connect API first")
            return

        self.ai_log("Testing API connection...")

        # Test with just BTC first
        test_symbols = ["btc_thb", "eth_thb", "usdt_thb"]

        for sym in test_symbols:
            ticker = self.api_client.get_simple_ticker(sym)
            if ticker:
                self.ai_log(f"OK: {sym.upper()}: {ticker['last_price']:,.0f} THB")
            else:
                self.ai_log(f"FAIL: {sym} - No data")

        self.ai_log("Full scan starting...")

        symbols = self.api_client.all_bitkub_symbols[:20]  # Test first 20 only
        collected = self.strategy.collect_market_data(symbols)

        self.ai_log(f"Result: {collected}/{len(symbols)} coins OK")

        if collected > 0:
            tradeable = self.strategy.filter_tradeable_coins()
            self.ai_log(f"{len(tradeable)} tradeable coins")

            for sym in tradeable[:5]:  # Show first 5
                score = self.strategy.score_coin(sym)
                ticker = self.api_client.get_simple_ticker(sym)
                if ticker:
                    self.ai_log(f"{sym.upper()}: Score={score}, Price={ticker['last_price']:,.0f}")
        else:
            self.ai_log("ERROR: No data received. Check:")
            self.ai_log("1. API Key/Secret correct?")
            self.ai_log("2. Internet connection OK?")
            self.ai_log("3. Check Python console for errors")

    def run_backtest(self):
        """Run backtest on all coins"""
        if not self.strategy:
            self.ai_log("Connect API first")
            return

        self.ai_log("Running backtest...")

        for symbol, data in self.strategy.coin_data.items():
            if not data['data_ready']:
                continue

            result = self.strategy.simple_backtest(symbol, periods=80)
            if result:
                self.ai_log(
                    f"{symbol.upper()}: {result['trades']} trades, WR={result['win_rate'] * 100:.0f}%, Avg={result['avg_return']:+.2f}%")

    def update_status(self):
        """Update status"""
        balance = self.paper_balance if self.is_paper_trading else self.current_balance
        self.status_labels["Balance"].configure(text=f"{balance:,.0f} THB")

        if self.strategy and self.strategy.position:
            pos = self.strategy.position
            try:
                ticker = self.api_client.get_simple_ticker(pos['symbol'])
                if ticker:
                    pnl = ((ticker['last_price'] - pos['entry_price']) / pos['entry_price']) * 100
                    self.status_labels["Position"].configure(text=f"{pos['symbol'].upper()} ({pnl:+.1f}%)",
                                                             text_color="#ffff00")
            except:
                self.status_labels["Position"].configure(text=pos['symbol'].upper(), text_color="#ffff00")
        else:
            self.status_labels["Position"].configure(text="None", text_color="#888888")

        self.status_labels["Trades"].configure(text=str(self.trade_count))

        wr = (self.win_count / self.trade_count * 100) if self.trade_count > 0 else 0
        self.status_labels["Win Rate"].configure(text=f"{wr:.0f}%")

        pnl_color = "#00ff00" if self.total_pnl >= 0 else "#ff0000"
        self.status_labels["P/L"].configure(text=f"{self.total_pnl:+.0f} THB", text_color=pnl_color)


if __name__ == "__main__":
    print("=" * 60)
    print("WARNING: CRYPTOCURRENCY TRADING INVOLVES SUBSTANTIAL RISK")
    print("=" * 60)
    print("- This is experimental software")
    print("- NO GUARANTEES of profit")
    print("- Test in PAPER MODE for 3+ months first")
    print("- Only risk money you can afford to lose completely")
    print("=" * 60)

    app = EnhancedTradingBot()
    app.mainloop()
