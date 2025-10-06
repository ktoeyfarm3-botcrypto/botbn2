"""
🌑 BLVCK TEA AiTrad V3.7 - FIXED COMPLETE 🌑
แก้ไขปัญหาทั้งหมด + เพิ่ม Learning System ที่สมบูรณ์
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

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class FixedBitkubAPI:
    """Fixed Bitkub API with Correct Symbol Format"""

    def __init__(self, api_key="", api_secret=""):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.bitkub.com"
        self.request_times = deque(maxlen=250)
        self.rate_limit_lock = threading.Lock()

        self.trading_fees = {'maker_fee': 0.0025, 'taker_fee': 0.0025}
        self.error_codes = {
            0: "Success", 1: "Invalid JSON payload", 2: "Missing X-BTK-APIKEY",
            3: "Invalid API key", 4: "API pending for activation", 5: "IP not allowed",
            6: "Missing / invalid signature", 7: "Missing timestamp", 8: "Invalid timestamp",
            9: "Invalid user / User not found", 10: "Invalid parameter", 11: "Invalid symbol",
            12: "Invalid amount / Amount too low", 13: "Invalid rate", 14: "Improper rate",
            15: "Amount too low", 16: "Failed to get balance", 17: "Wallet is empty",
            18: "Insufficient balance"
        }

        self.all_bitkub_symbols = []

        self.symbols_to_check = [
            "THB_BTC", "THB_ETH", "THB_USDT", "THB_USDC", "THB_BNB", "THB_XRP",
            "THB_ADA", "THB_SOL", "THB_DOGE", "THB_DOT", "THB_ATOM",
            "THB_LINK", "THB_AVAX", "THB_NEAR", "THB_ALGO", "THB_HBAR",
            "THB_FLOW", "THB_ICP", "THB_XTZ", "THB_SAND", "THB_MANA",
            "THB_AXS", "THB_GALA", "THB_ENJ", "THB_APE", "THB_CHZ",
            "THB_IMX", "THB_GMX", "THB_ILV", "THB_ARB", "THB_OP",
            "THB_LRC", "THB_SKL", "THB_FET", "THB_GRT", "THB_BAND",
            "THB_TRB", "THB_KUB", "THB_UNI", "THB_SUSHI", "THB_CRV",
            "THB_BCH", "THB_BAT", "THB_ZRX", "THB_KNC", "THB_AAVE",
            "THB_COMP", "THB_SNX", "THB_1INCH", "THB_BAL", "THB_YFI",
            "THB_UMA", "THB_LDO", "THB_FXS", "THB_BLUR", "THB_SCRT",
            "THB_ANKR", "THB_GNO", "THB_C98", "THB_WOO", "THB_TRX",
            "THB_ALPHA", "THB_PERP", "THB_DYDX", "THB_INJ", "THB_KAVA",
            "THB_LUNA", "THB_APT", "THB_SUI", "THB_TIA", "THB_ZK",
            "THB_SFP", "THB_IOTX", "THB_CELR", "THB_ZIL", "THB_JTO",
            "THB_PYTH", "THB_MANTA", "THB_AEVO", "THB_OMNI", "THB_PENDLE",
            "THB_ONDO", "THB_ETHFI", "THB_ENA", "THB_W", "THB_TAIKO",
            "THB_ZRO", "THB_IO", "THB_TON", "THB_CATI", "THB_EIGEN",
            "THB_GRASS", "THB_ME", "THB_VIRTUAL"
        ]

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
        """Test API connection and filter valid symbols"""
        print("\n=== Testing Bitkub API ===")

        try:
            response = requests.get(f"{self.base_url}/api/market/ticker", timeout=10)
            print(f"Response Status: {response.status_code}")

            if response.status_code != 200:
                print(f"HTTP Error: {response.status_code}")
                return False, f"HTTP {response.status_code}"

            data = response.json()
            print(f"API Response OK")
            print(f"Total symbols available: {len(data)}")

            verified_symbols = []
            for symbol in self.symbols_to_check:
                if symbol in data:
                    verified_symbols.append(symbol)

            self.all_bitkub_symbols = verified_symbols

            print(f"Found {len(verified_symbols)} valid symbols")

            return True, f"API OK - {len(verified_symbols)} symbols available"

        except Exception as e:
            print(f"Exception: {e}")
            return False, str(e)

    def get_simple_ticker(self, symbol):
        """Get ticker data for symbol"""
        try:
            self._wait_for_rate_limit()
            response = requests.get(f"{self.base_url}/api/market/ticker", timeout=10)

            if response.status_code != 200:
                return None

            data = response.json()
            ticker_data = data.get(symbol)

            if not ticker_data:
                return None

            return {
                'last_price': float(ticker_data.get('last', 0)),
                'high_24h': float(ticker_data.get('high24hr', 0)),
                'low_24h': float(ticker_data.get('low24hr', 0)),
                'volume_24h': float(ticker_data.get('baseVolume', 0))
            }

        except Exception as e:
            print(f"Error fetching ticker for {symbol}: {e}")
            return None

    def calculate_trading_fees(self, amount, price, order_type):
        """Calculate trading fees"""
        total_value = amount * price
        fee_rate = self.trading_fees['taker_fee']
        return total_value * fee_rate

    def calculate_break_even_price(self, entry_price, order_type):
        """Calculate break-even price"""
        buy_fee_rate = self.trading_fees['taker_fee']
        sell_fee_rate = self.trading_fees['taker_fee']
        total_fee_rate = buy_fee_rate + sell_fee_rate
        break_even = entry_price * (1 + total_fee_rate)
        return break_even

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
            return {"error": 999, "message": str(e)}

    def place_buy_order_safe(self, symbol, amount_thb, buy_price, order_type="limit"):
        """Place real buy order"""
        try:
            self._wait_for_rate_limit()

            order_data = {
                "sym": symbol,
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
            result = response.json()

            print(f"REAL BUY ORDER - Symbol: {symbol}, Amount: {amount_thb}, Price: {buy_price}")
            print(f"API Response: {result}")

            return result

        except Exception as e:
            return {"error": 999, "message": str(e)}

    def place_sell_order_safe(self, symbol, amount_crypto, sell_price, order_type="limit"):
        """Place real sell order"""
        try:
            self._wait_for_rate_limit()

            order_data = {
                "sym": symbol,
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
            result = response.json()

            print(f"REAL SELL ORDER - Symbol: {symbol}, Amount: {amount_crypto}, Price: {sell_price}")
            print(f"API Response: {result}")

            return result

        except Exception as e:
            return {"error": 999, "message": str(e)}


class AdvancedMultiCoinStrategy:
    """Enhanced Multi-Coin Strategy with Complete Learning System"""

    def __init__(self, api_client, log_callback=None):
        self.api_client = api_client
        self.log_callback = log_callback

        self.coin_data = {}
        self.min_data_points = 1000  # 2.7 ชั่วโมง (เริ่มเทรดได้เร็วขึ้น)
        self.optimal_data_points = 10000  # 1.15 วัน (ข้อมูลเพียงพอวิเคราะห์)
        self.max_data_points = 200000  # 23 วัน (~550 ชั่วโมง) - ใช้ RAM ~2.8GB

        self.total_data_collected = 0
        self.data_save_file = "bot_experience.pkl"

        self.position = None

        self.buy_threshold = 45  # ลดลงเพื่อให้ได้สัญญาณบ่อยขึ้น
        self.min_profit_margin = 0.015
        self.take_profit = 0.025
        self.stop_loss = -0.02
        self.trailing_stop = 0.015

        # RELAXED FILTERS
        self.min_volume_24h = 50000  # ลดจาก 100000
        self.max_volatility = 0.30  # เพิ่มจาก 0.20
        self.min_volatility = 0.003  # ลดจาก 0.005

        self.backtest_results = {}

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
                        print(f"Loaded learned threshold: {self.buy_threshold}")

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

                print(f"\nLoaded: {total_points:,} points + {total_trades} trades")
                print(f"   - {ready_coins}/{len(self.coin_data)} coins ready")

                if total_trades > 0:
                    wins = sum(1 for t in self.trade_history if t.get('win', False))
                    win_rate = wins / total_trades * 100
                    print(f"   - Historical Win Rate: {win_rate:.1f}%")

                if self.log_callback:
                    self.log_callback(f"Loaded {total_points:,} points + {total_trades} trades", "SYSTEM")
                    self.log_callback(f"{ready_coins}/{len(self.coin_data)} coins ready", "SYSTEM")
                    if total_trades > 0:
                        self.log_callback(f"Historical WR: {win_rate:.1f}%", "SYSTEM")

                return True
            except Exception as e:
                print(f"Load error: {e}")
                if self.log_callback:
                    self.log_callback(f"Load error: {str(e)[:50]}", "SYSTEM")
                return False
        else:
            if self.log_callback:
                self.log_callback("No saved data - starting fresh", "SYSTEM")
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

            total_points = sum(len(data['prices']) for data in self.coin_data.values())
            total_trades = len(self.trade_history)
            print(f"\nSaved: {total_points} points + {total_trades} trades")
            return True
        except Exception as e:
            print(f"Save error: {e}")
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
        """Collect data for all symbols"""
        collected = 0
        failed = 0

        for i, symbol in enumerate(symbols):
            try:
                self.initialize_coin_data(symbol)
                ticker = self.api_client.get_simple_ticker(symbol)

                if not ticker:
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

                if (i + 1) % 20 == 0:
                    self.ai_log(f"Scanning: {collected} OK, {failed} fail", "AI")

            except Exception as e:
                failed += 1
                continue

        if self.log_callback:
            self.log_callback(f"{collected} coins scanned successfully", "SYSTEM")
            self.log_callback(f"Total Experience: {self.total_data_collected:,} points", "SYSTEM")

        if self.total_data_collected % 100 == 0:
            self.save_experience()

        return collected

    def filter_tradeable_coins(self):
        """Filter coins - RELAXED for testing"""
        try:
            tradeable = []
            filtered_reasons = {
                'no_data': 0,
                'low_volume': 0,
                'high_volatility': 0,
                'low_volatility': 0
            }

            if self.log_callback:
                self.log_callback(f"Starting filter on {len(self.coin_data)} coins...", "SCAN")

            for symbol, data in self.coin_data.items():
                try:
                    if not data.get('data_ready', False):
                        filtered_reasons['no_data'] += 1
                        continue

                    prices = data.get('prices')
                    volumes = data.get('volumes')

                    if not prices or not volumes:
                        filtered_reasons['no_data'] += 1
                        continue

                    # Use lower threshold for filter (just need some data)
                    if len(prices) < 50:  # ต้องมีอย่างน้อย 50 จุด
                        filtered_reasons['no_data'] += 1
                        continue

                    # Use only recent data for speed
                    recent_prices = list(prices)[-50:] if len(prices) > 50 else list(prices)
                    recent_volumes = list(volumes)[-50:] if len(volumes) > 50 else list(volumes)

                    if len(recent_volumes) < 20:
                        filtered_reasons['no_data'] += 1
                        continue

                    avg_volume = np.mean(recent_volumes[-20:])

                    # RELAXED volume
                    if avg_volume < self.min_volume_24h:
                        filtered_reasons['low_volume'] += 1
                        continue

                    if len(recent_prices) >= 21:
                        # Calculate returns correctly
                        price_changes = np.diff(recent_prices[-21:])  # 20 values
                        base_prices = np.array(recent_prices[-21:-1])  # 20 values
                        returns = price_changes / base_prices
                        volatility = np.std(returns)

                        # RELAXED volatility
                        if volatility > self.max_volatility:
                            filtered_reasons['high_volatility'] += 1
                            continue
                        elif volatility < self.min_volatility:
                            filtered_reasons['low_volatility'] += 1
                            continue

                    data['liquidity_ok'] = True
                    data['volatility_ok'] = True
                    tradeable.append(symbol)

                except Exception as e:
                    print(f"Error filtering {symbol}: {e}")
                    filtered_reasons['no_data'] += 1
                    continue

            # Log summary (simplified)
            total_filtered = sum(filtered_reasons.values())
            if self.log_callback:
                self.log_callback(f"Filter: {len(tradeable)}/{len(self.coin_data)} passed", "SCAN")
                if total_filtered > 0:
                    self.log_callback(
                        f"Filtered: Vol={filtered_reasons['low_volume']}, Vola={filtered_reasons['high_volatility'] + filtered_reasons['low_volatility']}, NoData={filtered_reasons['no_data']}",
                        "SCAN")

            return tradeable

        except Exception as e:
            print(f"CRITICAL ERROR in filter_tradeable_coins: {e}")
            import traceback
            traceback.print_exc()
            if self.log_callback:
                self.log_callback(f"ERROR: Filter failed - {str(e)[:50]}", "SCAN")
            return []

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

        # Filter out blacklisted symbols
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

            # Use recent data only for speed
            recent_prices = list(prices)[-50:]
            recent_volumes = list(volumes)[-50:]

            if len(recent_prices) < 21:
                continue

            score = 0

            # Base indicators
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

            if len(recent_prices) >= 21:
                # Calculate returns correctly
                price_changes = np.diff(recent_prices[-21:])  # 20 values
                base_prices = np.array(recent_prices[-21:-1])  # 20 values
                returns = price_changes / base_prices
                volatility = np.std(returns)

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

        if self.log_callback and hasattr(self.log_callback.__self__, 'update_visual_scores'):
            scores_for_visual = [(s[0], s[1]) for s in all_scores[:10]]
            self.log_callback.__self__.update_visual_scores(scores_for_visual)

        # Simplified logging
        if self.log_callback:
            self.log_callback(f"Analyzed: {len(all_scores)} coins", "SCAN")
            self.log_callback(f"Best: {best_coin} Score={best_score}", "SCAN")

            # Log top 5 to SCAN
            for i, (sym, score, rsi, vol) in enumerate(all_scores[:5]):
                coin_name = sym.replace("THB_", "")
                stars = "⭐⭐⭐" if score >= 60 else "⭐⭐" if score >= 50 else "⭐" if score >= 40 else ""
                self.log_callback(f"#{i + 1} {coin_name}: {int(score)} RSI:{int(rsi)} {stars}", "SCAN")

            # Log top 3 to AI column
            for i, (sym, score, rsi, vol) in enumerate(all_scores[:3]):
                coin_name = sym.replace("THB_", "")
                ml_info = ""
                if sym in self.coin_performance and self.coin_performance[sym]['trades'] >= 3:
                    perf = self.coin_performance[sym]
                    wr = perf['wins'] / perf['trades'] * 100
                    ml_info = f" WR:{wr:.0f}%"
                stars = " ⭐⭐⭐" if score >= 60 else " ⭐⭐" if score >= 50 else " ⭐" if score >= 40 else ""
                self.log_callback(f"#{i + 1} {coin_name}: {int(score)} RSI:{int(rsi)}{ml_info}{stars}", "AI")

        if best_score >= self.buy_threshold:
            if self.log_callback:
                self.log_callback(f"READY TO BUY (Threshold: {self.buy_threshold})", "AI")
            return best_coin, best_score, f"Strong signal (Score: {best_score})"
        else:
            if self.log_callback:
                self.log_callback(f"No signal (Best: {best_score}, Need: {self.buy_threshold})", "AI")
            return None, best_score, f"No strong signal (Best: {best_score})"

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
        """FIXED: Learn from completed trade"""
        try:
            is_win = profit_pct > 0

            # Record trade
            trade_record = {
                'symbol': symbol,
                'entry_score': entry_score,
                'profit_pct': profit_pct,
                'win': is_win,
                'timestamp': datetime.now(),
                'hour': datetime.now().hour
            }
            self.trade_history.append(trade_record)

            # Update coin performance
            if symbol not in self.coin_performance:
                self.coin_performance[symbol] = {'wins': 0, 'losses': 0, 'trades': 0, 'total_profit': 0}

            perf = self.coin_performance[symbol]
            perf['trades'] += 1
            perf['total_profit'] += profit_pct
            if is_win:
                perf['wins'] += 1
            else:
                perf['losses'] += 1

            # Update score analysis
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

            # Update time performance
            time_slot = self._get_time_slot(datetime.now().hour)
            if time_slot in self.time_performance:
                time_data = self.time_performance[time_slot]
                if is_win:
                    time_data['wins'] += 1
                else:
                    time_data['losses'] += 1

            # Adjust threshold if enough trades
            if len(self.trade_history) >= self.min_trades_for_learning and len(self.trade_history) % 10 == 0:
                self._adjust_threshold()

            self.ai_log(f"Learned: {symbol} Score={entry_score:.0f} P/L={profit_pct:+.2f}%", "AI")

        except Exception as e:
            print(f"Learning error: {e}")

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
        """Adjust buy threshold based on learning"""
        try:
            total_trades = len(self.trade_history)
            if total_trades < 20:
                return

            recent_trades = self.trade_history[-20:]
            wins = sum(1 for t in recent_trades if t.get('win', False))
            win_rate = wins / len(recent_trades)

            if win_rate > 0.70:
                self.buy_threshold = max(40, self.buy_threshold - 2)
                self.ai_log(f"WR={win_rate * 100:.0f}% -> Lowered threshold to {self.buy_threshold}", "AI")
            elif win_rate < 0.40:
                self.buy_threshold = min(70, self.buy_threshold + 2)
                self.ai_log(f"WR={win_rate * 100:.0f}% -> Raised threshold to {self.buy_threshold}", "AI")

        except Exception as e:
            print(f"Threshold adjustment error: {e}")


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
        """Draw top coin scores beside the core"""
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

            coin_name = symbol.replace("THB_", "")
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


class EnhancedTradingBot(ctk.CTk):
    """Enhanced Multi-Coin Trading Bot - V3.7 Fixed Complete"""

    def __init__(self):
        super().__init__()

        self.title("BLVCK TEA AiTrad V3.7 - FIXED COMPLETE")
        self.geometry("1400x900")

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

        header = ctk.CTkFrame(self, height=60, fg_color="#1a1a1a")
        header.pack(fill="x", padx=10, pady=(10, 5))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="BLVCK TEA AiTrad V3.7 - FIXED COMPLETE",
            font=("Arial", 24, "bold"),
            text_color="#00ffff"
        ).pack(expand=True)

        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True, padx=10, pady=5)

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

        log_split_container = ctk.CTkFrame(left_panel)
        log_split_container.pack(fill="both", expand=True, padx=10, pady=(5, 10))

        sys_log_frame = ctk.CTkFrame(log_split_container)
        sys_log_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        ctk.CTkLabel(
            sys_log_frame,
            text="SYSTEM",
            font=("Arial", 10, "bold"),
            text_color="#00aaff"
        ).pack(pady=(0, 2))

        self.log_display = ctk.CTkTextbox(
            sys_log_frame,
            font=("Courier", 9, "bold"),
            fg_color="#0a0a0a",
            text_color="#ffffff"
        )
        self.log_display.pack(fill="both", expand=True)

        scan_log_frame = ctk.CTkFrame(log_split_container)
        scan_log_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        ctk.CTkLabel(
            scan_log_frame,
            text="SCAN DETAIL",
            font=("Arial", 10, "bold"),
            text_color="#ffaa00"
        ).pack(pady=(0, 2))

        self.scan_detail_display = ctk.CTkTextbox(
            scan_log_frame,
            font=("Courier", 9, "bold"),
            fg_color="#1a1000",
            text_color="#ffaa00",
            border_width=2,
            border_color="#ffaa00"
        )
        self.scan_detail_display.pack(fill="both", expand=True)

        self.scan_detail_display.insert("end", "=== SCAN DETAIL LOG ===\n")
        self.scan_detail_display.insert("end", "Waiting for scan data...\n")

        right_panel_container = ctk.CTkFrame(main_container, width=500)
        right_panel_container.pack(side="right", fill="both", padx=(5, 0))
        right_panel_container.pack_propagate(False)

        self.scrollable_right = ctk.CTkScrollableFrame(right_panel_container)
        self.scrollable_right.pack(fill="both", expand=True)

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

        strategy_frame = ctk.CTkFrame(self.scrollable_right, fg_color="#001a1a", border_width=2, border_color="#00ffff")
        strategy_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(strategy_frame, text="STRATEGY SETTINGS", font=("Arial", 12, "bold"), text_color="#00ffff").pack(
            pady=(5, 5))

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

        exp_frame = ctk.CTkFrame(strategy_frame, fg_color="#001a1a", border_width=1, border_color="#00ffff")
        exp_frame.pack(fill="x", padx=10, pady=3)

        self.exp_label = ctk.CTkLabel(
            exp_frame,
            text="Exp: 0 pts | 0 coins",
            font=("Arial", 9, "bold"),
            text_color="#00ffff"
        )
        self.exp_label.pack(pady=3)

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
        """Unified logging"""

        if log_type == "SCAN":
            timestamp = datetime.now().strftime("%H:%M:%S")
            try:
                if hasattr(self, 'scan_detail_display'):
                    self.scan_detail_display.insert("end", f"[{timestamp}] {message}\n")
                    self.scan_detail_display.see("end")

                    lines = self.scan_detail_display.get("1.0", "end").split("\n")
                    if len(lines) > 100:
                        self.scan_detail_display.delete("1.0", "50.0")
                else:
                    self.log_display.insert("end", f"[{timestamp}] [SCAN] {message}\n")
                    self.log_display.see("end")
            except Exception as e:
                print(f"[SCAN] {message}")
            return

        if log_type != "AI":
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_display.insert("end", f"[{timestamp}] {message}\n")
            self.log_display.see("end")
            return

        column_type = "decision"

        if any(keyword in message for keyword in
               ["Price", "Break-even", "Amount:", "Volume", "collected", "data points", "THB", "Entry:", "Exit:"]):
            column_type = "market"

        elif any(keyword in message for keyword in
                 ["RSI", "Volatility", "Score", "Ratio", "trend", "oversold", "overbought", "WR:", "Avg:", "trades",
                  "⭐", "#"]):
            column_type = "indicators"

        elif any(keyword in message for keyword in
                 ["ANALYZING", "SIGNAL", "Strategy", "HOLDING", "tradeable", "Best", "strong", "Scanning"]):
            column_type = "decision"

        elif any(keyword in message for keyword in
                 ["BUY", "SELL", "PROFIT", "LOSS", "Order", "Position", "EXECUTION", "FAILED", "opened", "closed",
                  "Learned"]):
            column_type = "trade"

        self.visual.add_ai_log(message, column_type)

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

            self.ai_log("=== API CONNECTED ===", "SCAN")
            self.ai_log("Initializing strategy...", "SCAN")

            self.strategy = AdvancedMultiCoinStrategy(self.api_client, log_callback=self.ai_log)

            self.update_experience_display()

            self.ai_log(f"Strategy initialized", "SCAN")
            self.ai_log(f"Ready to scan {len(self.api_client.all_bitkub_symbols)} symbols", "SCAN")
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
                self.ai_log(f"Buy: {buy_threshold}, TP: {take_profit * 100:.1f}%, SL: {stop_loss * 100:.1f}%", "SYSTEM")
            else:
                self.ai_log("Connect API first", "SYSTEM")
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
        """Update experience display"""
        if not self.strategy:
            return

        total_points = sum(len(data['prices']) for data in self.strategy.coin_data.values())
        coins_count = len(self.strategy.coin_data)

        if total_points >= 1000:
            exp_text = f"{total_points / 1000:.1f}k"
        else:
            exp_text = str(total_points)

        self.exp_label.configure(
            text=f"Exp: {exp_text} pts | {coins_count} coins"
        )

    def toggle_paper_trading(self):
        """Toggle paper trading mode"""
        self.is_paper_trading = self.paper_trading_var.get()

        if self.is_paper_trading:
            self.real_trading_var.set(False)
            mode_text = "PAPER TRADING"
            mode_color = "green"

            self.trading_mode_label.configure(
                text=f"{mode_text} MODE ACTIVE (SAFE)",
                text_color=mode_color
            )
            self.start_button.configure(text="START PAPER TRADING", fg_color="#00aa00")
            self.status_labels["Mode"].configure(text="Paper", text_color="#ff8800")

            self.ai_log(f"Switched to {mode_text} mode", "SYSTEM")

    def toggle_real_trading(self):
        """Toggle real trading mode"""
        switch_is_on = self.real_trading_var.get()
        self.is_paper_trading = not switch_is_on

        if switch_is_on:
            warning = messagebox.askyesno(
                "REAL TRADING WARNING",
                "You are about to enable REAL TRADING!\n\n"
                "The system will use REAL MONEY\n"
                "You may lose everything\n"
                "Monitor your account closely\n\n"
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

            mode_text = "REAL TRADING"
            mode_color = "red"

            self.trading_mode_label.configure(
                text=f"{mode_text} MODE ACTIVE (DANGER!)",
                text_color=mode_color
            )
            self.start_button.configure(text="START REAL TRADING", fg_color="#ff0000")
            self.status_labels["Mode"].configure(text="REAL", text_color="#ff0000")

            self.ai_log("REAL TRADING MODE ACTIVATED", "SYSTEM")

        else:
            mode_text = "PAPER TRADING"
            mode_color = "green"

            self.trading_mode_label.configure(
                text=f"{mode_text} MODE ACTIVE (SAFE)",
                text_color=mode_color
            )
            self.start_button.configure(text="START PAPER TRADING", fg_color="#00aa00")
            self.status_labels["Mode"].configure(text="Paper", text_color="#ff8800")

            self.ai_log(f"Switched to {mode_text} mode", "SYSTEM")

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
                    "This bot will place REAL orders\n"
                    "Monitor your account closely\n\n"
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
            self.ai_log("Starting trading immediately", "SYSTEM")
            warmup_count = self.strategy.min_data_points
        else:
            self.ai_log("Collecting fresh market data...", "SYSTEM")
            warmup_count = 0

        required_warmup = self.strategy.min_data_points
        symbols = self.api_client.all_bitkub_symbols

        while self.is_trading:
            try:
                self.ai_log(f"=== LOOP START (warmup: {warmup_count}/{required_warmup}) ===", "SCAN")

                try:
                    amount_text = self.amount_entry.get().strip()
                    if not amount_text:
                        self.trade_amount_thb = 500.0
                    else:
                        self.trade_amount_thb = float(amount_text)
                        if self.trade_amount_thb < 10:
                            self.trade_amount_thb = 500.0
                except (ValueError, AttributeError):
                    self.trade_amount_thb = 500.0

                self.visual.set_trading_state("SCANNING")

                self.ai_log("Starting scan...", "SCAN")
                collected = self.strategy.collect_market_data(symbols)
                self.ai_log(f"Scan complete: {collected} coins", "SCAN")

                ready_coins_now = sum(1 for data in self.strategy.coin_data.values() if data.get('data_ready', False))

                self.ai_log(f"Ready coins: {ready_coins_now}/{len(self.strategy.coin_data)}", "SCAN")

                if warmup_count < required_warmup and ready_coins_now < 10:
                    warmup_count += 1
                    if warmup_count % 10 == 0:
                        self.ai_log(f"Collecting data: {warmup_count}/{required_warmup}", "SYSTEM")
                        self.ai_log(f"{ready_coins_now} coins ready", "AI")
                    self.ai_log(f"Warmup phase: {warmup_count}/{required_warmup}", "SCAN")
                    time.sleep(10)
                    continue

                if warmup_count == required_warmup or (warmup_count < required_warmup and ready_coins_now >= 10):
                    self.ai_log("Data collection complete", "SYSTEM")
                    self.ai_log(f"AI Trading Mode: ACTIVE ({ready_coins_now} coins)", "SYSTEM")
                    warmup_count = required_warmup + 1

                current_balance = self.paper_balance if self.is_paper_trading else self.current_balance

                if self.strategy.position is None:
                    self.visual.set_trading_state("ANALYZING")

                    self.ai_log("=== FILTERING COINS ===", "SCAN")
                    tradeable = self.strategy.filter_tradeable_coins()

                    self.ai_log(f"Filter result: {len(tradeable)} tradeable coins", "SYSTEM")
                    self.ai_log(f"=== FILTER DONE: {len(tradeable)} coins ===", "SCAN")

                    if not tradeable:
                        self.ai_log("No tradeable coins found", "AI")
                        self.ai_log("Waiting for better market conditions...", "AI")
                        self.ai_log("=== NO TRADEABLE COINS ===", "SCAN")
                        time.sleep(10)
                        continue

                    self.ai_log(f"=== ANALYZING {len(tradeable)} COINS ===", "SCAN")
                    best_coin, score, reason = self.strategy.find_best_coin_to_buy(tradeable)

                    if best_coin:
                        self.ai_log(f"=== SIGNAL CONFIRMED ===", "SCAN")
                        self.ai_log(f"Selected: {best_coin} (Score: {score})", "SCAN")
                        ticker = self.api_client.get_simple_ticker(best_coin)
                        if ticker:
                            self.execute_buy(best_coin, ticker, reason, score)
                        else:
                            self.ai_log(f"Failed to get ticker for {best_coin}", "AI")
                    else:
                        self.ai_log(reason, "AI")
                        self.ai_log(f"Best score: {score}, Need: {self.strategy.buy_threshold}", "AI")

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
                            entry_price = self.strategy.position['entry_price']
                            current_price = ticker['last_price']
                            profit_pct = ((current_price - entry_price) / entry_price) * 100

                            self.ai_log(f"Holding: {profit_pct:+.2f}%", "AI")
                            self.visual.set_trading_state("HOLDING")

                time.sleep(10)

            except ValueError as e:
                time.sleep(5)
            except Exception as e:
                self.ai_log(f"Error: {str(e)[:30]}", "AI")
                print(f"Exception in trading_loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(10)

        self.ai_log("Trading stopped", "SYSTEM")
        self.visual.set_trading_state("IDLE")

    def execute_buy(self, symbol, ticker, reason, score=0):
        """Execute buy"""
        try:
            if self.strategy.position is not None:
                return

            price = ticker['last_price']

            if price <= 0:
                self.ai_log(f"SKIP: {symbol} - Invalid price", "AI")
                return

            amount_thb = self.trade_amount_thb

            min_amount = 10
            max_amount = 10000 if self.is_paper_trading else 5000

            if amount_thb < min_amount:
                self.ai_log(f"Amount < {min_amount} THB", "AI")
                return

            if amount_thb > max_amount:
                self.ai_log(f"Limited to {max_amount} THB", "AI")
                amount_thb = max_amount

            current_balance = self.paper_balance if self.is_paper_trading else self.current_balance
            if amount_thb > current_balance:
                self.ai_log(f"Insufficient: {current_balance:.0f} THB", "AI")
                return

            self.visual.set_trading_state("BUYING")

            amount_crypto = amount_thb / price
            buy_fee = self.api_client.calculate_trading_fees(amount_crypto, price, "buy")
            break_even = self.api_client.calculate_break_even_price(price, "buy")

            self.ai_log(f"Price: {price:,.0f} THB", "AI")
            self.ai_log(f"Amount: {amount_thb:.0f} THB", "AI")
            self.ai_log(f"Break-even: {break_even:,.0f}", "AI")

            self.ai_log(f"BUY SIGNAL: {symbol.upper()}", "AI")
            self.ai_log(f"Reason: {reason[:30]}", "AI")

            self.strategy.position = {
                'symbol': symbol,
                'entry_price': price,
                'amount': amount_crypto,
                'entry_time': datetime.now(),
                'break_even_price': break_even,
                'buy_fee': buy_fee,
                'pending': True,
                'entry_score': score
            }

            if self.is_paper_trading:
                self.ai_log(f"PAPER MODE - Simulated", "AI")
                self.paper_balance -= amount_thb
                self.strategy.position['pending'] = False
            else:
                self.ai_log(f"REAL MODE - Sending order...", "AI")

                buy_price = price * 1.002

                result = self.api_client.place_buy_order_safe(symbol, amount_thb, buy_price, 'limit')

                if result.get('error') != 0:
                    error_code = result.get('error')
                    error_msg = self.api_client.error_codes.get(error_code, 'Unknown error')

                    self.ai_log(f"BUY FAILED: {error_msg}", "AI")
                    self.ai_log(f"Error code: {error_code}", "AI")

                    # Add to blacklist if invalid symbol
                    if error_code == 11:  # Invalid symbol
                        if not hasattr(self.strategy, 'blacklisted_symbols'):
                            self.strategy.blacklisted_symbols = set()
                        self.strategy.blacklisted_symbols.add(symbol)
                        self.ai_log(f"Blacklisted: {symbol}", "AI")

                    print(f"\nReal Mode Order Failed:")
                    print(f"   Symbol: {symbol}")
                    print(f"   Amount: {amount_thb} THB")
                    print(f"   Price: {buy_price}")
                    print(f"   Error: {error_code} - {error_msg}")
                    print(f"   Full response: {result}")

                    self.strategy.position = None
                    return
                else:
                    order_id = result.get('result', {}).get('id', 'N/A')
                    self.ai_log(f"Order ID: {order_id}", "AI")
                    self.strategy.position['pending'] = False
                    self.strategy.position['order_id'] = order_id
                    self.current_balance -= amount_thb

            self.trade_count += 1
            self.ai_log("Position opened!", "AI")
            self.visual.set_trading_state("HOLDING")

        except Exception as e:
            self.ai_log(f"BUY ERROR: {str(e)[:30]}", "AI")
            print(f"Exception in execute_buy: {e}")
            import traceback
            traceback.print_exc()
            self.strategy.position = None

    def execute_sell(self, symbol, ticker, reason):
        """Execute sell"""
        try:
            price = ticker['last_price']

            if price <= 0:
                self.ai_log(f"SKIP SELL: Invalid price", "AI")
                return

            position = self.strategy.position
            amount = position['amount']
            entry_score = position.get('entry_score', 0)

            self.visual.set_trading_state("SELLING")

            entry_price = position['entry_price']
            buy_fee = position['buy_fee']
            sell_fee = self.api_client.calculate_trading_fees(amount, price, "sell")

            gross_pnl = (price - entry_price) * amount
            net_pnl = gross_pnl - buy_fee - sell_fee
            profit_pct = net_pnl / (entry_price * amount) * 100

            self.ai_log(f"Entry: {entry_price:,.0f}", "AI")
            self.ai_log(f"Exit: {price:,.0f}", "AI")

            self.ai_log(f"SELL: {reason[:20]}", "AI")
            self.ai_log(f"Net P/L: {net_pnl:+.2f} THB ({profit_pct:+.2f}%)", "AI")

            if self.is_paper_trading:
                self.ai_log(f"PAPER MODE", "AI")
                proceeds = amount * price
                self.paper_balance += proceeds

            else:
                self.ai_log(f"REAL SELL", "AI")

                sell_price = price * 0.998

                result = self.api_client.place_sell_order_safe(
                    symbol,
                    amount,
                    sell_price,
                    'limit'
                )

                if result.get('error') != 0:
                    error_code = result.get('error', 999)
                    error_msg = self.api_client.error_codes.get(error_code, f"Error {error_code}")

                    self.ai_log(f"SELL FAILED: {error_msg}", "AI")

                    print(f"\nReal Sell Order Failed:")
                    print(f"   Symbol: {symbol}")
                    print(f"   Amount: {amount:.8f}")
                    print(f"   Price: {sell_price:,.2f}")
                    print(f"   Error: {error_code} - {error_msg}")
                    print(f"   Response: {result}")

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

        except Exception as e:
            self.ai_log(f"SELL ERROR: {str(e)[:30]}", "AI")
            print(f"Exception in execute_sell: {e}")
            import traceback
            traceback.print_exc()

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

        self.update_experience_display()

        self.after(1000, self.update_status)

    def manual_save_experience(self):
        """Save experience manually"""
        if not self.strategy:
            self.ai_log("Connect API first", "SYSTEM")
            return

        if self.strategy.save_experience():
            total_points = sum(len(data['prices']) for data in self.strategy.coin_data.values())

            self.ai_log(f"Saved: {total_points:,} exp points", "SYSTEM")
            messagebox.showinfo(
                "Success",
                f"Saved successfully!\n\n"
                f"Total Points: {total_points:,}\n"
                f"Coins: {len(self.strategy.coin_data)}"
            )
        else:
            self.ai_log("Save failed", "SYSTEM")
            messagebox.showerror("Error", "Failed to save experience data")

    def manual_load_experience(self):
        """Load experience manually"""
        if not self.strategy:
            self.ai_log("Connect API first", "SYSTEM")
            return

        self.strategy.load_experience()
        self.update_experience_display()

        total_points = sum(len(data['prices']) for data in self.strategy.coin_data.values())

        messagebox.showinfo(
            "Loaded",
            f"Loaded successfully!\n\n"
            f"Total Points: {total_points:,}\n"
            f"Coins: {len(self.strategy.coin_data)}"
        )

    def clear_experience(self):
        """Clear all experience"""
        if not self.strategy:
            self.ai_log("Connect API first", "SYSTEM")
            return

        total_points = sum(len(data['prices']) for data in self.strategy.coin_data.values())
        coins_count = len(self.strategy.coin_data)

        confirm = messagebox.askyesno(
            "Clear All Data?",
            f"Delete ALL experience data?\n\n"
            f"Total Points: {total_points:,}\n"
            f"Coins: {coins_count}\n\n"
            f"This cannot be undone!\n\n"
            f"Are you sure?"
        )

        if confirm:
            self.strategy.coin_data = {}
            self.strategy.total_data_collected = 0

            if os.path.exists(self.strategy.data_save_file):
                os.remove(self.strategy.data_save_file)

            self.ai_log("All data cleared", "SYSTEM")
            self.update_experience_display()
            messagebox.showinfo("Cleared", "All experience data deleted!")


if __name__ == "__main__":
    print("=" * 60)
    print("BLVCK TEA AiTrad V3.7 - FIXED COMPLETE")
    print("=" * 60)
    print("FIXED: learn_from_trade() method added")
    print("FIXED: Relaxed filters for more trading signals")
    print("FIXED: Lower buy threshold (45 instead of 50)")
    print("ENHANCED: Complete ML learning system")
    print("=" * 60)

    app = EnhancedTradingBot()
    app.mainloop()
