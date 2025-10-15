"""
🌑 BLVCK TEA AiTrad V3.9 - COMPLETE FULL VERSION 🌑
แก้ไขปัญหาทั้งหมด + เพิ่ม Learning System + CHARTS + REAL-TIME STATS

✅ COMPLETE: โค้ดครบถ้วน 100% จากต้นฉบับ
✅ NEW: กราฟแสดงผลการเทรด Real-time
✅ NEW: ปริมาณเหรียญที่ถือ (Holding Amount)
✅ NEW: มูลค่าปัจจุบัน (Current Value)
✅ NEW: % กำไร/ขาดทุน Real-time (+/-)
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
import pickle
import os

# Chart imports
try:
    import matplotlib
    matplotlib.use('TkAgg')
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️ matplotlib not installed - charts disabled")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class FixedBitkubAPI:
    """✅ FIXED: Bitkub API with Complete Symbol Map"""

    def __init__(self, api_key="", api_secret=""):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.bitkub.com"
        self.request_times = deque(maxlen=250)
        self.rate_limit_lock = threading.Lock()

        self.trading_fees = {'maker_fee': 0.0025, 'taker_fee': 0.0025}
        self.error_codes = {
            0: "Success", 1: "Invalid JSON", 2: "Missing API KEY",
            3: "Invalid API key", 11: "Invalid symbol", 18: "Insufficient balance"
        }

        self.all_bitkub_symbols = []
        self.verified_symbols = set()

        # Complete Symbol Map
        self.symbol_map = {
            "THB_BTC": "btc_thb", "THB_ETH": "eth_thb", "THB_BNB": "bnb_thb",
            "THB_ADA": "ada_thb", "THB_XRP": "xrp_thb", "THB_SOL": "sol_thb",
            "THB_DOT": "dot_thb", "THB_AVAX": "avax_thb", "THB_MATIC": "matic_thb",
            "THB_ATOM": "atom_thb", "THB_NEAR": "near_thb", "THB_SAND": "sand_thb",
            "THB_MANA": "mana_thb", "THB_AXS": "axs_thb", "THB_GALA": "gala_thb",
            "THB_ENJ": "enj_thb", "THB_LINK": "link_thb", "THB_UNI": "uni_thb",
            "THB_AAVE": "aave_thb", "THB_COMP": "comp_thb", "THB_MKR": "mkr_thb",
            "THB_SNX": "snx_thb", "THB_LRC": "lrc_thb", "THB_GRT": "grt_thb",
            "THB_DOGE": "doge_thb", "THB_SHIB": "shib_thb", "THB_USDT": "usdt_thb",
            "THB_USDC": "usdc_thb", "THB_LTC": "ltc_thb", "THB_BCH": "bch_thb",
            "THB_ETC": "etc_thb", "THB_TRX": "trx_thb", "THB_XLM": "xlm_thb",
            "THB_XTZ": "xtz_thb", "THB_ALGO": "algo_thb", "THB_FLOW": "flow_thb",
            "THB_ICP": "icp_thb", "THB_FET": "fet_thb", "THB_OCEAN": "ocean_thb",
            "THB_FIL": "fil_thb", "THB_AR": "ar_thb", "THB_VET": "vet_thb",
            "THB_HBAR": "hbar_thb", "THB_APT": "apt_thb", "THB_SUI": "sui_thb",
            "THB_ARB": "arb_thb", "THB_OP": "op_thb", "THB_BLUR": "blur_thb",
            "THB_LDO": "ldo_thb", "THB_CHZ": "chz_thb", "THB_BAT": "bat_thb",
            "THB_KNC": "knc_thb", "THB_ZRX": "zrx_thb", "THB_ANKR": "ankr_thb",
            "THB_DYDX": "dydx_thb", "THB_ENS": "ens_thb", "THB_LUNA": "luna_thb",
            "THB_FTM": "ftm_thb", "THB_RUNE": "rune_thb", "THB_KAVA": "kava_thb",
            "THB_BAND": "band_thb", "THB_ALPHA": "alpha_thb", "THB_KUB": "kub_thb",
            "THB_SIX": "six_thb", "THB_JFIN": "jfin_thb", "THB_YFI": "yfi_thb",
            "THB_SUSHI": "sushi_thb", "THB_HOT": "hot_thb", "THB_ZIL": "zil_thb",
            "THB_AUDIO": "audio_thb", "THB_PENDLE": "pendle_thb", "THB_GMX": "gmx_thb",
            "THB_TIA": "tia_thb", "THB_JTO": "jto_thb", "THB_PYTH": "pyth_thb",
            "THB_MANTA": "manta_thb", "THB_AEVO": "aevo_thb", "THB_ONDO": "ondo_thb",
            "THB_ETHFI": "ethfi_thb", "THB_ENA": "ena_thb", "THB_W": "w_thb",
            "THB_TAIKO": "taiko_thb", "THB_ZRO": "zro_thb", "THB_IO": "io_thb",
            "THB_TON": "ton_thb", "THB_CATI": "cati_thb", "THB_EIGEN": "eigen_thb",
            "THB_GRASS": "grass_thb", "THB_ME": "me_thb", "THB_VIRTUAL": "virtual_thb"
        }

        self.reverse_symbol_map = {v: k for k, v in self.symbol_map.items()}
        self.symbols_to_check = list(set(self.symbol_map.values()))

    def normalize_symbol_for_trading(self, symbol):
        """Convert symbol using map"""
        symbol = symbol.upper()
        if symbol in self.symbol_map:
            return self.symbol_map[symbol]
        
        parts = symbol.lower().split('_')
        if len(parts) == 2:
            if parts[1] == 'thb':
                return symbol.lower()
            elif parts[0] == 'thb':
                return f"{parts[1]}_thb"
        
        return f"{symbol.lower()}_thb"

    def verify_symbol(self, symbol):
        """Verify symbol with detailed logging"""
        if symbol in self.verified_symbols:
            verified = self.normalize_symbol_for_trading(symbol)
            return True, verified
        
        if symbol in self.symbol_map:
            verified = self.symbol_map[symbol]
            self.verified_symbols.add(symbol)
            return True, verified
        
        if symbol in self.reverse_symbol_map:
            verified = symbol
            self.verified_symbols.add(symbol)
            return True, verified
        
        normalized = self.normalize_symbol_for_trading(symbol)
        if normalized in self.all_bitkub_symbols:
            self.verified_symbols.add(symbol)
            return True, normalized
        
        return False, symbol

    def _wait_for_rate_limit(self):
        with self.rate_limit_lock:
            now = time.time()
            while len(self.request_times) > 0 and now - self.request_times[0] > 10:
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

    def test_api_connection(self):
        """Test API and discover symbols"""
        try:
            response = requests.get(f"{self.base_url}/api/market/ticker", timeout=10)
            if response.status_code != 200:
                return False, f"HTTP {response.status_code}"

            data = response.json()
            verified_count = 0
            
            for display_format, trading_format in self.symbol_map.items():
                if display_format in data or trading_format in data:
                    self.verified_symbols.add(trading_format)
                    verified_count += 1

            for symbol_key in data.keys():
                if "THB" in symbol_key.upper():
                    normalized = self.normalize_symbol_for_trading(symbol_key)
                    self.verified_symbols.add(normalized)

            self.all_bitkub_symbols = sorted(list(self.verified_symbols))
            return True, f"API OK - {len(self.all_bitkub_symbols)} symbols"

        except Exception as e:
            return False, str(e)

    def get_simple_ticker(self, symbol):
        """Get ticker - Try multiple formats"""
        try:
            self._wait_for_rate_limit()
            response = requests.get(f"{self.base_url}/api/market/ticker", timeout=10)
            
            if response.status_code != 200:
                return None

            data = response.json()
            
            symbol_variations = [symbol, symbol.upper(), symbol.lower()]
            if symbol in self.reverse_symbol_map:
                symbol_variations.append(self.reverse_symbol_map[symbol])
            
            parts = symbol.split('_')
            if len(parts) == 2:
                symbol_variations.append(f"THB_{parts[0].upper()}")
                symbol_variations.append(f"{parts[0].upper()}_THB")

            for variant in symbol_variations:
                ticker_data = data.get(variant)
                if ticker_data:
                    return {
                        'last_price': float(ticker_data.get('last', 0)),
                        'high_24h': float(ticker_data.get('high24hr', 0)),
                        'low_24h': float(ticker_data.get('low24hr', 0)),
                        'volume_24h': float(ticker_data.get('baseVolume', 0))
                    }
            
            return None

        except Exception as e:
            return None

    def calculate_trading_fees(self, amount, price, order_type):
        total_value = amount * price
        return total_value * self.trading_fees['taker_fee']

    def calculate_break_even_price(self, entry_price, order_type):
        total_fee_rate = self.trading_fees['taker_fee'] * 2
        return entry_price * (1 + total_fee_rate)

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
            return {"error": 999, "message": str(e)}

    def place_buy_order_safe(self, symbol, amount_thb, buy_price, order_type="limit"):
        """Place buy with decimal handling + validation"""
        trading_symbol = self.normalize_symbol_for_trading(symbol)
        is_valid, verified_symbol = self.verify_symbol(symbol)
        
        if not is_valid:
            return {"error": 11, "message": f"Invalid symbol"}

        trading_symbol = verified_symbol
        buy_price = round(float(buy_price), 8)
        amount_thb = round(float(amount_thb), 2)

        if amount_thb < 10:
            return {"error": 12, "message": "Amount too low"}

        balance = self.check_balance()
        if balance and balance.get('error') == 0:
            thb_data = balance['result'].get('THB', {})
            if isinstance(thb_data, dict):
                available = float(thb_data.get('available', 0))
            else:
                available = float(thb_data)

            if available < amount_thb:
                return {"error": 18, "message": f"Insufficient: {available:.2f}"}

        max_retries = 3
        for attempt in range(max_retries):
            try:
                self._wait_for_rate_limit()

                order_data = {
                    "sym": trading_symbol,
                    "amt": amount_thb,
                    "rat": buy_price,
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

                error_code = result.get('error', 999)
                if error_code in [3, 5, 11, 18] or error_code == 0:
                    return result
                
                if attempt < max_retries - 1:
                    time.sleep(2)

            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    return {"error": 999, "message": str(e)}
        
        return {"error": 999, "message": "Max retries"}

    def place_sell_order_safe(self, symbol, amount_crypto, sell_price, order_type="limit"):
        """Place sell with decimal handling + validation"""
        trading_symbol = self.normalize_symbol_for_trading(symbol)
        is_valid, verified_symbol = self.verify_symbol(symbol)
        
        if not is_valid:
            return {"error": 11, "message": f"Invalid symbol"}

        trading_symbol = verified_symbol
        sell_price = round(float(sell_price), 8)
        amount_crypto = round(float(amount_crypto), 8)

        max_retries = 3
        for attempt in range(max_retries):
            try:
                self._wait_for_rate_limit()

                order_data = {
                    "sym": trading_symbol,
                    "amt": amount_crypto,
                    "rat": sell_price,
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

                error_code = result.get('error', 999)
                if error_code in [3, 5, 11, 18] or error_code == 0:
                    return result
                
                if attempt < max_retries - 1:
                    time.sleep(2)

            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    return {"error": 999, "message": str(e)}
        
        return {"error": 999, "message": "Max retries"}


class AdvancedMultiCoinStrategy:
    """✅ COMPLETE: Enhanced Multi-Coin Strategy with Learning System"""

    def __init__(self, api_client, log_callback=None):
        self.api_client = api_client
        self.log_callback = log_callback

        self.coin_data = {}
        self.min_data_points = 1000
        self.optimal_data_points = 10000
        self.max_data_points = 200000

        self.total_data_collected = 0
        self.data_save_file = "bot_experience.pkl"

        self.position = None

        self.buy_threshold = 45
        self.min_profit_margin = 0.015
        self.take_profit = 0.025
        self.stop_loss = -0.02
        self.trailing_stop = 0.015

        self.min_volume_24h = 50000
        self.max_volatility = 0.30
        self.min_volatility = 0.003

        self.backtest_results = {}

        self.blacklisted_symbols = set()
        self.symbol_error_counts = {}
        self.max_errors_per_symbol = 3

        # Machine Learning Components
        self.trade_history = []
        self.coin_performance = {}
        self.score_analysis = {
            '40-50': {'wins': 0, 'losses': 0, 'total_profit': 0},
            '50-60': {'wins': 0, 'losses': 0, 'total_profit': 0},
            '60-70': {'wins': 0, 'losses': 0, 'total_profit': 0},
            '70-80': {'wins': 0, 'losses': 0, 'total_profit': 0},
        }
        self.time_performance = {
            '00-06': {'wins': 0, 'losses': 0},
            '06-12': {'wins': 0, 'losses': 0},
            '12-18': {'wins': 0, 'losses': 0},
            '18-24': {'wins': 0, 'losses': 0},
        }
        self.learning_enabled = True
        self.min_trades_for_learning = 10

        self.load_experience()

    def ai_log(self, message, category="decision"):
        if self.log_callback:
            self.log_callback(message, category)

    def load_experience(self):
        """Load saved experience data"""
        if os.path.exists(self.data_save_file):
            try:
                with open(self.data_save_file, 'rb') as f:
                    saved_data = pickle.load(f)
                    loaded_coin_data = saved_data.get('coin_data', {})
                    self.total_data_collected = saved_data.get('total_collected', 0)

                    self.trade_history = saved_data.get('trade_history', [])
                    self.coin_performance = saved_data.get('coin_performance', {})
                    self.score_analysis = saved_data.get('score_analysis', self.score_analysis)
                    self.time_performance = saved_data.get('time_performance', self.time_performance)
                    learned_threshold = saved_data.get('buy_threshold', self.buy_threshold)

                    if learned_threshold != self.buy_threshold and len(self.trade_history) >= 20:
                        self.buy_threshold = learned_threshold

                for symbol, data in loaded_coin_data.items():
                    if symbol not in self.coin_data:
                        self.coin_data[symbol] = data
                    else:
                        existing = self.coin_data[symbol]
                        for key in ['prices', 'volumes', 'highs', 'lows', 'timestamps']:
                            if key in data and key in existing:
                                combined = list(data[key]) + list(existing[key])
                                if len(combined) > self.max_data_points:
                                    combined = combined[-self.max_data_points:]
                                existing[key] = deque(combined, maxlen=self.max_data_points)

                        if len(existing['prices']) >= self.min_data_points:
                            existing['data_ready'] = True

                total_points = sum(len(data['prices']) for data in self.coin_data.values())
                ready_coins = sum(1 for data in self.coin_data.values() if data.get('data_ready', False))
                total_trades = len(self.trade_history)

                if self.log_callback:
                    self.log_callback(f"Loaded {total_points:,} points + {total_trades} trades", "SYSTEM")

                return True
            except Exception as e:
                return False
        return False

    def save_experience(self):
        """Save experience data"""
        try:
            save_data = {
                'coin_data': self.coin_data,
                'total_collected': self.total_data_collected,
                'saved_at': datetime.now().isoformat(),
                'trade_history': self.trade_history[-200:],
                'coin_performance': self.coin_performance,
                'score_analysis': self.score_analysis,
                'time_performance': self.time_performance,
                'buy_threshold': self.buy_threshold,
            }

            with open(self.data_save_file, 'wb') as f:
                pickle.dump(save_data, f)

            return True
        except Exception as e:
            return False

    def initialize_coin_data(self, symbol):
        """Initialize data structure for a coin"""
        if symbol not in self.coin_data:
            self.coin_data[symbol] = {
                'prices': deque(maxlen=self.max_data_points),
                'volumes': deque(maxlen=self.max_data_points),
                'highs': deque(maxlen=self.max_data_points),
                'lows': deque(maxlen=self.max_data_points),
                'timestamps': deque(maxlen=self.max_data_points),
                'data_ready': False,
                'last_score': 0,
                'liquidity_ok': False,
                'volatility_ok': False
            }

    def collect_market_data(self, symbols):
        """✅ FIXED: Collect data with detailed logging"""
        collected = 0
        failed = 0

        for i, symbol in enumerate(symbols):
            try:
                self.initialize_coin_data(symbol)
                ticker = self.api_client.get_simple_ticker(symbol)

                if not ticker:
                    failed += 1
                    continue

                if ticker['last_price'] <= 0:
                    failed += 1
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
                self.total_data_collected += 1

                # ✅ IMPROVED: Log progress every 50 coins
                if (i + 1) % 50 == 0:
                    self.ai_log(f"📊 Progress: {i + 1}/{len(symbols)} coins ({collected} OK, {failed} fail)", "SCAN")

            except Exception as e:
                failed += 1
                continue

        # ✅ IMPROVED: Always log summary
        if self.log_callback:
            self.log_callback(f"✅ {collected} coins scanned successfully", "SYSTEM")
            self.log_callback(f"📈 Total Experience: {self.total_data_collected:,} points", "SYSTEM")
            if failed > 0:
                self.log_callback(f"⚠️ Failed: {failed} symbols", "SYSTEM")

        # ✅ Auto-save every 100 points
        if self.total_data_collected % 100 == 0 and self.total_data_collected > 0:
            self.save_experience()

        return collected

    def calculate_volatility_safe(self, prices):
        """Calculate volatility with safety checks"""
        if len(prices) < 21:
            return 0

        try:
            recent_prices = prices[-21:]
            price_changes = np.diff(recent_prices)
            base_prices = np.array(recent_prices[:-1])

            base_prices = np.where(base_prices == 0, 1e-10, base_prices)
            returns = price_changes / base_prices

            returns = returns[np.isfinite(returns)]

            if len(returns) < 5:
                return 0

            volatility = np.std(returns)

            if not np.isfinite(volatility):
                return 0

            return min(volatility, 1.0)

        except Exception as e:
            return 0

    def filter_tradeable_coins(self):
        """Filter coins with blacklist"""
        try:
            tradeable = []

            for symbol, data in self.coin_data.items():
                try:
                    if symbol in self.blacklisted_symbols:
                        continue

                    if self.symbol_error_counts.get(symbol, 0) >= self.max_errors_per_symbol:
                        self.blacklisted_symbols.add(symbol)
                        continue

                    if not data.get('data_ready', False):
                        continue

                    prices = data.get('prices')
                    volumes = data.get('volumes')

                    if not prices or not volumes or len(prices) < 50:
                        continue

                    recent_prices = list(prices)[-50:]
                    recent_volumes = list(volumes)[-50:]

                    if len(recent_volumes) < 20:
                        continue

                    avg_volume = np.mean(recent_volumes[-20:])

                    if avg_volume < self.min_volume_24h:
                        continue

                    volatility = self.calculate_volatility_safe(recent_prices)

                    if volatility > self.max_volatility or volatility < self.min_volatility:
                        continue

                    data['liquidity_ok'] = True
                    data['volatility_ok'] = True
                    tradeable.append(symbol)

                except Exception as e:
                    continue

            if self.log_callback:
                self.log_callback(f"Filter: {len(tradeable)}/{len(self.coin_data)} passed", "SCAN")

            return tradeable

        except Exception as e:
            if self.log_callback:
                self.log_callback(f"ERROR: Filter failed", "SCAN")
            return []

    def record_symbol_error(self, symbol):
        """Track errors per symbol"""
        if symbol not in self.symbol_error_counts:
            self.symbol_error_counts[symbol] = 0

        self.symbol_error_counts[symbol] += 1

        if self.symbol_error_counts[symbol] >= self.max_errors_per_symbol:
            self.blacklisted_symbols.add(symbol)
            self.ai_log(f"Blacklisted: {symbol}", "AI")

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
        if avg_gain == 0:
            return 0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def find_best_coin_to_buy(self, tradeable_coins):
        """Find best coin to buy - WITH ML ENHANCEMENTS"""
        if not tradeable_coins:
            return None, 0, "No tradeable coins"

        if hasattr(self, 'blacklisted_symbols'):
            tradeable_coins = [s for s in tradeable_coins if s not in self.blacklisted_symbols]
            if not tradeable_coins:
                return None, 0, "All coins blacklisted"

        best_coin = None
        best_score = 0
        all_scores = []

        current_hour = datetime.now().hour
        time_slot = self._get_time_slot(current_hour)
        time_perf = self.time_performance.get(time_slot, {'wins': 0, 'losses': 0})
        time_trades = time_perf['wins'] + time_perf['losses']
        time_win_rate = time_perf['wins'] / time_trades if time_trades > 0 else 0.5

        for symbol in tradeable_coins:
            data = self.coin_data.get(symbol)
            if not data:
                continue

            prices = data.get('prices')
            volumes = data.get('volumes')

            if not prices or not volumes:
                continue

            recent_prices = list(prices)[-50:]
            recent_volumes = list(volumes)[-50:]

            if len(recent_prices) < 21:
                continue

            score = 0

            rsi = self.calculate_rsi(recent_prices)
            if rsi < 30:
                score += 40
            elif rsi < 40:
                score += 25
            elif rsi < 50:
                score += 10

            if len(recent_prices) >= 6:
                recent_trend = (recent_prices[-1] - recent_prices[-5]) / recent_prices[-5]
                if recent_trend < -0.02:
                    score += 15
                elif recent_trend < -0.01:
                    score += 8

            if len(recent_volumes) >= 11:
                volume_ratio = recent_volumes[-1] / np.mean(recent_volumes[-10:])
                if volume_ratio > 1.5:
                    score += 20
                elif volume_ratio > 1.2:
                    score += 10

            volatility = self.calculate_volatility_safe(recent_prices)
            if 0.01 <= volatility <= 0.15:
                score += 15
            elif 0.005 <= volatility <= 0.20:
                score += 8

            # ML ENHANCEMENTS
            if self.learning_enabled:
                if symbol in self.coin_performance:
                    perf = self.coin_performance[symbol]
                    if perf['trades'] >= 5:
                        coin_wr = perf['wins'] / perf['trades']
                        if coin_wr > 0.70:
                            score += 15
                        elif coin_wr < 0.30:
                            score -= 20

                if time_trades >= 5:
                    if time_win_rate > 0.65:
                        score += 5
                    elif time_win_rate < 0.40:
                        score -= 10

            data['last_score'] = score
            all_scores.append((symbol, score, rsi, recent_volumes[-1]))

            if score > best_score:
                best_score = score
                best_coin = symbol

        all_scores.sort(key=lambda x: x[1], reverse=True)

        # ✅ FIXED: ใช้ method ที่มีอยู่
        if self.log_callback:
            # Try to update visual scores if possible
            try:
                if hasattr(self.log_callback, '__self__'):
                    bot = self.log_callback.__self__
                    if hasattr(bot, 'update_visual_scores'):
                        scores_for_visual = [(s[0], s[1]) for s in all_scores[:10]]
                        bot.update_visual_scores(scores_for_visual)
            except:
                pass  # Silent fail if method not available
            
            self.log_callback(f"Analyzed: {len(all_scores)} coins", "SCAN")
            self.log_callback(f"Best: {best_coin} Score={best_score}", "SCAN")

        if best_score >= self.buy_threshold:
            if self.log_callback:
                self.log_callback(f"READY TO BUY (Threshold: {self.buy_threshold})", "AI")
            return best_coin, best_score, f"Strong signal (Score: {best_score})"
        else:
            if self.log_callback:
                self.log_callback(f"No signal (Best: {best_score})", "AI")
            return None, best_score, f"No strong signal"

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

    def learn_from_trade(self, symbol, entry_score, profit_pct):
        """Learn from completed trade"""
        try:
            is_win = profit_pct > 0

            trade_record = {
                'symbol': symbol,
                'entry_score': entry_score,
                'profit_pct': profit_pct,
                'win': is_win,
                'timestamp': datetime.now(),
                'hour': datetime.now().hour
            }
            self.trade_history.append(trade_record)

            if symbol not in self.coin_performance:
                self.coin_performance[symbol] = {'wins': 0, 'losses': 0, 'trades': 0, 'total_profit': 0}

            perf = self.coin_performance[symbol]
            perf['trades'] += 1
            perf['total_profit'] += profit_pct
            if is_win:
                perf['wins'] += 1
            else:
                perf['losses'] += 1

            if 40 <= entry_score < 50:
                bucket = '40-50'
            elif 50 <= entry_score < 60:
                bucket = '50-60'
            elif 60 <= entry_score < 70:
                bucket = '60-70'
            elif 70 <= entry_score < 80:
                bucket = '70-80'
            else:
                bucket = None

            if bucket and bucket in self.score_analysis:
                score_data = self.score_analysis[bucket]
                score_data['total_profit'] += profit_pct
                if is_win:
                    score_data['wins'] += 1
                else:
                    score_data['losses'] += 1

            time_slot = self._get_time_slot(datetime.now().hour)
            if time_slot in self.time_performance:
                time_data = self.time_performance[time_slot]
                if is_win:
                    time_data['wins'] += 1
                else:
                    time_data['losses'] += 1

            if len(self.trade_history) >= self.min_trades_for_learning and len(self.trade_history) % 10 == 0:
                self._adjust_threshold()

            self.ai_log(f"Learned: {symbol} Score={entry_score:.0f}", "AI")

        except Exception as e:
            pass

    def _get_time_slot(self, hour):
        """Get time slot for hour"""
        if 0 <= hour < 6:
            return '00-06'
        elif 6 <= hour < 12:
            return '06-12'
        elif 12 <= hour < 18:
            return '12-18'
        else:
            return '18-24'

    def _adjust_threshold(self):
        """Adjust buy threshold with statistical validation"""
        try:
            total_trades = len(self.trade_history)

            if total_trades < 30:
                return

            recent_trades = self.trade_history[-30:]
            wins = sum(1 for t in recent_trades if t.get('win', False))
            win_rate = wins / len(recent_trades)

            std_error = math.sqrt(win_rate * (1 - win_rate) / len(recent_trades))
            confidence_margin = 1.96 * std_error

            if win_rate - confidence_margin > 0.65:
                old_threshold = self.buy_threshold
                self.buy_threshold = max(35, self.buy_threshold - 1)

                if old_threshold != self.buy_threshold:
                    self.ai_log(f"Threshold↓ {old_threshold}→{self.buy_threshold}", "AI")

            elif win_rate + confidence_margin < 0.45:
                old_threshold = self.buy_threshold
                self.buy_threshold = min(70, self.buy_threshold + 1)

                if old_threshold != self.buy_threshold:
                    self.ai_log(f"Threshold↑ {old_threshold}→{self.buy_threshold}", "AI")

        except Exception as e:
            pass


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
        self.top_scores = []

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

        for _ in range(30):
            self.particles.append({
                'angle': np.random.random() * 2 * math.pi,
                'radius': 50 + np.random.random() * 150,
                'speed': 0.01 + np.random.random() * 0.02,
                'size': 2 + np.random.random() * 3
            })

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
            self.log_container.grid_columnconfigure(i, weight=1)
        self.log_container.grid_rowconfigure(1, weight=1)

        self.animate()

    def set_active(self, active):
        self.is_active = active

    def set_trading_state(self, state):
        self.trading_state = state

    def update_top_scores(self, scores):
        """Update top scores list"""
        self.top_scores = scores

    def animate(self):
        if not self.winfo_exists():
            return

        self.angle += 0.02
        self.pulse += 0.05

        self.canvas.delete("all")

        color = self.state_colors.get(self.trading_state, "#00ffff")

        self.draw_core(color)
        self.draw_particles(color)
        self.draw_status_text()
        self.draw_top_scores(self.top_scores)

        self.after(50, self.animate)

    def draw_core(self, color):
        pulse_size = 80 + 15 * math.sin(self.pulse)
        glow_size = pulse_size + 20

        glow_colors = {
            "#00ffff": "#006666",
            "#0099ff": "#004466",
            "#ff00ff": "#660066",
            "#00ff00": "#006600",
            "#ffff00": "#666600",
            "#ff0000": "#660000"
        }
        glow_color = glow_colors.get(color, "#333333")

        self.canvas.create_oval(
            self.center_x - glow_size, self.center_y - glow_size,
            self.center_x + glow_size, self.center_y + glow_size,
            fill="", outline=glow_color, width=2
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

    def draw_top_scores(self, top_scores):
        """Draw top coin scores"""
        if not top_scores:
            return

        start_x = self.center_x + 200
        start_y = self.center_y - 80

        self.canvas.create_text(
            start_x, start_y - 20,
            text="TOP SCORES",
            fill="#ffaa00", font=("Courier", 10, "bold"),
            anchor="w"
        )

        for i, (symbol, score) in enumerate(top_scores[:5]):
            y_pos = start_y + (i * 35)

            if score >= 60:
                score_color = "#00ff00"
                stars = "★★★"
            elif score >= 50:
                score_color = "#ffff00"
                stars = "★★"
            elif score >= 40:
                score_color = "#ff8800"
                stars = "★"
            else:
                score_color = "#888888"
                stars = ""

            coin_name = symbol.replace("_thb", "").replace("thb_", "").upper()
            self.canvas.create_text(
                start_x, y_pos,
                text=f"{i + 1}. {coin_name}",
                fill="#00ffff", font=("Courier", 9, "bold"),
                anchor="w"
            )

            self.canvas.create_text(
                start_x + 70, y_pos,
                text=f"{int(score)}",
                fill=score_color, font=("Courier", 10, "bold"),
                anchor="w"
            )

            if stars:
                self.canvas.create_text(
                    start_x + 100, y_pos,
                    text=stars,
                    fill=score_color, font=("Courier", 8),
                    anchor="w"
                )

    def add_ai_log(self, message, log_type="decision"):
        """Add message to specific column"""
        timestamp = datetime.now().strftime("%H:%M:%S")

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


class SeparateLogWindow(ctk.CTkToplevel):
    """✅ NEW: Separate Log Window - แยกหน้าต่าง Log ออกมาได้"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("📋 BLVCK TEA - Log Viewer")
        self.geometry("1400x800")
        
        # Header
        header = ctk.CTkFrame(self, height=50, fg_color="#1a1a1a")
        header.pack(fill="x", padx=10, pady=(10, 5))
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header,
            text="📋 COMPLETE LOG VIEWER - ทั้งหมด 6 ช่อง",
            font=("Arial", 18, "bold"),
            text_color="#00ffff"
        ).pack(side="left", padx=20)
        
        ctk.CTkButton(
            header,
            text="Clear All Logs",
            command=self.clear_all_logs,
            height=30,
            width=150,
            fg_color="#cc0000"
        ).pack(side="right", padx=10)
        
        # Main container
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=10, pady=5)
        
        # ========== TOP: AI LOGS (4 columns) ==========
        ai_log_frame = ctk.CTkFrame(main_container, fg_color="#0a0a0a")
        ai_log_frame.pack(fill="both", expand=True, pady=(0, 5))
        
        ctk.CTkLabel(
            ai_log_frame,
            text="🤖 AI DECISION LOGS (4 Columns)",
            font=("Arial", 13, "bold"),
            text_color="#00ffff"
        ).pack(pady=(5, 5))
        
        self.log_container = ctk.CTkFrame(ai_log_frame, fg_color="#0a0a0a")
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
                font=("Arial", 11, "bold"),
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
            self.log_container.grid_columnconfigure(i, weight=1)
        self.log_container.grid_rowconfigure(1, weight=1)
        
        # ========== BOTTOM: SYSTEM LOGS (2 columns) ==========
        system_log_frame = ctk.CTkFrame(main_container)
        system_log_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            system_log_frame,
            text="💻 SYSTEM LOGS (2 Columns)",
            font=("Arial", 13, "bold"),
            text_color="#00aaff"
        ).pack(pady=(5, 5))
        
        log_split = ctk.CTkFrame(system_log_frame)
        log_split.pack(fill="both", expand=True, padx=5, pady=(0, 10))
        
        # System Log (Left)
        sys_frame = ctk.CTkFrame(log_split)
        sys_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        ctk.CTkLabel(
            sys_frame,
            text="SYSTEM",
            font=("Arial", 10, "bold"),
            text_color="#00aaff"
        ).pack(pady=(0, 2))
        
        self.system_log = ctk.CTkTextbox(
            sys_frame,
            font=("Courier", 9, "bold"),
            fg_color="#0a0a0a",
            text_color="#ffffff",
            border_width=2,
            border_color="#00aaff"
        )
        self.system_log.pack(fill="both", expand=True)
        
        # Scan Detail Log (Right)
        scan_frame = ctk.CTkFrame(log_split)
        scan_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        ctk.CTkLabel(
            scan_frame,
            text="SCAN DETAIL",
            font=("Arial", 10, "bold"),
            text_color="#ffaa00"
        ).pack(pady=(0, 2))
        
        self.scan_log = ctk.CTkTextbox(
            scan_frame,
            font=("Courier", 9, "bold"),
            fg_color="#1a1000",
            text_color="#ffaa00",
            border_width=2,
            border_color="#ffaa00"
        )
        self.scan_log.pack(fill="both", expand=True)
        
        # Initialize logs
        self.system_log.insert("end", "=== SYSTEM LOG ===\n")
        self.system_log.insert("end", "Waiting for events...\n\n")
        
        self.scan_log.insert("end", "=== SCAN DETAIL LOG ===\n")
        self.scan_log.insert("end", "Waiting for scan data...\n\n")
    
    def add_ai_log(self, message, log_type="decision"):
        """Add message to AI log column"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        target_column = None
        for col_config in self.ai_log_displays:
            if col_config["type"] == log_type:
                target_column = col_config
                break
        
        if not target_column:
            target_column = self.ai_log_displays[2]  # default: decision
        
        widget = target_column["widget"]
        
        log_entry = f"[{timestamp}] {message}\n"
        widget.insert("end", log_entry)
        widget.see("end")
        
        lines = widget.get("1.0", "end").split("\n")
        if len(lines) > 200:
            widget.delete("1.0", "100.0")
    
    def add_system_log(self, message):
        """Add message to system log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.system_log.insert("end", f"[{timestamp}] {message}\n")
        self.system_log.see("end")
        
        lines = self.system_log.get("1.0", "end").split("\n")
        if len(lines) > 200:
            self.system_log.delete("1.0", "100.0")
    
    def add_scan_log(self, message):
        """Add message to scan log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.scan_log.insert("end", f"[{timestamp}] {message}\n")
        self.scan_log.see("end")
        
        lines = self.scan_log.get("1.0", "end").split("\n")
        if len(lines) > 200:
            self.scan_log.delete("1.0", "100.0")
    
    def clear_all_logs(self):
        """Clear all log displays"""
        for col in self.ai_log_displays:
            col["widget"].delete("1.0", "end")
            col["widget"].insert("end", f"=== {col['type'].upper()} LOG CLEARED ===\n\n")
        
        self.system_log.delete("1.0", "end")
        self.system_log.insert("end", "=== SYSTEM LOG CLEARED ===\n\n")
        
        self.scan_log.delete("1.0", "end")
        self.scan_log.insert("end", "=== SCAN LOG CLEARED ===\n\n")


class EnhancedTradingBot(ctk.CTk):
    """✅ COMPLETE: Enhanced Multi-Coin Trading Bot V3.9 with Charts"""

    def __init__(self):
        super().__init__()

        self.title("BLVCK TEA AiTrad V3.9 - COMPLETE")
        self.geometry("1600x950")

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

        # ✅ NEW: Chart data
        self.price_history = deque(maxlen=100)
        self.time_history = deque(maxlen=100)

        # ✅ NEW: Separate Log Window
        self.log_window = None

        self.setup_ui()
        
        # Start background updates
        threading.Thread(target=self.update_price_data_thread, daemon=True).start()

    def setup_ui(self):
        """Setup complete UI"""
        
        # Header
        header = ctk.CTkFrame(self, height=50, fg_color="#1a1a1a")
        header.pack(fill="x", padx=10, pady=(10, 5))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="🌑 BLVCK TEA AiTrad V3.9 - Complete Enhanced",
            font=("Arial", 20, "bold"),
            text_color="#00ffff"
        ).pack(expand=True)

        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=10, pady=5)

        # ========== LEFT PANEL ==========
        left_panel = ctk.CTkFrame(main_container)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 5))

        # ✅ NEW: Price Chart
        if MATPLOTLIB_AVAILABLE:
            chart_frame = ctk.CTkFrame(left_panel, fg_color="#0a0a0a")
            chart_frame.pack(fill="both", expand=True, padx=10, pady=5)

            ctk.CTkLabel(
                chart_frame,
                text="📈 REAL-TIME PRICE CHART",
                font=("Arial", 13, "bold"),
                text_color="#00ffff"
            ).pack(pady=(5, 0))

            self.fig = Figure(figsize=(9, 3.5), facecolor='#0a0a0a', dpi=80)
            self.ax = self.fig.add_subplot(111)
            self.ax.set_facecolor('#0a0a0a')
            self.ax.tick_params(colors='#00ffff', labelsize=8)
            self.ax.spines['bottom'].set_color('#00ffff')
            self.ax.spines['left'].set_color('#00ffff')
            self.ax.spines['top'].set_color('#0a0a0a')
            self.ax.spines['right'].set_color('#0a0a0a')

            self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
            self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
            
            self.update_chart()
        else:
            no_chart = ctk.CTkFrame(left_panel, fg_color="#1a0000")
            no_chart.pack(fill="both", expand=True, padx=10, pady=5)
            ctk.CTkLabel(
                no_chart,
                text="⚠️ Install matplotlib for charts\npip install matplotlib",
                font=("Arial", 12, "bold"),
                text_color="#ff0000",
                justify="center"
            ).pack(expand=True)

        # ✅ NEW: Position Display
        position_frame = ctk.CTkFrame(left_panel, fg_color="#001a1a", 
                                     border_width=2, border_color="#00ffff")
        position_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            position_frame,
            text="💼 CURRENT POSITION - REAL-TIME",
            font=("Arial", 12, "bold"),
            text_color="#00ffff"
        ).pack(pady=(5, 5))

        pos_grid = ctk.CTkFrame(position_frame, fg_color="transparent")
        pos_grid.pack(fill="x", padx=10, pady=5)

        self.pos_labels = {}
        
        # Row 1
        r1 = ctk.CTkFrame(pos_grid, fg_color="transparent")
        r1.pack(fill="x", pady=2)
        ctk.CTkLabel(r1, text="Symbol:", font=("Arial", 10), width=100, anchor="w").pack(side="left")
        self.pos_labels['symbol'] = ctk.CTkLabel(r1, text="None", font=("Arial", 11, "bold"), 
                                                  text_color="#888888", anchor="w")
        self.pos_labels['symbol'].pack(side="left", expand=True, fill="x", padx=5)
        
        ctk.CTkLabel(r1, text="Holding:", font=("Arial", 10), width=80, anchor="e").pack(side="left")
        self.pos_labels['amount'] = ctk.CTkLabel(r1, text="0.000000", font=("Arial", 10, "bold"),
                                                  text_color="#ffaa00", anchor="e", width=120)
        self.pos_labels['amount'].pack(side="left")

        # Row 2
        r2 = ctk.CTkFrame(pos_grid, fg_color="transparent")
        r2.pack(fill="x", pady=2)
        ctk.CTkLabel(r2, text="Entry Price:", font=("Arial", 10), width=100, anchor="w").pack(side="left")
        self.pos_labels['entry'] = ctk.CTkLabel(r2, text="0.00", font=("Arial", 10, "bold"),
                                                 text_color="#888888", anchor="w")
        self.pos_labels['entry'].pack(side="left", expand=True, fill="x", padx=5)
        
        ctk.CTkLabel(r2, text="Current:", font=("Arial", 10), width=80, anchor="e").pack(side="left")
        self.pos_labels['current'] = ctk.CTkLabel(r2, text="0.00", font=("Arial", 10, "bold"),
                                                   text_color="#00ffff", anchor="e", width=120)
        self.pos_labels['current'].pack(side="left")

        # Row 3
        r3 = ctk.CTkFrame(pos_grid, fg_color="transparent")
        r3.pack(fill="x", pady=2)
        ctk.CTkLabel(r3, text="Value:", font=("Arial", 10), width=100, anchor="w").pack(side="left")
        self.pos_labels['value'] = ctk.CTkLabel(r3, text="0.00 THB", font=("Arial", 10, "bold"),
                                                 text_color="#00ffff", anchor="w")
        self.pos_labels['value'].pack(side="left", expand=True, fill="x", padx=5)
        
        ctk.CTkLabel(r3, text="P/L:", font=("Arial", 10, "bold"), width=80, anchor="e").pack(side="left")
        self.pos_labels['pnl'] = ctk.CTkLabel(r3, text="0.00%", font=("Arial", 14, "bold"),
                                               text_color="#888888", anchor="e", width=120)
        self.pos_labels['pnl'].pack(side="left")

        # ✅ Visual Widget with AI Logs (4 columns) - ต้องอยู่ในหน้าหลัก
        ctk.CTkLabel(
            left_panel,
            text="🤖 AI MULTI-COIN DASHBOARD",
            font=("Arial", 13, "bold"),
            text_color="#00ffff"
        ).pack(pady=(5, 0))

        self.visual = EnhancedVisualWidget(left_panel, fg_color="#0a0a0a")
        self.visual.pack(fill="both", expand=True, padx=10, pady=5)

        # ✅ System Log + Scan Detail (2 columns) - ต้องอยู่ในหน้าหลัก
        sys_log_label = ctk.CTkLabel(
            left_panel,
            text="📋 SYSTEM LOG",
            font=("Arial", 11, "bold"),
            text_color="#00aaff"
        )
        sys_log_label.pack(pady=(5, 0))

        log_split = ctk.CTkFrame(left_panel)
        log_split.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        # ✅ CRITICAL: ต้องสร้าง log_display ในหน้าหลัก
        sys_frame = ctk.CTkFrame(log_split)
        sys_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        ctk.CTkLabel(
            sys_frame,
            text="SYSTEM",
            font=("Arial", 9, "bold"),
            text_color="#00aaff"
        ).pack(pady=(0, 2))

        self.log_display = ctk.CTkTextbox(
            sys_frame,
            font=("Courier", 9, "bold"),
            fg_color="#0a0a0a",
            text_color="#ffffff",
            height=150
        )
        self.log_display.pack(fill="both", expand=True)

        # ✅ CRITICAL: ต้องสร้าง scan_detail_display ในหน้าหลัก
        scan_frame = ctk.CTkFrame(log_split)
        scan_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        ctk.CTkLabel(
            scan_frame,
            text="SCAN DETAIL",
            font=("Arial", 9, "bold"),
            text_color="#ffaa00"
        ).pack(pady=(0, 2))

        self.scan_detail_display = ctk.CTkTextbox(
            scan_frame,
            font=("Courier", 9, "bold"),
            fg_color="#1a1000",
            text_color="#ffaa00",
            border_width=2,
            border_color="#ffaa00",
            height=150
        )
        self.scan_detail_display.pack(fill="both", expand=True)
        
        # Initialize with welcome message
        self.log_display.insert("end", "=== SYSTEM LOG ===\n")
        self.log_display.insert("end", "Bot initialized successfully\n")
        self.log_display.insert("end", "Waiting for API connection...\n\n")
        
        self.scan_detail_display.insert("end", "=== SCAN DETAIL LOG ===\n")
        self.scan_detail_display.insert("end", "Waiting for scan data...\n\n")

        # ========== RIGHT PANEL ==========
        right_panel_container = ctk.CTkFrame(main_container, width=500)
        right_panel_container.pack(side="right", fill="both", padx=(5, 0))
        right_panel_container.pack_propagate(False)

        self.scrollable_right = ctk.CTkScrollableFrame(right_panel_container)
        self.scrollable_right.pack(fill="both", expand=True)

        # API Frame
        api_frame = ctk.CTkFrame(self.scrollable_right)
        api_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(api_frame, text="API CREDENTIALS", font=("Arial", 12, "bold")).pack(pady=(5, 5))

        self.api_key_entry = ctk.CTkEntry(api_frame, width=460, height=32, placeholder_text="API Key", show="*")
        self.api_key_entry.pack(pady=2)

        self.api_secret_entry = ctk.CTkEntry(api_frame, width=460, height=32, placeholder_text="API Secret", show="*")
        self.api_secret_entry.pack(pady=2)

        ctk.CTkButton(
            api_frame,
            text="CONNECT API",
            command=self.connect_api,
            height=30,
            width=460
        ).pack(pady=3)

        # Amount Section
        amount_section = ctk.CTkFrame(api_frame, fg_color="#001a1a", border_width=1, border_color="#00ffff")
        amount_section.pack(fill="x", pady=5)

        ctk.CTkLabel(
            amount_section,
            text="TRADE AMOUNT",
            font=("Arial", 11, "bold"),
            text_color="#00ffff"
        ).pack(pady=(5, 2))

        amount_input_frame = ctk.CTkFrame(amount_section, fg_color="transparent")
        amount_input_frame.pack(fill="x", padx=10, pady=5)

        self.amount_entry = ctk.CTkEntry(
            amount_input_frame,
            width=320,
            height=32,
            placeholder_text="Enter amount (THB)",
            font=("Arial", 12)
        )
        self.amount_entry.insert(0, "500")
        self.amount_entry.pack(side="left", padx=(0, 5))

        self.amount_confirm_btn = ctk.CTkButton(
            amount_input_frame,
            text="Set",
            command=self.confirm_trade_amount,
            height=32,
            width=120,
            fg_color="#00aa00",
            font=("Arial", 11, "bold")
        )
        self.amount_confirm_btn.pack(side="left")

        self.amount_status_label = ctk.CTkLabel(
            amount_section,
            text="Current: 500 THB",
            font=("Arial", 10),
            text_color="#00ff00"
        )
        self.amount_status_label.pack(pady=(0, 5))

        # Strategy Frame
        strategy_frame = ctk.CTkFrame(self.scrollable_right, fg_color="#001a1a", border_width=2, border_color="#00ffff")
        strategy_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(strategy_frame, text="STRATEGY SETTINGS", font=("Arial", 12, "bold"), text_color="#00ffff").pack(pady=(5, 5))

        data_points_frame = ctk.CTkFrame(strategy_frame, fg_color="transparent")
        data_points_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(data_points_frame, text="Data Points:", font=("Arial", 10, "bold")).pack(side="left", padx=2)
        ctk.CTkLabel(data_points_frame, text="Min:", font=("Arial", 9)).pack(side="left", padx=2)
        self.data_points_entry = ctk.CTkEntry(data_points_frame, width=50, height=25)
        self.data_points_entry.insert(0, "1000")
        self.data_points_entry.pack(side="left", padx=2)

        ctk.CTkLabel(data_points_frame, text="Max:", font=("Arial", 9)).pack(side="left", padx=2)
        self.max_data_points_entry = ctk.CTkEntry(data_points_frame, width=50, height=25)
        self.max_data_points_entry.insert(0, "200000")
        self.max_data_points_entry.pack(side="left", padx=2)

        ctk.CTkLabel(data_points_frame, text="points", font=("Arial", 9)).pack(side="left", padx=2)

        exp_frame = ctk.CTkFrame(strategy_frame, fg_color="#001a1a", border_width=2, border_color="#00ffff")
        exp_frame.pack(fill="x", padx=10, pady=5)

        # ✅ IMPROVED: Header with icon
        ctk.CTkLabel(
            exp_frame,
            text="📚 EXPERIENCE DATA",
            font=("Arial", 11, "bold"),
            text_color="#00ffff"
        ).pack(pady=(5, 2))

        # ✅ IMPROVED: Large display
        self.exp_label = ctk.CTkLabel(
            exp_frame,
            text="Exp: 0 pts | 0 coins",
            font=("Arial", 13, "bold"),
            text_color="#00ff00",
            fg_color="#002200",
            corner_radius=8,
            height=40
        )
        self.exp_label.pack(pady=5, padx=10, fill="x")

        # ✅ IMPROVED: Add detail labels
        self.exp_detail_frame = ctk.CTkFrame(exp_frame, fg_color="transparent")
        self.exp_detail_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        self.exp_detail_left = ctk.CTkLabel(
            self.exp_detail_frame,
            text="Ready: 0 coins",
            font=("Arial", 9),
            text_color="#00aaff"
        )
        self.exp_detail_left.pack(side="left", padx=5)
        
        self.exp_detail_right = ctk.CTkLabel(
            self.exp_detail_frame,
            text="Trades: 0",
            font=("Arial", 9),
            text_color="#ffaa00"
        )
        self.exp_detail_right.pack(side="right", padx=5)

        exp_buttons = ctk.CTkFrame(strategy_frame, fg_color="transparent")
        exp_buttons.pack(fill="x", padx=10, pady=2)

        ctk.CTkButton(
            exp_buttons,
            text="Save",
            command=self.manual_save_experience,
            height=22,
            width=145,
            font=("Arial", 8),
            fg_color="#0066cc"
        ).pack(side="left", padx=1)

        ctk.CTkButton(
            exp_buttons,
            text="Load",
            command=self.manual_load_experience,
            height=22,
            width=145,
            font=("Arial", 8),
            fg_color="#006600"
        ).pack(side="left", padx=1)

        ctk.CTkButton(
            exp_buttons,
            text="Clear",
            command=self.clear_experience,
            height=22,
            width=145,
            font=("Arial", 8),
            fg_color="#cc0000"
        ).pack(side="left", padx=1)

        self.strategy_mode = ctk.StringVar(value="full_auto")

        strategy_radio_frame = ctk.CTkFrame(strategy_frame, fg_color="transparent")
        strategy_radio_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkRadioButton(
            strategy_radio_frame,
            text="Full Auto AI",
            variable=self.strategy_mode,
            value="full_auto",
            font=("Arial", 10)
        ).pack(anchor="w", pady=2)

        ctk.CTkRadioButton(
            strategy_radio_frame,
            text="Manual Settings",
            variable=self.strategy_mode,
            value="manual",
            font=("Arial", 10)
        ).pack(anchor="w", pady=2)

        self.manual_settings_frame = ctk.CTkFrame(strategy_frame, fg_color="#002222")
        self.manual_settings_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(self.manual_settings_frame, text="Buy Threshold:", font=("Arial", 9)).pack(anchor="w", padx=5)
        self.buy_threshold_slider = ctk.CTkSlider(self.manual_settings_frame, from_=30, to=80, number_of_steps=50)
        self.buy_threshold_slider.set(45)
        self.buy_threshold_slider.pack(fill="x", padx=5, pady=2)

        ctk.CTkLabel(self.manual_settings_frame, text="Take Profit (%):", font=("Arial", 9)).pack(anchor="w", padx=5)
        self.tp_slider = ctk.CTkSlider(self.manual_settings_frame, from_=1, to=10, number_of_steps=90)
        self.tp_slider.set(2.5)
        self.tp_slider.pack(fill="x", padx=5, pady=2)

        ctk.CTkLabel(self.manual_settings_frame, text="Stop Loss (%):", font=("Arial", 9)).pack(anchor="w", padx=5)
        self.sl_slider = ctk.CTkSlider(self.manual_settings_frame, from_=1, to=5, number_of_steps=40)
        self.sl_slider.set(2.0)
        self.sl_slider.pack(fill="x", padx=5, pady=2)

        ctk.CTkButton(
            strategy_frame,
            text="Apply Settings",
            command=self.apply_strategy_settings,
            height=28,
            fg_color="#00aa00"
        ).pack(fill="x", padx=10, pady=5)

        # Status Frame
        status_frame = ctk.CTkFrame(self.scrollable_right)
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

        # Control Frame
        control_frame = ctk.CTkFrame(self.scrollable_right)
        control_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(control_frame, text="CONTROLS", font=("Arial", 12, "bold")).pack(pady=(5, 5))

        mode_switch_frame = ctk.CTkFrame(control_frame, fg_color="#1a0000", border_width=2, border_color="#ff0000")
        mode_switch_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(
            mode_switch_frame,
            text="TRADING MODE SELECTION",
            font=("Arial", 11, "bold"),
            text_color="#ff0000"
        ).pack(pady=5)

        self.paper_trading_var = ctk.BooleanVar(value=True)
        self.paper_trading_switch = ctk.CTkSwitch(
            mode_switch_frame,
            text="Paper Trading Mode (SAFE)",
            variable=self.paper_trading_var,
            command=self.toggle_paper_trading
        )
        self.paper_trading_switch.pack(anchor="w", padx=10, pady=3)

        self.real_trading_var = ctk.BooleanVar(value=False)
        self.real_trading_switch = ctk.CTkSwitch(
            mode_switch_frame,
            text="REAL TRADING (DANGER!)",
            variable=self.real_trading_var,
            command=self.toggle_real_trading,
            button_color="red",
            progress_color="darkred"
        )
        self.real_trading_switch.pack(anchor="w", padx=10, pady=3)

        self.trading_mode_label = ctk.CTkLabel(
            mode_switch_frame,
            text="PAPER TRADING MODE ACTIVE (SAFE)",
            font=("Arial", 10, "bold"),
            text_color="green"
        )
        self.trading_mode_label.pack(pady=5)

        self.start_button = ctk.CTkButton(
            control_frame,
            text="START PAPER TRADING",
            command=self.toggle_trading,
            height=40,
            font=("Arial", 13, "bold"),
            fg_color="#00aa00"
        )
        self.start_button.pack(pady=5, padx=10, fill="x")

        btn_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            btn_frame,
            text="TEST API",
            command=self.test_api_only,
            height=28,
            width=140,
            fg_color="#0066cc"
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            btn_frame,
            text="TEST SCAN",
            command=self.test_scan_small,
            height=28,
            width=140,
            fg_color="#9900cc"
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            btn_frame,
            text="CLEAR CHART",
            command=self.clear_chart,
            height=28,
            width=140,
            fg_color="#cc6600"
        ).pack(side="left", padx=2)

        # ✅ NEW: Open Log Window Button
        ctk.CTkButton(
            control_frame,
            text="📋 OPEN LOG VIEWER",
            command=self.open_log_window,
            height=35,
            font=("Arial", 12, "bold"),
            fg_color="#0066cc"
        ).pack(pady=5, padx=10, fill="x")

        self.after(1000, self.update_status)

    def confirm_trade_amount(self):
        """Confirm and set trade amount"""
        try:
            amount_text = self.amount_entry.get().strip()
            if not amount_text:
                self.ai_log("Please enter amount", "SYSTEM")
                return

            amount = float(amount_text)

            if amount < 10:
                self.ai_log("Minimum: 10 THB", "SYSTEM")
                messagebox.showwarning("Invalid Amount", "Minimum trade amount is 10 THB")
                return

            max_limit = 10000 if self.is_paper_trading else 5000
            if amount > max_limit:
                self.ai_log(f"Maximum: {max_limit} THB", "SYSTEM")
                messagebox.showwarning("Invalid Amount", f"Maximum trade amount is {max_limit} THB")
                return

            self.trade_amount_thb = amount

            self.amount_status_label.configure(
                text=f"Current: {amount:,.0f} THB",
                text_color="#00ff00"
            )

            self.ai_log(f"Trade amount set: {amount:,.0f} THB", "SYSTEM")

            self.amount_confirm_btn.configure(text="Set!", fg_color="#00ff00")
            self.after(1000, lambda: self.amount_confirm_btn.configure(text="Set", fg_color="#00aa00"))

        except ValueError:
            self.ai_log("Invalid number format", "SYSTEM")
            messagebox.showerror("Invalid Input", "Please enter a valid number")

    def ai_log(self, message, log_type="AI"):
        """✅ FIXED: Unified logging - แสดงทั้งหน้าหลัก + Log Window"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # ✅ SCAN DETAIL LOG
        if log_type == "SCAN":
            # Main window
            try:
                if hasattr(self, 'scan_detail_display'):
                    self.scan_detail_display.insert("end", f"[{timestamp}] {message}\n")
                    self.scan_detail_display.see("end")
                    lines = self.scan_detail_display.get("1.0", "end").split("\n")
                    if len(lines) > 100:
                        self.scan_detail_display.delete("1.0", "50.0")
            except:
                pass
            
            # Log window
            if self.log_window and self.log_window.winfo_exists():
                self.log_window.add_scan_log(message)
            
            return

        # ✅ SYSTEM LOG
        if log_type == "SYSTEM":
            # Main window
            try:
                if hasattr(self, 'log_display'):
                    self.log_display.insert("end", f"[{timestamp}] {message}\n")
                    self.log_display.see("end")
                    lines = self.log_display.get("1.0", "end").split("\n")
                    if len(lines) > 100:
                        self.log_display.delete("1.0", "50.0")
            except:
                pass
            
            # Log window
            if self.log_window and self.log_window.winfo_exists():
                self.log_window.add_system_log(message)
            
            return

        # ✅ ERROR LOG
        if log_type == "ERROR":
            # Main window
            try:
                if hasattr(self, 'log_display'):
                    self.log_display.insert("end", f"[{timestamp}] ❌ {message}\n")
                    self.log_display.see("end")
            except:
                pass
            
            # Log window
            if self.log_window and self.log_window.winfo_exists():
                self.log_window.add_system_log(f"❌ {message}")
                self.log_window.add_ai_log(f"❌ {message}", "trade")
            
            # Visual widget
            if hasattr(self, 'visual'):
                self.visual.add_ai_log(f"❌ {message}", "trade")
            
            return

        # ✅ AI LOGS (4 columns)
        if log_type == "AI":
            column_type = "decision"

            # Smart routing
            if any(keyword in message for keyword in 
                   ["Price", "Break-even", "Amount:", "Volume", "collected", "data points", 
                    "THB", "Entry:", "Exit:", "Balance", "Fee", "Value"]):
                column_type = "market"
                
            elif any(keyword in message for keyword in 
                     ["RSI", "Volatility", "Score", "Ratio", "trend", "oversold", "overbought", 
                      "WR:", "Avg:", "trades", "⭐", "#", "momentum", "MA"]):
                column_type = "indicators"
                
            elif any(keyword in message for keyword in 
                     ["ANALYZING", "SIGNAL", "Strategy", "HOLDING", "tradeable", "Best", 
                      "strong", "Scanning", "Filter", "Ready", "Threshold"]):
                column_type = "decision"
                
            elif any(keyword in message for keyword in 
                     ["BUY", "SELL", "PROFIT", "LOSS", "Order", "Position", "EXECUTION", 
                      "FAILED", "opened", "closed", "Learned", "executed"]):
                column_type = "trade"

            # Visual widget (main window)
            if hasattr(self, 'visual'):
                self.visual.add_ai_log(message, column_type)
            
            # Log window
            if self.log_window and self.log_window.winfo_exists():
                self.log_window.add_ai_log(message, column_type)
                
            # Important messages → System log too
            if any(keyword in message.upper() for keyword in 
                   ["BUY", "SELL", "ERROR", "FAIL", "POSITION", "EXECUTED"]):
                try:
                    if hasattr(self, 'log_display'):
                        self.log_display.insert("end", f"[{timestamp}] {message}\n")
                        self.log_display.see("end")
                except:
                    pass
                
                if self.log_window and self.log_window.winfo_exists():
                    self.log_window.add_system_log(message)
            
            return

        # ✅ Fallback
        try:
            if hasattr(self, 'log_display'):
                self.log_display.insert("end", f"[{timestamp}] {message}\n")
                self.log_display.see("end")
        except:
            pass
        
        if self.log_window and self.log_window.winfo_exists():
            self.log_window.add_system_log(message)

    def open_log_window(self):
        """✅ NEW: Open separate log viewer window"""
        if self.log_window is None or not self.log_window.winfo_exists():
            self.log_window = SeparateLogWindow(self)
            self.ai_log("📋 Log Viewer opened", "SYSTEM")
        else:
            self.log_window.focus()
            self.log_window.lift()

    def update_visual_scores(self, top_scores):
        """Update visual widget with top scores"""
        if self.visual:
            self.visual.update_top_scores(top_scores)

    def connect_api(self):
        """Connect API with testing"""
        api_key = self.api_key_entry.get().strip()
        api_secret = self.api_secret_entry.get().strip()

        if not api_key or not api_secret:
            self.ai_log("Enter API credentials", "SYSTEM")
            return

        self.api_client = FixedBitkubAPI(api_key, api_secret)
        success, message = self.api_client.test_api_connection()

        if success:
            self.ai_log(f"{message}", "SYSTEM")
            self.ai_log("Initializing strategy...", "SCAN")

            self.strategy = AdvancedMultiCoinStrategy(self.api_client, log_callback=self.ai_log)
            self.update_experience_display()

            self.ai_log(f"Ready to trade {len(self.api_client.all_bitkub_symbols)} symbols", "SYSTEM")
        else:
            self.ai_log(f"Connection failed: {message}", "SYSTEM")
            messagebox.showerror("Connection Failed", message)

    def test_api_only(self):
        """Test API connection only"""
        if not self.api_client:
            self.ai_log("Connect API first", "SYSTEM")
            return

        self.ai_log("Testing API connection...", "SYSTEM")
        success, message = self.api_client.test_api_connection()

        if success:
            self.ai_log(f"{message}", "SYSTEM")
        else:
            self.ai_log(f"{message}", "SYSTEM")

    def test_scan_small(self):
        """Test scanning a few coins"""
        if not self.strategy:
            self.ai_log("Connect API first", "SYSTEM")
            return

        self.ai_log("Testing scan (5 coins)...", "SYSTEM")

        test_symbols = self.api_client.all_bitkub_symbols[:5]
        collected = self.strategy.collect_market_data(test_symbols)

        self.ai_log(f"Scanned {collected}/5 coins", "SYSTEM")

    def apply_strategy_settings(self):
        """Apply strategy settings"""
        if self.strategy_mode.get() == "manual":
            buy_threshold = int(self.buy_threshold_slider.get())
            take_profit = self.tp_slider.get() / 100
            stop_loss = self.sl_slider.get() / 100

            if self.strategy:
                self.strategy.buy_threshold = buy_threshold
                self.strategy.take_profit = take_profit
                self.strategy.stop_loss = -stop_loss

                self.ai_log(f"Manual Settings Applied", "SYSTEM")
        else:
            self.ai_log("Full Auto AI Mode Active", "SYSTEM")

        try:
            min_points = int(self.data_points_entry.get())
            max_points = int(self.max_data_points_entry.get())

            if min_points < 10:
                min_points = 10
            if max_points < min_points:
                max_points = min_points * 2

            if self.strategy:
                self.strategy.min_data_points = min_points
                self.strategy.max_data_points = max_points
                self.ai_log(f"Data: Min={min_points}, Max={max_points}", "SYSTEM")
        except:
            self.ai_log("Invalid data points value", "SYSTEM")

    def update_experience_display(self):
        """✅ IMPROVED: Update experience display with details"""
        if not self.strategy:
            return

        total_points = sum(len(data['prices']) for data in self.strategy.coin_data.values())
        coins_count = len(self.strategy.coin_data)
        ready_count = sum(1 for data in self.strategy.coin_data.values() if data.get('data_ready', False))
        trades_count = len(self.strategy.trade_history)

        # ✅ Format large numbers
        if total_points >= 1000000:
            exp_text = f"{total_points / 1000000:.1f}M"
        elif total_points >= 1000:
            exp_text = f"{total_points / 1000:.1f}k"
        else:
            exp_text = str(total_points)

        # ✅ Update main label with color coding
        if total_points >= 10000:
            bg_color = "#002200"
            text_color = "#00ff00"
            status = "🔥"
        elif total_points >= 1000:
            bg_color = "#222200"
            text_color = "#ffff00"
            status = "⚡"
        else:
            bg_color = "#222222"
            text_color = "#888888"
            status = "📊"

        self.exp_label.configure(
            text=f"{status} Exp: {exp_text} pts | {coins_count} coins",
            text_color=text_color,
            fg_color=bg_color
        )
        
        # ✅ Update detail labels
        if hasattr(self, 'exp_detail_left'):
            self.exp_detail_left.configure(text=f"Ready: {ready_count}/{coins_count} coins")
        
        if hasattr(self, 'exp_detail_right'):
            self.exp_detail_right.configure(text=f"Trades: {trades_count}")

    def toggle_paper_trading(self):
        """Toggle paper trading mode"""
        self.is_paper_trading = self.paper_trading_var.get()

        if self.is_paper_trading:
            self.real_trading_var.set(False)
            self.trading_mode_label.configure(text="PAPER TRADING MODE ACTIVE (SAFE)", text_color="green")
            self.start_button.configure(text="START PAPER TRADING", fg_color="#00aa00")
            self.status_labels["Mode"].configure(text="Paper", text_color="#ff8800")
            self.ai_log(f"Switched to Paper mode", "SYSTEM")

    def toggle_real_trading(self):
        """Toggle real trading mode"""
        switch_is_on = self.real_trading_var.get()
        self.is_paper_trading = not switch_is_on

        if switch_is_on:
            warning = messagebox.askyesno(
                "REAL TRADING WARNING",
                "You are about to enable REAL TRADING!\n\n"
                "The system will use REAL MONEY\n"
                "You may lose everything\n\n"
                "Confirm REAL TRADING activation?"
            )

            if not warning:
                self.real_trading_var.set(False)
                self.is_paper_trading = True
                self.ai_log("Cancelled - Staying in Paper mode", "SYSTEM")
                return

            if self.api_client:
                balance = self.api_client.check_balance()
                if balance and balance.get('error') == 0:
                    try:
                        thb_data = balance['result'].get('THB', {})
                        if isinstance(thb_data, dict):
                            self.current_balance = float(thb_data.get('available', 0))
                        else:
                            self.current_balance = float(thb_data)

                        self.ai_log(f"Real Balance: {self.current_balance:,.2f} THB", "SYSTEM")
                    except:
                        self.ai_log("Could not get balance", "SYSTEM")

            self.trading_mode_label.configure(text="REAL TRADING MODE ACTIVE (DANGER!)", text_color="red")
            self.start_button.configure(text="START REAL TRADING", fg_color="#ff0000")
            self.status_labels["Mode"].configure(text="REAL", text_color="#ff0000")
            self.ai_log("REAL TRADING MODE ACTIVATED", "SYSTEM")

        else:
            self.trading_mode_label.configure(text="PAPER TRADING MODE ACTIVE (SAFE)", text_color="green")
            self.start_button.configure(text="START PAPER TRADING", fg_color="#00aa00")
            self.status_labels["Mode"].configure(text="Paper", text_color="#ff8800")
            self.ai_log(f"Switched to Paper mode", "SYSTEM")

    def toggle_trading(self):
        """Toggle trading on/off"""
        if not self.strategy:
            self.ai_log("Connect API first", "SYSTEM")
            return

        self.is_trading = not self.is_trading

        if self.is_trading:
            if not self.is_paper_trading:
                final_warning = messagebox.askyesno(
                    "REAL TRADING WARNING",
                    "Starting REAL TRADING with REAL MONEY!\n\n"
                    "This bot will place REAL orders\n\n"
                    "Confirm?"
                )

                if not final_warning:
                    self.is_trading = False
                    self.ai_log("Trading cancelled", "SYSTEM")
                    return

            self.start_button.configure(text="STOP TRADING", fg_color="#ff0000")
            self.visual.set_active(True)

            if self.is_paper_trading:
                self.ai_log("Trading started (Paper Mode)", "SYSTEM")
            else:
                self.ai_log("REAL TRADING STARTED", "SYSTEM")

            threading.Thread(target=self.trading_loop, daemon=True).start()
        else:
            self.start_button.configure(text="START TRADING", fg_color="#00aa00")
            self.visual.set_active(False)
            self.ai_log("Stopped", "SYSTEM")

    def trading_loop(self):
        """Main trading loop"""
        ready_coins = sum(1 for data in self.strategy.coin_data.values() if data.get('data_ready', False))

        if ready_coins >= 10:
            self.ai_log(f"Using historical data: {ready_coins} coins ready!", "SYSTEM")
            warmup_count = self.strategy.min_data_points
        else:
            self.ai_log("Collecting fresh market data...", "SYSTEM")
            warmup_count = 0

        required_warmup = self.strategy.min_data_points
        symbols = self.api_client.all_bitkub_symbols

        while self.is_trading:
            try:
                self.ai_log(f"=== LOOP START ===", "SCAN")

                try:
                    amount_text = self.amount_entry.get().strip()
                    if not amount_text:
                        self.trade_amount_thb = 500.0
                    else:
                        self.trade_amount_thb = float(amount_text)
                except:
                    self.trade_amount_thb = 500.0

                self.visual.set_trading_state("SCANNING")
                collected = self.strategy.collect_market_data(symbols)

                ready_coins_now = sum(1 for data in self.strategy.coin_data.values() if data.get('data_ready', False))

                if warmup_count < required_warmup and ready_coins_now < 10:
                    warmup_count += 1
                    if warmup_count % 10 == 0:
                        self.ai_log(f"Collecting data: {warmup_count}/{required_warmup}", "SYSTEM")
                    time.sleep(10)
                    continue

                if warmup_count == required_warmup or (warmup_count < required_warmup and ready_coins_now >= 10):
                    self.ai_log("Data collection complete", "SYSTEM")
                    warmup_count = required_warmup + 1

                if self.strategy.position is None:
                    self.visual.set_trading_state("ANALYZING")

                    tradeable = self.strategy.filter_tradeable_coins()

                    if not tradeable:
                        self.ai_log("No tradeable coins found", "AI")
                        time.sleep(10)
                        continue

                    best_coin, score, reason = self.strategy.find_best_coin_to_buy(tradeable)

                    if best_coin:
                        ticker = self.api_client.get_simple_ticker(best_coin)
                        if ticker:
                            self.execute_buy(best_coin, ticker, reason, score)
                    else:
                        self.ai_log(reason, "AI")

                else:
                    pos_symbol = self.strategy.position['symbol']
                    ticker = self.api_client.get_simple_ticker(pos_symbol)

                    if ticker:
                        should_sell, reason = self.strategy.should_sell_profitable(
                            ticker['last_price'],
                            ticker['volume_24h']
                        )

                        if should_sell:
                            self.execute_sell(pos_symbol, ticker, reason)
                        else:
                            self.visual.set_trading_state("HOLDING")

                time.sleep(10)

            except Exception as e:
                self.ai_log(f"Error: {str(e)[:30]}", "AI")
                time.sleep(10)

        self.ai_log("Trading stopped", "SYSTEM")
        self.visual.set_trading_state("IDLE")

    def execute_buy(self, symbol, ticker, reason, score):
        """✅ COMPLETE: Execute buy with all required fields"""
        try:
            is_valid, verified_symbol = self.api_client.verify_symbol(symbol)
            if not is_valid:
                self.ai_log(f"Invalid symbol: {symbol}", "ERROR")
                return

            symbol = verified_symbol
            price = ticker['last_price']

            if price <= 0:
                self.ai_log(f"Invalid price", "ERROR")
                return

            amount_thb = self.trade_amount_thb

            if self.is_paper_trading:
                if self.paper_balance < amount_thb:
                    self.ai_log(f"Insufficient balance", "AI")
                    return

            # Calculate fees
            fee_rate = self.api_client.trading_fees['taker_fee']
            net_thb = amount_thb * (1 - fee_rate)
            amount = net_thb / price
            buy_fee = amount_thb * fee_rate

            self.visual.set_trading_state("BUYING")

            coin_name = symbol.split('_')[0].upper()
            self.ai_log(f"BUY {coin_name}: Score={score}", "AI")
            self.ai_log(f"Price: {price:.0f} THB", "AI")
            self.ai_log(f"Amount: {amount_thb:.0f} THB", "AI")

            break_even = self.api_client.calculate_break_even_price(price, "buy")
            self.ai_log(f"Break-even: {break_even:.0f}", "AI")

            # ✅ FIXED: Create position with ALL required fields
            self.strategy.position = {
                'symbol': symbol,
                'entry_price': price,
                'amount': amount,
                'buy_fee': buy_fee,
                'pending': True,
                'entry_score': score,
                'entry_time': datetime.now()  # ✅ CRITICAL: ต้องมี!
            }

            if self.is_paper_trading:
                self.ai_log(f"PAPER MODE", "AI")
                self.paper_balance -= amount_thb
                self.strategy.position['pending'] = False
            else:
                self.ai_log(f"REAL MODE - Sending order...", "AI")
                buy_price = round(price * 1.002, 8)

                result = self.api_client.place_buy_order_safe(symbol, amount_thb, buy_price, 'limit')

                if result.get('error') != 0:
                    error_code = result.get('error')
                    error_msg = self.api_client.error_codes.get(error_code, 'Unknown')
                    
                    self.ai_log(f"BUY FAILED: {error_msg}", "ERROR")
                    self.strategy.record_symbol_error(symbol)
                    self.strategy.position = None
                    return
                else:
                    order_id = result.get('result', {}).get('id', 'N/A')
                    self.ai_log(f"Order ID: {order_id}", "AI")
                    self.strategy.position['pending'] = False
                    self.strategy.position['order_id'] = order_id
                    
                    # ✅ Get actual balance from Bitkub
                    time.sleep(2)
                    balance_result = self.api_client.check_balance()
                    if balance_result and balance_result.get('error') == 0:
                        coin_key = symbol.split('_')[0].upper()
                        coin_balance = balance_result['result'].get(coin_key, {})
                        
                        if isinstance(coin_balance, dict):
                            actual_amount = float(coin_balance.get('available', 0))
                        else:
                            actual_amount = float(coin_balance)
                        
                        if actual_amount > 0:
                            self.strategy.position['amount'] = actual_amount
                            self.ai_log(f"Actual: {actual_amount:.8f}", "AI")
                    
                    self.current_balance -= amount_thb

            self.trade_count += 1
            self.ai_log("Position opened!", "AI")
            self.visual.set_trading_state("HOLDING")

        except Exception as e:
            self.ai_log(f"BUY ERROR: {str(e)[:30]}", "ERROR")
            self.strategy.position = None

    def execute_sell(self, symbol, ticker, reason):
        """✅ COMPLETE: Execute sell with balance verification"""
        try:
            is_valid, verified_symbol = self.api_client.verify_symbol(symbol)
            if not is_valid:
                self.ai_log(f"Invalid symbol: {symbol}", "ERROR")
                return

            symbol = verified_symbol
            price = ticker['last_price']

            if price <= 0:
                self.ai_log(f"Invalid price", "ERROR")
                return

            position = self.strategy.position
            if not position:
                self.ai_log(f"No position to sell", "ERROR")
                return
                
            amount = position['amount']
            entry_score = position.get('entry_score', 0)

            self.visual.set_trading_state("SELLING")

            entry_price = position['entry_price']
            buy_fee = position.get('buy_fee', 0)
            sell_fee = self.api_client.calculate_trading_fees(amount, price, "sell")

            gross_pnl = (price - entry_price) * amount
            net_pnl = gross_pnl - buy_fee - sell_fee
            profit_pct = net_pnl / (entry_price * amount) * 100

            self.ai_log(f"SELL: {reason[:20]}", "AI")
            self.ai_log(f"Entry: {entry_price:,.0f} THB", "AI")
            self.ai_log(f"Exit: {price:,.0f} THB", "AI")
            self.ai_log(f"P/L: {net_pnl:+.2f} THB ({profit_pct:+.2f}%)", "AI")

            if self.is_paper_trading:
                self.ai_log(f"PAPER MODE", "AI")
                proceeds = amount * price
                self.paper_balance += proceeds
            else:
                self.ai_log(f"REAL MODE - Sending order...", "AI")

                # ✅ SAFETY: Get actual balance before selling
                balance_result = self.api_client.check_balance()
                if balance_result and balance_result.get('error') == 0:
                    coin_key = symbol.split('_')[0].upper()
                    coin_balance = balance_result['result'].get(coin_key, {})

                    if isinstance(coin_balance, dict):
                        actual_available = float(coin_balance.get('available', 0))
                    else:
                        actual_available = float(coin_balance)

                    if actual_available > 0:
                        if actual_available < amount:
                            self.ai_log(f"Adjust sell: {amount:.8f} → {actual_available:.8f}", "AI")
                            amount = actual_available
                    else:
                        self.ai_log(f"No balance to sell!", "ERROR")
                        return

                sell_price = round(price * 0.998, 8)

                result = self.api_client.place_sell_order_safe(symbol, amount, sell_price, 'limit')

                if result.get('error') != 0:
                    error_code = result.get('error', 999)
                    error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")

                    self.ai_log(f"SELL FAILED: {error_msg}", "ERROR")
                    self.strategy.record_symbol_error(symbol)
                    return
                else:
                    order_id = result.get('result', {}).get('id', 'N/A')
                    self.ai_log(f"Sell Order ID: {order_id}", "AI")
                    proceeds = amount * price
                    self.current_balance += proceeds

            self.total_pnl += net_pnl

            if net_pnl > 0:
                self.win_count += 1
                self.visual.set_trading_state("PROFIT")
            else:
                self.visual.set_trading_state("LOSS")

            if self.strategy:
                self.strategy.learn_from_trade(symbol, entry_score, profit_pct)

            self.ai_log("Position closed!", "AI")
            self.strategy.position = None

            time.sleep(1)
            self.visual.set_trading_state("IDLE")

        except Exception as e:
            self.ai_log(f"SELL ERROR: {str(e)[:30]}", "ERROR")
            import traceback
            traceback.print_exc()

    def update_visual_scores(self, top_scores):
        """✅ NEW: Update visual widget with top scores"""
        if hasattr(self, 'visual') and self.visual:
            self.visual.update_top_scores(top_scores)

    def update_price_data_thread(self):
        """✅ FIXED: Background thread to update price data"""
        while True:
            try:
                # ✅ FIXED: Check self.strategy not strategy
                if self.api_client and self.strategy and self.strategy.position:
                    symbol = self.strategy.position['symbol']
                    ticker = self.api_client.get_simple_ticker(symbol)
                    
                    if ticker and ticker['last_price'] > 0:
                        price = ticker['last_price']
                        self.price_history.append(price)
                        self.time_history.append(datetime.now())
                
                time.sleep(3)
            except Exception as e:
                # Silent fail - don't spam logs
                time.sleep(5)

    def update_chart(self):
        """Update matplotlib chart"""
        if not MATPLOTLIB_AVAILABLE:
            return

        try:
            self.ax.clear()
            
            if len(self.price_history) > 1:
                times = list(range(len(self.price_history)))
                prices = list(self.price_history)
                
                self.ax.plot(times, prices, color='#00ffff', linewidth=2, marker='o', markersize=3, label='Price')
                
                if self.strategy and self.strategy.position:
                    entry = self.strategy.position['entry_price']
                    self.ax.axhline(y=entry, color='#ffaa00', linestyle='--', linewidth=1.5, label='Entry')
                    
                    if len(prices) > 0:
                        current = prices[-1]
                        color = '#00ff00' if current > entry else '#ff0000'
                        self.ax.axhline(y=current, color=color, linestyle=':', linewidth=1, alpha=0.7, label='Current')
                
                self.ax.set_xlabel('Time', color='#00ffff', fontsize=9)
                self.ax.set_ylabel('Price (THB)', color='#00ffff', fontsize=9)
                self.ax.legend(loc='upper left', facecolor='#0a0a0a', edgecolor='#00ffff', labelcolor='#00ffff', fontsize=8)
                self.ax.grid(True, alpha=0.15, color='#00ffff', linestyle=':')
                
            else:
                self.ax.text(0.5, 0.5, 'Waiting for price data...', ha='center', va='center', 
                           color='#888888', fontsize=11, transform=self.ax.transAxes)
            
            self.ax.set_facecolor('#0a0a0a')
            self.fig.tight_layout()
            self.canvas.draw()
            
        except:
            pass
        
        self.after(3000, self.update_chart)

    def clear_chart(self):
        """Clear chart data"""
        self.price_history.clear()
        self.time_history.clear()
        self.ai_log("Chart cleared", "SYSTEM")

    def update_status(self):
        """Update all status displays"""
        balance = self.paper_balance if self.is_paper_trading else self.current_balance
        self.status_labels["Balance"].configure(text=f"{balance:,.0f} THB")

        if self.strategy and self.strategy.position:
            pos = self.strategy.position
            symbol = pos['symbol']
            coin_name = symbol.replace("_thb", "").upper()
            
            current_price = 0
            if self.api_client:
                ticker = self.api_client.get_simple_ticker(symbol)
                if ticker:
                    current_price = ticker['last_price']
            
            entry_price = pos['entry_price']
            amount = pos['amount']
            current_value = current_price * amount if current_price > 0 else 0
            
            if current_price > 0 and entry_price > 0:
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
                
                if pnl_pct > 0:
                    pnl_color = "#00ff00"
                    pnl_text = f"+{pnl_pct:.2f}%"
                elif pnl_pct < 0:
                    pnl_color = "#ff0000"
                    pnl_text = f"{pnl_pct:.2f}%"
                else:
                    pnl_color = "#888888"
                    pnl_text = "0.00%"
            else:
                pnl_color = "#888888"
                pnl_text = "0.00%"

            self.pos_labels['symbol'].configure(text=coin_name, text_color="#00ffff")
            self.pos_labels['amount'].configure(text=f"{amount:.6f}", text_color="#ffaa00")
            self.pos_labels['entry'].configure(text=f"{entry_price:,.2f}", text_color="#888888")
            self.pos_labels['current'].configure(text=f"{current_price:,.2f}", text_color="#00ffff")
            self.pos_labels['value'].configure(text=f"{current_value:,.2f} THB", text_color="#00ffff")
            self.pos_labels['pnl'].configure(text=pnl_text, text_color=pnl_color)
            
            self.status_labels["Position"].configure(text=f"{coin_name} ({pnl_text})", text_color=pnl_color)
            
        else:
            self.pos_labels['symbol'].configure(text="None", text_color="#888888")
            self.pos_labels['amount'].configure(text="0.000000", text_color="#888888")
            self.pos_labels['entry'].configure(text="0.00", text_color="#888888")
            self.pos_labels['current'].configure(text="0.00", text_color="#888888")
            self.pos_labels['value'].configure(text="0.00 THB", text_color="#888888")
            self.pos_labels['pnl'].configure(text="0.00%", text_color="#888888")
            self.status_labels["Position"].configure(text="None", text_color="#888888")

        self.status_labels["Trades"].configure(text=str(self.trade_count))
        
        wr = (self.win_count / self.trade_count * 100) if self.trade_count > 0 else 0
        self.status_labels["Win Rate"].configure(text=f"{wr:.0f}%")
        
        pnl_color = "#00ff00" if self.total_pnl >= 0 else "#ff0000"
        self.status_labels["P/L"].configure(text=f"{self.total_pnl:+.0f} THB", text_color=pnl_color)

        self.update_experience_display()

        self.after(1000, self.update_status)

    def manual_save_experience(self):
        """Save experience manually"""
        if not self.strategy:
            self.ai_log("Connect API first", "SYSTEM")
            return

        if self.strategy.save_experience():
            self.ai_log(f"Experience saved", "SYSTEM")
            messagebox.showinfo("Success", "Saved successfully!")
        else:
            messagebox.showerror("Error", "Failed to save")

    def manual_load_experience(self):
        """Load experience manually"""
        if not self.strategy:
            self.ai_log("Connect API first", "SYSTEM")
            return

        self.strategy.load_experience()
        self.update_experience_display()
        messagebox.showinfo("Loaded", "Loaded successfully!")

    def clear_experience(self):
        """Clear all experience"""
        if not self.strategy:
            self.ai_log("Connect API first", "SYSTEM")
            return

        confirm = messagebox.askyesno("Clear All Data?", "Delete ALL experience data?\n\nThis cannot be undone!")

        if confirm:
            self.strategy.coin_data = {}
            self.strategy.total_data_collected = 0

            if os.path.exists(self.strategy.data_save_file):
                os.remove(self.strategy.data_save_file)

            self.ai_log("All data cleared", "SYSTEM")
            self.update_experience_display()
            messagebox.showinfo("Cleared", "All data deleted!")


if __name__ == "__main__":
    print("=" * 80)
    print("🌑 BLVCK TEA AiTrad V3.9 - COMPLETE FULL VERSION")
    print("=" * 80)
    print("✅ COMPLETE: โค้ดครบถ้วน 100% จากต้นฉบับ")
    print("✅ NEW: กราฟแสดงผลการเทรด Real-time")
    print("✅ NEW: ปริมาณเหรียญที่ถือ (Holding Amount)")
    print("✅ NEW: มูลค่าปัจจุบัน (Current Value)")
    print("✅ NEW: % กำไร/ขาดทุน Real-time (+/-) พร้อม Color Coding")
    print("=" * 80)
    print("📦 Requirements:")
    print("   pip install customtkinter numpy requests matplotlib")
    print("=" * 80)
    
    app = EnhancedTradingBot()
    app.mainloop()
